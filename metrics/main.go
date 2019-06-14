package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/metrics"
	"github.com/fweikert/continuous-integration/metrics/publishers"
	"github.com/fweikert/continuous-integration/metrics/service"
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

	/*
		bk, err := clients.CreateBuildkiteClient(settings.BuildkiteApiToken, settings.BuildkiteDebug)
		if err != nil {
			log.Fatalf("Cannot create Buildkite client: %v", err)
		}
	*/

	gcs, err := clients.CreateGcsClient()
	if err != nil {
		log.Fatalf("Cannot create GCS client: %v", err)
	}

	/*
		stackdriverClient, err := clients.CreateStackdriverClient()
		if err != nil {
			log.Fatalf("Cannot create Stackdriver client: %v", err)
		}

		cloudSql, err := publishers.CreateCloudSqlPublisher(settings.CloudSqlUser, settings.CloudSqlPassword, settings.CloudSqlInstance, settings.CloudSqlDatabase, settings.CloudSqlLocalPort)
		if err != nil {
			log.Fatalf("Failed to set up Cloud SQL publisher: %v", err)
		}

		stackdriver := publishers.CreateStackdriverPublisher(stackdriverClient, *projectID)
	*/

	stdout := publishers.CreateStdoutPublisher(publishers.Csv)

	srv := service.CreateService(handleError)

	/*
		// TODO: support multiple organizations
		platformLoad := metrics.CreatePlatformLoad(bk, 100, settings.BuildkiteOrgs...)
		srv.AddMetric(platformLoad, 60, stackdriver)

		buildsPerChange := metrics.CreateBuildsPerChange(bk, 500, pipelines...)
		srv.AddMetric(buildsPerChange, 60, stdout)

		buildSuccess := metrics.CreateBuildSuccess(bk, 200, pipelines...)
		srv.AddMetric(buildSuccess, 60, stdout)
	*/

	flakiness := metrics.CreateFlakiness(gcs, "bazel-buildkite-stats", "flaky-tests-bep", pipelines...)
	srv.AddMetric(flakiness, 60, stdout)

	/*
		pid := &data.PipelineID{Org: "bazel", Slug: "google-bazel-presubmit"}

		macPerformance := metrics.CreateMacPerformance(bk, 20, pid) // TODO: pipelines...)
		srv.AddMetric(macPerformance, 60, stdout)

		pipelinePerformance := metrics.CreatePipelinePerformance(bk, 20, pipelines...)
		srv.AddMetric(pipelinePerformance, 60, stdout)

		platformSignificance := metrics.CreatePlatformSignificance(bk, 100, pipelines...)
		srv.AddMetric(platformSignificance, 24*60, stdout)

		platformUsage := metrics.CreatePlatformUsage(bk, 100, settings.BuildkiteOrgs...)
		srv.AddMetric(platformUsage, 60, stdout)

		releaseDownloads := metrics.CreateReleaseDownloads(settings.GitHubOrg,
			settings.GitHubRepo,
			settings.GitHubApiToken, megaByte)
		srv.AddMetric(releaseDownloads, 12*60, stdout)

		workerAvailability := metrics.CreateWorkerAvailability(bk, settings.BuildkiteOrgs...)
		srv.AddMetric(workerAvailability, 60, stdout)
	*/

	if *testMode {
		log.Println("[Test mode] Running all jobs exactly once...")
		srv.RunJobsOnce()
		os.Exit(0)
	}

	srv.Start()
	http.HandleFunc("/", handleRequest)
	log.Fatal(http.ListenAndServe(":8080", nil))
}
