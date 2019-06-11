package metrics

import (
	"fmt"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
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
	perfData, err := mp.perfMetric.Collect()
	if err != nil {
		return nil, fmt.Errorf("Cannot calculate macOS metrics: %v", err)
	}

	result := data.CreateDataSet(GetColumnNames(mp.columns))
	var lastAdded string
	for _, row := range perfData.GetData().Data {
		str := data.GetRowAsStrings(row)
		build := str[1]
		jobName := str[2]
		skipped_tasks := str[6]

		if build != lastAdded {
			err = nil
			if getPlatformFromJobName(&jobName) == macPlatform {
				err = result.AddRow(row[0], row[1], row[4], row[5], false)
				lastAdded = build
			} else if strings.Contains(skipped_tasks, macPlatform) {
				err = result.AddRow(row[0], row[1], -1, -1, true)
				lastAdded = build
			}

			if err != nil {
				return nil, fmt.Errorf("Pipeline %s: Failed to add result for job %s of build %s: %v", str[0], str[2], str[1], err)
			}
		}
	}
	return result, nil
}

// CREATE TABLE mac_performance (org VARCHAR(255), pipeline VARCHAR(255), build INT, wait_time_seconds FLOAT, run_time_seconds FLOAT, skipped BOOL, PRIMARY KEY(org, pipeline, build));
func CreateMacPerformance(client *clients.BuildkiteClient, lastNBuilds int, pipelines ...*data.PipelineID) *MacPerformance {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"wait_time_seconds", false}, Column{"run_time_seconds", false}, Column{"skipped", false}}
	perfMetric := CreatePipelinePerformance(client, lastNBuilds, pipelines...)
	return &MacPerformance{perfMetric: perfMetric, columns: columns}
}
