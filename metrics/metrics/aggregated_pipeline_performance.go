package metrics

import (
	"fmt"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

type AggregatedPipelinePerformance struct {
	client      clients.BuildkiteClient
	pipelines   []*data.PipelineID
	columns     []Column
	lastNBuilds int
}

func (app *AggregatedPipelinePerformance) Name() string {
	return "aggregated_pipeline_performance"
}

func (app *AggregatedPipelinePerformance) Columns() []Column {
	return app.columns
}

func (*AggregatedPipelinePerformance) Type() MetricType {
	return BuildBasedMetric
}

func (*AggregatedPipelinePerformance) RelevantDelta() int {
	return 100 // builds
}

func (app *AggregatedPipelinePerformance) Collect() (data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(app.columns))
	for _, pipeline := range app.pipelines {
		builds, err := app.client.GetMostRecentBuilds(pipeline, app.lastNBuilds)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect aggregated performance statistics for pipeline %s: %v", pipeline, err)
		}
		for _, build := range builds {
			if build.FinishedAt == nil {
				continue
			}

			skippedTasks := getSkippedTasks(build)
			err := result.AddRow(pipeline.Org, pipeline.Slug, *build.Number, build.ScheduledAt.Time, getDifferenceSeconds(build.ScheduledAt, build.FinishedAt), skippedTasks, *build.State)
			if err != nil {
				return nil, fmt.Errorf("Failed to add result for build %d in %s: %v", *build.Number, pipeline.Slug, err)
			}

		}
	}
	return result, nil
}

// CREATE TABLE aggregated_pipeline_performance (org VARCHAR(255), pipeline VARCHAR(255), build INT, scheduled DATETIME, total_time_seconds FLOAT, skipped_tasks VARCHAR(255), result VARCHAR(16), PRIMARY KEY(org, pipeline, build));
func CreateAggregatedPipelinePerformance(client clients.BuildkiteClient, lastNBuilds int, pipelines ...*data.PipelineID) *AggregatedPipelinePerformance {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"scheduled", false}, Column{"total_time_seconds", false}, Column{"skipped_tasks", false}, Column{"result", false}}
	return &AggregatedPipelinePerformance{client: client, pipelines: pipelines, columns: columns, lastNBuilds: lastNBuilds}
}
