package main

import (
	"flag"
	"fmt"
	"log"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/metrics"

	"github.com/fweikert/continuous-integration/metrics/clients"
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
	sqlDatabase    = flag.String("sql_database", "metrics", "Name of the SQL database.")
	sqlLocalPort   = flag.Int("sql_local_port", 3306, "Port of the SQL database when testing locally. Requires the Cloud SQL proxy to be installed and running.")
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

	cloudSql, err := publishers.CreateCloudSqlPublisher(*sqlUser, *sqlPassword, *sqlInstance, *sqlDatabase, *sqlLocalPort)
	pipelinePerformance := metrics.CreatePipelinePerformance(bk, pipelines...)
	workerAvailability := metrics.CreateWorkerAvailability(bk)
	releaseDownloads := metrics.CreateReleaseDownloads(*ghOrg, *ghRepo, *ghApiToken, megaByte)

	srv := service.CreateService(handleError)
	srv.AddMetric(pipelinePerformance, 120, cloudSql)
	srv.AddMetric(workerAvailability, 60, cloudSql)
	srv.AddMetric(releaseDownloads, 3600, cloudSql)

	ds, err := releaseDownloads.Collect()
	fmt.Println(ds)
	fmt.Println(err)

	//srv.Start()
	//time.Sleep(30 * time.Second)
	//srv.Stop()
}
