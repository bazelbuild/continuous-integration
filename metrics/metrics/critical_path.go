package metrics

import (
	"fmt"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

type CriticalPath struct {
	client      clients.BuildkiteClient
	pipelines   []*data.PipelineID
	columns     []Column
	lastNBuilds int
	debug       bool
}

func (cp *CriticalPath) Name() string {
	return "critical_path"
}

func (cp *CriticalPath) Columns() []Column {
	return cp.columns
}

func (*CriticalPath) Type() MetricType {
	return BuildBasedMetric
}

func (*CriticalPath) RelevantDelta() int {
	return 200 // builds
}

func (cp *CriticalPath) Collect() (data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(cp.columns))
	for _, pipeline := range cp.pipelines {
		builds, err := cp.client.GetMostRecentBuilds(pipeline, cp.lastNBuilds)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect critical path statistics for pipeline %s: %v", pipeline, err)
		}
		for _, build := range builds {
			if build.FinishedAt == nil {
				continue
			}
			// TODO(fweikert): remove
			if cp.debug {
				fmt.Printf("%v -> %v -> %v -> %v (%d)\n", *build.ScheduledAt, *build.CreatedAt, *build.StartedAt, *build.FinishedAt, *build.Number)
				for _, job := range build.Jobs {
					if job.Name != nil {
						fmt.Printf("%v -> %v -> %v -> %v -> %v (%s)\n", *job.ScheduledAt, *job.CreatedAt, *job.RunnableAt, *job.StartedAt, *job.FinishedAt, *job.Name)
					}
				}
			}

			// Caveat: The Buildkite API only returns the latest invocation of each job within a given build,
			// which causes a problem when a failing build is retried via the web UI. In this case the time
			// between the original run and the retry will be counted as wait time by this code.
			performance, err := analyzeJobsPerformance(build.Jobs)
			if err != nil {
				return nil, fmt.Errorf("Could not calculate job performance for build %d: %v", *build.Number, err)
			}

			err = result.AddRow(pipeline.Org, pipeline.Slug, *build.Number, performance.totalWaitSeconds, performance.totalRunSeconds, performance.longestRunningTaskName, performance.longestRunningTaskRunSeconds, *build.State)
			if err != nil {
				return nil, fmt.Errorf("Failed to add result for build %d: %v", *build.Number, err)
			}
		}
	}
	return result, nil
}

// CREATE TABLE critical_path (org VARCHAR(255), pipeline VARCHAR(255), build INT, wait_time_seconds FLOAT, run_time_seconds FLOAT, longest_task_name VARCHAR(255), longest_task_time_seconds FLOAT, result VARCHAR(255), PRIMARY KEY(org, pipeline, build));
func CreateCriticalPath(client clients.BuildkiteClient, lastNBuilds int, pipelines ...*data.PipelineID) *CriticalPath {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"wait_time_seconds", false}, Column{"run_time_seconds", false}, Column{"longest_task_name", false}, Column{"longest_task_time_seconds", false}, Column{"result", false}}
	return &CriticalPath{client: client, pipelines: pipelines, columns: columns, lastNBuilds: lastNBuilds, debug: false}
}
