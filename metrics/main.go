package main

import (
	"flag"
	"fmt"
	"log"
	"time"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/collectors"
	"github.com/fweikert/continuous-integration/metrics/publishers"
	"github.com/fweikert/continuous-integration/metrics/service"
)

var (
	org         = flag.String("buildkite_org", "bazel", "Buildkite orginization slug")
	apiToken    = flag.String("buildkite_token", "", "Buildkite API access token that grants read access. See https://buildkite.com/docs/apis/rest-api#authentication")
	debug       = flag.Bool("debug", false, "Enable debugging")
	pipelines   = flag.String("pipelines", "", "Comma separated list of slugs of pipelines whose performance statistics should be exported.")
	sqlUser     = flag.String("sql_user", "", "User name for the CloudSQL publisher.")
	sqlPassword = flag.String("sql_password", "", "Password for the CloudSQL publisher.")
	sqlInstance = flag.String("sql_instance", "", "Instance name for the CloudSQL publisher.")
)

func handleError(metricName string, err error) {
	fmt.Printf("[%s] %v", metricName, err)
}

func main() {
	flag.Parse()

	bk, err := clients.CreateBuildkiteClient(*org, *apiToken, *debug)
	if err != nil {
		log.Fatalf("Cannot create Buildkite client: %v", err)
	}

	cloudSql := publishers.CreateCloudSqlPublisher()
	presubmitPerformance := collectors.CreatePresubmitPerformanceCollector(bk)

	srv := service.CreateService(handleError)
	srv.AddMetric("presubmit_performance", 10, presubmitPerformance, cloudSql)

	srv.Start()
	time.Sleep(30 * time.Second)
	srv.Stop()
}
