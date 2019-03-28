package main

import (
	"flag"
	"fmt"
	"log"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/collectors"
	"github.com/fweikert/continuous-integration/metrics/publishers"
	"github.com/fweikert/continuous-integration/metrics/service"
)

var (
	bkOrg          = flag.String("buildkite_org", "bazel", "Buildkite organization slug")
	bkApiToken     = flag.String("buildkite_token", "", "Buildkite API access token that grants read access. See https://buildkite.com/docs/apis/rest-api#authentication")
	bkDebug        = flag.Bool("debug", false, "Enable debugging")
	pipelineString = flag.String("pipelines", "", "Comma separated list of slugs of pipelines whose performance statistics should be exported.")
	ghOrg          = flag.String("github_org", "bazelbuild", "Name of the GitHub organization.")
	ghRepo         = flag.String("github_repo", "bazelbuild", "Name of the GitHub repository.")
	ghApiToken     = flag.String("github_token", "", "Access token for the GitHub API.")
	sqlUser        = flag.String("sql_user", "", "User name for the CloudSQL publisher.")
	sqlPassword    = flag.String("sql_password", "", "Password for the CloudSQL publisher.")
	sqlInstance    = flag.String("sql_instance", "", "Instance name for the CloudSQL publisher.")
)

const megaByte = 1024 * 1024

func handleError(metricName string, err error) {
	fmt.Printf("[%s] %v", metricName, err)
}

func main() {
	flag.Parse()

	if strings.TrimSpace(*pipelineString) == "" {
		log.Fatalf("No pipelines were specified.")
	}
	pipelines := strings.Split(*pipelineString, ",")

	bk, err := clients.CreateBuildkiteClient(*bkOrg, *bkApiToken, *bkDebug)
	if err != nil {
		log.Fatalf("Cannot create Buildkite client: %v", err)
	}

	cloudSql := publishers.CreateCloudSqlPublisher()
	pipelinePerformance := collectors.CreatePipelinePerformanceCollector(bk, pipelines...)
	workerAvailability := collectors.CreateWorkerAvailabilityCollector(bk)
	releaseDownloads := collectors.CreateReleaseDownloadsCollector(*ghOrg, *ghRepo, *ghApiToken, megaByte)

	srv := service.CreateService(handleError)
	srv.AddMetric("pipeline_performance", 120, pipelinePerformance, cloudSql)
	srv.AddMetric("worker_availability", 60, workerAvailability, cloudSql)
	srv.AddMetric("release_downloads", 3600, releaseDownloads, cloudSql)

	ds, err := releaseDownloads.Collect()
	fmt.Println(ds)
	fmt.Println(err)

	//srv.Start()
	//time.Sleep(30 * time.Second)
	//srv.Stop()
}
