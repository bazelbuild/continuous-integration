package collectors

import (
	"github.com/fweikert/continuous-integration/metrics/clients"
)

type PresubmitPerformance struct {
	bk        *clients.BuildkiteClient
	pipelines []string
}

func (pp PresubmitPerformance) Collect() (map[string]interface{}, error) {
	data := make(map[string]interface{})
	data["test"] = 2
	return data, nil
}

func CreatePresubmitPerformanceCollector(bk *clients.BuildkiteClient, pipelines []string) PresubmitPerformance {
	return PresubmitPerformance{bk: bk, pipelines: pipelines}
}

// performance: pipeline    platform    task    wait_time   run_time    job
