package metrics

import (
	"fmt"
	"strings"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

type PipelinePerformance struct {
	client      clients.BuildkiteClient
	pipelines   []*data.PipelineID
	columns     []Column
	lastNBuilds int
}

func (pp *PipelinePerformance) Name() string {
	return "pipeline_performance"
}

func (pp *PipelinePerformance) Columns() []Column {
	return pp.columns
}

func (*PipelinePerformance) Type() MetricType {
	return BuildBasedMetric
}

func (*PipelinePerformance) RelevantDelta() int {
	return 100 // builds
}

func (pp *PipelinePerformance) Collect() (data.DataSet, error) {
	result := &pipelinePerformanceSet{headers: GetColumnNames(pp.columns)}
	for _, pipeline := range pp.pipelines {
		builds, err := pp.client.GetMostRecentBuilds(pipeline, pp.lastNBuilds)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect performance statistics for pipeline %s: %v", pipeline, err)
		}
		for _, build := range builds {

			fmt.Println(*build.Number)

			skippedTasks := getSkippedTasks(build)
			for _, job := range build.Jobs {
				if job != nil && job.Agent.Hostname != nil {
					hn := *job.Agent.Hostname
					if strings.Contains(hn, "imac") {
						fmt.Printf("\t%s\n", hn)
					}
				}
				if !isFinishedWorkerTask(job) {
					continue
				}
				row := &pipelinePerformanceRow{org: pipeline.Org,
					pipeline:        pipeline.Slug,
					build:           *build.Number,
					job:             *job.Name,
					creationTime:    job.RunnableAt.Time,
					waitTimeSeconds: getDifferenceSeconds(job.RunnableAt, job.StartedAt),
					runTimeSeconds:  getDifferenceSeconds(job.StartedAt, job.FinishedAt),
					skippedTasks:    skippedTasks,
				}
				result.rows = append(result.rows, row)
			}
		}
	}
	return result, nil
}

// CREATE TABLE pipeline_performance (org VARCHAR(255), pipeline VARCHAR(255), build INT, job VARCHAR(255), creation_time DATETIME, wait_time_seconds FLOAT, run_time_seconds FLOAT, skipped_tasks VARCHAR(255), PRIMARY KEY(org, pipeline, build, job));
func CreatePipelinePerformance(client clients.BuildkiteClient, lastNBuilds int, pipelines ...*data.PipelineID) *PipelinePerformance {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"job", true}, Column{"creation_time", false}, Column{"wait_time_seconds", false}, Column{"run_time_seconds", false}, Column{"skipped_tasks", false}}
	return &PipelinePerformance{client: client, pipelines: pipelines, columns: columns, lastNBuilds: lastNBuilds}
}

type pipelinePerformanceRow struct {
	org             string
	pipeline        string
	build           int
	job             string
	creationTime    time.Time
	waitTimeSeconds float64
	runTimeSeconds  float64
	skippedTasks    string
}

type pipelinePerformanceSet struct {
	headers []string
	rows    []*pipelinePerformanceRow
}

func (s *pipelinePerformanceSet) GetData() *data.LegacyDataSet {
	rawSet := data.CreateDataSet(s.headers)
	for _, row := range s.rows {
		rawRow := []interface{}{row.org, row.pipeline, row.build, row.job, row.creationTime, row.waitTimeSeconds, row.runTimeSeconds, row.skippedTasks}
		rawSet.Data = append(rawSet.Data, rawRow)
	}
	return rawSet
}
