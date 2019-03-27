package collectors

import (
	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type PresubmitPerformance struct {
	bk        *clients.BuildkiteClient
	pipelines []string
}

func (pp PresubmitPerformance) Collect() (*data.DataSet, error) {
	data := data.CreateDataSet("test")
	data.AddRow(1)
	data.AddRow(3)
	return data, nil
}

func CreatePresubmitPerformanceCollector(bk *clients.BuildkiteClient, pipelines ...string) PresubmitPerformance {
	return PresubmitPerformance{bk: bk, pipelines: pipelines}
}

// performance: pipeline    platform    task    wait_time   run_time    job
