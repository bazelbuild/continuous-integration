package metrics

import (
	"fmt"
	"strings"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

const macPlatform = "macos"

type MacPerformance struct {
	perfMetric *PipelinePerformance
	columns    []Column
}

func (mp *MacPerformance) Name() string {
	return "mac_performance"
}

func (mp *MacPerformance) Columns() []Column {
	return mp.columns
}

func (mp *MacPerformance) Collect() (data.DataSet, error) {
	legacyPerfData, err := mp.perfMetric.Collect()
	if err != nil {
		return nil, fmt.Errorf("Cannot calculate macOS metrics: %v", err)
	}

	perfData, ok := legacyPerfData.(*pipelinePerformanceSet)
	if !ok {
		return nil, fmt.Errorf("Invalid type %T of performance data", legacyPerfData)
	}

	result := data.CreateDataSet(GetColumnNames(mp.columns))
	skippedBuilds := make(map[int]struct{})
	for _, row := range perfData.rows {
		if _, ok := skippedBuilds[row.build]; ok {
			continue
		}

		err = nil
		if getPlatformFromJobName(&row.job) == macPlatform {
			err = result.AddRow(row.org, row.pipeline, row.build, getShardFromJobName(row.job), row.waitTimeSeconds, row.runTimeSeconds, false)
		} else if strings.Contains(row.skippedTasks, macPlatform) {
			err = result.AddRow(row.org, row.pipeline, row.build, nil, nil, nil, true)
			skippedBuilds[row.build] = struct{}{}
		}

		if err != nil {
			return nil, fmt.Errorf("Pipeline %s/%s: Failed to add result for job %s of build %d: %v", row.org, row.pipeline, row.job, row.build, err)
		}
	}
	return result, nil
}

// CREATE TABLE mac_performance (org VARCHAR(255), pipeline VARCHAR(255), build INT, shard INT, wait_time_seconds FLOAT, run_time_seconds FLOAT, skipped BOOL, PRIMARY KEY(org, pipeline, build, shard));
func CreateMacPerformance(client clients.BuildkiteClient, lastNBuilds int, pipelines ...*data.PipelineID) *MacPerformance {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"shard", true}, Column{"wait_time_seconds", false}, Column{"run_time_seconds", false}, Column{"skipped", false}}
	perfMetric := CreatePipelinePerformance(client, lastNBuilds, pipelines...)
	return &MacPerformance{perfMetric: perfMetric, columns: columns}
}
