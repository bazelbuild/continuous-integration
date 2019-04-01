package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

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

func main() {
	flag.Parse()

	settings, err := ReadSettingsFromDatastore(*projectID, *datastoreSettingsName)
	if err != nil {
		log.Fatalf("Could not read settings from Datastore: %v", err)
	}
	if len(settings.BuildkitePipelines) == 0 {
		log.Fatalf("No pipelines were specified.")
	}

	bk, err := clients.CreateBuildkiteClient(settings.BuildkiteOrg, settings.BuildkiteApiToken, settings.BuildkiteDebug)
	if err != nil {
		log.Fatalf("Cannot create Buildkite client: %v", err)
	}

	cloudSql, err := publishers.CreateCloudSqlPublisher(settings.CloudSqlUser, settings.CloudSqlPassword, settings.CloudSqlInstance, settings.CloudSqlDatabase, settings.CloudSqlLocalPort)
	if err != nil {
		log.Fatalf("Failed to set up Cloud SQL publisher: %v", err)
	}

	srv := service.CreateService(handleError)

	pipelinePerformance := metrics.CreatePipelinePerformance(bk, settings.BuildkitePipelines...)
	srv.AddMetric(pipelinePerformance, 60, cloudSql)

	releaseDownloads := metrics.CreateReleaseDownloads(settings.GitHubOrg,
		settings.GitHubRepo,
		settings.GitHubApiToken, megaByte)
	srv.AddMetric(releaseDownloads, 12*60, cloudSql)

	workerAvailability := metrics.CreateWorkerAvailability(bk)
	srv.AddMetric(workerAvailability, 60, cloudSql)

	if *testMode {
		log.Println("[Test mode] Running all jobs exactly once...")
		srv.RunJobsOnce()
	} else {
		srv.Start()

		exitSignal := make(chan os.Signal)
		signal.Notify(exitSignal, syscall.SIGINT, syscall.SIGTERM)
		<-exitSignal

		srv.Stop()
	}
}
