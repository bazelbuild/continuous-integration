package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/metrics"
	"github.com/bazelbuild/continuous-integration/metrics/publishers"
	"github.com/bazelbuild/continuous-integration/metrics/service"
)

var (
	projectID             = flag.String("project_id", "bazel-untrusted", "ID of the GCP project.")
	datastoreSettingsName = flag.String("datastore_settings_name", "MetricSettings", "Name of the settings entity in Datastore.")
	testMode              = flag.Bool("test", false, "If true, the service will collect and publish all metrics immediately and only once.")
)

const megaByte = 1024 * 1024

func handleError(metricName string, err error) {
	fmt.Printf("[%s] %v\n", metricName, err)
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "You should try https://bazel.build")
}

func minutes(value int) time.Duration {
	return time.Duration(value) * time.Minute
}

func logInTestMode(message string) {
	log.Printf("[Test mode] %s\n", message)
}

func main() {
	flag.Parse()

	settings, err := ReadSettingsFromDatastore(*projectID, *datastoreSettingsName)
	if err != nil {
		log.Fatalf("Could not read settings from Datastore: %v", err)
	}
	pipelines, err := settings.GetPipelineIDs()
	if err != nil {
		log.Fatalf("Could not get Buildkite pipeline IDs from Datastore: %v", err)
	}
	if len(pipelines) == 0 {
		log.Fatalf("No pipelines were specified.")
	}

	bkAPI, err := clients.CreateBuildkiteAPI(settings.BuildkiteApiToken, settings.BuildkiteDebug)
	if err != nil {
		log.Fatalf("Cannot create Buildkite API client: %v", err)
	}
	bk := clients.CreateCachedBuildkiteClient(bkAPI, time.Duration(settings.BuildkiteCacheTimeoutMinutes)*time.Minute)

	computeClient, err := clients.CreateComputeEngineClient()
	if err != nil {
		log.Fatalf("Cannot create Compute Engine client: %v", err)
	}

	storageClient, err := clients.CreateCloudStorageClient()
	if err != nil {
		log.Fatalf("Cannot create Cloud Storage client: %v", err)
	}

	stackdriverClient, err := clients.CreateStackdriverClient()
	if err != nil {
		log.Fatalf("Cannot create Stackdriver client: %v", err)
	}

	stackdriver := publishers.CreateStackdriverPublisher(stackdriverClient, *projectID)

	stdout := publishers.CreateStdoutPublisher(publishers.Csv)

	var defaultPublisher publishers.Publisher
	if *testMode {
		logInTestMode("Using stdout publisher for all metrics.")
		defaultPublisher = stdout
	} else {
		defaultPublisher, err = publishers.CreateCloudSqlPublisher(settings.CloudSqlUser, settings.CloudSqlPassword, settings.CloudSqlInstance, settings.CloudSqlDatabase, settings.CloudSqlLocalPort)
		if err != nil {
			log.Fatalf("Failed to set up Cloud SQL publisher: %v", err)
		}
	}

	srv := service.CreateService(handleError)

	aggPipelinePerformance := metrics.CreateAggregatedPipelinePerformance(bk, 20, pipelines...)
	srv.AddMetric(aggPipelinePerformance, minutes(10), defaultPublisher)

	buildsPerChange := metrics.CreateBuildsPerChange(bk, 500, pipelines...)
	srv.AddMetric(buildsPerChange, minutes(60), defaultPublisher)

	buildSuccess := metrics.CreateBuildSuccess(bk, 200, pipelines...)
	srv.AddMetric(buildSuccess, minutes(60), defaultPublisher)

	ctx := context.Background()
	cloudBuildStatus, err := metrics.CreateCloudBuildStatus(ctx, settings.CloudBuildProject, settings.CloudBuildSubscription)
	if err != nil {
		log.Fatalf("Failed to set up CloudBuildStatus metric: %v", err)
	}
	srv.AddMetric(cloudBuildStatus, minutes(5), defaultPublisher, stackdriver)

	criticalPath := metrics.CreateCriticalPath(bk, 20, pipelines...)
	srv.AddMetric(criticalPath, minutes(60), defaultPublisher)

	flakiness := metrics.CreateFlakiness(storageClient, "bazel-buildkite-stats", "flaky-tests-bep", pipelines...)
	srv.AddMetric(flakiness, minutes(60), defaultPublisher)

	macPerformance := metrics.CreateMacPerformance(bk, 20, pipelines...)
	srv.AddMetric(macPerformance, minutes(60), defaultPublisher)

	pipelinePerformance := metrics.CreatePipelinePerformance(bk, 20, pipelines...)
	srv.AddMetric(pipelinePerformance, minutes(10), defaultPublisher)

	platformLoad := metrics.CreatePlatformLoad(bk, 100, settings.BuildkiteOrgs...)
	srv.AddMetric(platformLoad, minutes(1), defaultPublisher, stackdriver)

	platformSignificance := metrics.CreatePlatformSignificance(bk, 100, pipelines...)
	srv.AddMetric(platformSignificance, minutes(24*60), defaultPublisher)

	platformUsage := metrics.CreatePlatformUsage(bk, 100, settings.BuildkiteOrgs...)
	srv.AddMetric(platformUsage, minutes(60), defaultPublisher)

	releaseDownloads := metrics.CreateReleaseDownloads(settings.GitHubOrg,
		settings.GitHubRepo,
		settings.GitHubApiToken, megaByte)
	srv.AddMetric(releaseDownloads, minutes(12*60), defaultPublisher)

	workerAvailability := metrics.CreateWorkerAvailability(bk, settings.BuildkiteOrgs...)
	srv.AddMetric(workerAvailability, minutes(5), defaultPublisher)

	// TODO(fweikert): Read gracePeriod from Datastore
	zombieInstances := metrics.CreateZombieInstances(computeClient, settings.CloudProjects, bk, settings.BuildkiteOrgs, minutes(3))
	srv.AddMetric(zombieInstances, minutes(5), defaultPublisher)

	if *testMode {
		logInTestMode("Running all jobs exactly once...")
		srv.RunJobsOnce()
		os.Exit(0)
	}

	srv.Start()
	http.HandleFunc("/", handleRequest)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", port), nil))
}
