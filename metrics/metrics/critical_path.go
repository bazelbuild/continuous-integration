package metrics

import (
	"fmt"
	"sort"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/go-buildkite/buildkite"
)

type CriticalPath struct {
	client      *clients.BuildkiteClient
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
			wait_time_seconds, longest_task_name, longest_task_time_seconds, err := analyzeJobs(build.ScheduledAt, build.Jobs)
			if err != nil {
				return nil, fmt.Errorf("Could not calculate waiting time for build %d: %v", *build.Number, err)
			}

			run_time_seconds := getDifferenceSeconds(build.CreatedAt, build.FinishedAt) - wait_time_seconds
			err = result.AddRow(pipeline.Org, pipeline.Slug, *build.Number, wait_time_seconds, run_time_seconds, longest_task_name, longest_task_time_seconds, *build.State)
			if err != nil {
				return nil, fmt.Errorf("Failed to add result for build %d: %v", *build.Number, err)
			}
		}
	}
	return result, nil
}

type event struct {
	*buildkite.Timestamp
	runDelta int
}

func analyzeJobs(scheduleTime *buildkite.Timestamp, jobs []*buildkite.Job) (wait_time_seconds float64, longest_task_name string, longest_task_time_seconds float64, err error) {
	events := make([]event, 0)
	for _, job := range jobs {
		if job.Name == nil || job.FinishedAt == nil {
			continue
		}
		// Job lifecycle: scheduled -> created -> runnable -> started -> finished
		// wait time = started - runnable
		// run time = finished - started
		// total time = finished - runnable
		// Scheduled and created are affected by "wait" steps, so we don't look at them here.
		duration := getDifferenceSeconds(job.RunnableAt, job.FinishedAt)
		if duration > longest_task_time_seconds {
			longest_task_name = *job.Name
			longest_task_time_seconds = duration
		}
		events = append(events, event{job.StartedAt, 1}, event{job.FinishedAt, -1})
	}
	sortFunc := func(i, j int) bool { return events[i].Time.Before(events[j].Time) }
	sort.Slice(events, sortFunc)

	runningTasks := 0
	prevTime := scheduleTime
	for _, evt := range events {
		if runningTasks == 0 {
			wait_time_seconds += getDifferenceSeconds(prevTime, evt.Timestamp)
		}
		runningTasks += evt.runDelta
		prevTime = evt.Timestamp
	}
	if runningTasks > 0 {
		err = fmt.Errorf("There are %d unfinished jobs", runningTasks)
	}
	return
}

// CREATE TABLE critical_path (org VARCHAR(255), pipeline VARCHAR(255), build INT, wait_time_seconds FLOAT, run_time_seconds FLOAT, longest_task_name VARCHAR(255), longest_task_time_seconds FLOAT, result VARCHAR(255), PRIMARY KEY(org, pipeline, build));
func CreateCriticalPath(client *clients.BuildkiteClient, lastNBuilds int, pipelines ...*data.PipelineID) *CriticalPath {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"wait_time_seconds", false}, Column{"run_time_seconds", false}, Column{"longest_task_name", false}, Column{"longest_task_time_seconds", false}, Column{"result", false}}
	return &CriticalPath{client: client, pipelines: pipelines, columns: columns, lastNBuilds: lastNBuilds, debug: false}
}
