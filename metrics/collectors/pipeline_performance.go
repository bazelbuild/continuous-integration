package collectors

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type PipelinePerformance struct {
	client    *clients.BuildkiteClient
	pipelines []string
}

func (pp PipelinePerformance) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet("pipeline", "build", "platform", "task", "wait_time_seconds", "run_time_seconds", "job_name")
	for _, pipeline := range pp.pipelines {
		jobs, err := pp.client.GetMostRecentJobs(pipeline, 30)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect performance statistics for pipeline %s: %v", pipeline, err)
		}
		for _, job := range jobs {
			err := result.AddRow(pipeline, 42, "platform", "task", 1, 2, job)
			if err != nil {
				return nil, err
			}
		}
	}
	return result, nil
}

func CreatePipelinePerformanceCollector(client *clients.BuildkiteClient, pipelines ...string) PipelinePerformance {
	return PipelinePerformance{client: client, pipelines: pipelines}
}
