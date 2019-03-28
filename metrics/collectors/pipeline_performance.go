package collectors

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/go-buildkite/buildkite"
)

type PipelinePerformance struct {
	client    *clients.BuildkiteClient
	pipelines []string
}

func (pp PipelinePerformance) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet("pipeline", "build", "job", "wait_time_seconds", "run_time_seconds")
	for _, pipeline := range pp.pipelines {
		builds, err := pp.client.GetMostRecentBuilds(pipeline, 30)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect performance statistics for pipeline %s: %v", pipeline, err)
		}
		for _, build := range builds {
			for _, job := range build.Jobs {
				err := result.AddRow(pipeline, *build.Number, *job.Name, getDifferenceSeconds(job.CreatedAt, job.StartedAt), getDifferenceSeconds(job.StartedAt, job.FinishedAt))
				if err != nil {
					return nil, fmt.Errorf("Failed to add result for job %s of build %d: %v", *job.Name, *build.Number, err)
				}
			}
		}
	}
	return result, nil
}

func getDifferenceSeconds(start *buildkite.Timestamp, end *buildkite.Timestamp) float64 {
	if start == nil || end == nil {
		return -1
	}
	return end.Time.Sub(start.Time).Seconds()
}

func CreatePipelinePerformanceCollector(client *clients.BuildkiteClient, pipelines ...string) PipelinePerformance {
	return PipelinePerformance{client: client, pipelines: pipelines}
}
