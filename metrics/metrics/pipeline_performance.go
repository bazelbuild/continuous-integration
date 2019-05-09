package metrics

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/go-buildkite/buildkite"
)

const skipTasksEnvVar = "CI_SKIP_TASKS"

type PipelinePerformance struct {
	client         *clients.BuildkiteClient
	pipelines      []string
	columns        []Column
	lastNBuilds    int
	platformFilter string
}

func (pp *PipelinePerformance) Name() string {
	return "pipeline_performance"
}

func (pp *PipelinePerformance) Columns() []Column {
	return pp.columns
}

func (pp *PipelinePerformance) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(pp.columns))
	for _, pipeline := range pp.pipelines {
		builds, err := pp.client.GetMostRecentBuilds(pipeline, pp.lastNBuilds)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect performance statistics for pipeline %s: %v", pipeline, err)
		}
		for _, build := range builds {
			skippedTasks := getSkippedTasks(build)
			for _, job := range build.Jobs {
				if pp.platformFilter != "" && getPlatfrom(job) != pp.platformFilter {
					continue
				}
				err := result.AddRow(pipeline, *build.Number, *job.Name, job.CreatedAt, getDifferenceSeconds(job.CreatedAt, job.StartedAt), getDifferenceSeconds(job.StartedAt, job.FinishedAt), skippedTasks)
				if err != nil {
					return nil, fmt.Errorf("Failed to add result for job %s of build %d: %v", *job.Name, *build.Number, err)
				}
			}
		}
	}
	return result, nil
}

func getSkippedTasks(build buildkite.Build) string {
	if data, ok := build.Env[skipTasksEnvVar]; ok {
		if skippedTasks, ok := data.(string); ok {
			return skippedTasks
		}
	}
	return ""
}

// CREATE TABLE pipeline_performance (pipeline VARCHAR(255), build INT, job VARCHAR(255), creation_time DATETIME, wait_time_seconds FLOAT, run_time_seconds FLOAT, skipped_tasks VARCHAR(255), PRIMARY KEY(pipeline, build, job));
func CreatePipelinePerformance(client *clients.BuildkiteClient, lastNBuilds int, platformFilter string, pipelines ...string) *PipelinePerformance {
	columns := []Column{Column{"pipeline", true}, Column{"build", true}, Column{"job", true}, Column{"creation_time", false}, Column{"wait_time_seconds", false}, Column{"run_time_seconds", false}, Column{"skipped_tasks", false}}
	return &PipelinePerformance{client: client, pipelines: pipelines, columns: columns, lastNBuilds: lastNBuilds, platformFilter: platformFilter}
}
