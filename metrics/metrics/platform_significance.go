package metrics

import (
	"fmt"
	"log"
	"strconv"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type PlatformSignificance struct {
	buildSuccess *BuildSuccess
	columns      []Column
}

func (ps *PlatformSignificance) Name() string {
	return "platform_significance"
}

func (ps *PlatformSignificance) Columns() []Column {
	return ps.columns
}

type pipelineStats struct {
	totalBuilds           int
	setupFailed           int
	passingBuilds         int
	canceledBuilds        int
	linuxFailures         int
	macosFailures         int
	windowsFailures       int
	rbeFailures           int
	multiPlatformFailures int
}

func (ps *PlatformSignificance) Collect() (data.DataSet, error) {
	buildResult, err := ps.buildSuccess.Collect()
	if err != nil {
		return nil, err
	}

	stats, err := collectPipelineResults(buildResult)
	if err != nil {
		return nil, fmt.Errorf("Failed to collect pipeline results: %v", err)
	}

	result := data.CreateDataSet(GetColumnNames(ps.columns))
	for pipeline, values := range stats {
		result.AddRow(pipeline, values.totalBuilds, values.passingBuilds, values.canceledBuilds, values.setupFailed, values.linuxFailures, values.macosFailures, values.windowsFailures, values.rbeFailures, values.multiPlatformFailures)
	}
	return result, nil
}

func collectPipelineResults(buildResult data.DataSet) (map[string]*pipelineStats, error) {
	stats := make(map[string]*pipelineStats)
	for _, row := range buildResult.GetData().Data {
		values, err := toString(row)
		if err != nil {
			return nil, fmt.Errorf("Could not process build_success results: %v", err)
		}
		pipeline := values[0]
		if _, ok := stats[pipeline]; !ok {
			stats[pipeline] = &pipelineStats{}
		}

		passed := true
		canceled := false
		failures := make([]int, 0)
		missingData := 0
		for i := 1; i < len(values); i += 1 {
			if values[i] == "" {
				// Count the columns without data. If all columns have no data, this means that the setup step failed or was canceled.
				// Otherwise missing data means that the respective platform is not part of a given pipeline.
				missingData += 1
			} else if values[i] != passingState {
				passed = false
				if values[i] == canceledState {
					canceled = true
					break
				} else if values[i] == failedState {
					failures = append(failures, i)
				}
			}
		}

		stats[pipeline].totalBuilds += 1
		if missingData == len(values)-1 {
			stats[pipeline].setupFailed += 1
		} else if canceled {
			stats[pipeline].canceledBuilds += 1
		} else if passed {
			stats[pipeline].passingBuilds += 1
		} else if len(failures) > 1 {
			stats[pipeline].multiPlatformFailures += 1
		} else if len(failures) == 1 {
			switch failures[0] {
			case 1:
				stats[pipeline].linuxFailures += 1
				log.Printf("Linux only: %s/%d\n", pipeline, row[1])
			case 2:
				stats[pipeline].macosFailures += 1
				log.Printf("MacOS only: %s/%d\n", pipeline, row[1])
			case 3:
				stats[pipeline].windowsFailures += 1
				log.Printf("Windows only: %s/%d\n", pipeline, row[1])
			case 4:
				stats[pipeline].rbeFailures += 1
				log.Printf("RBE only: %s/%d\n", pipeline, row[1])
			}
		}
	}
	return stats, nil
}

func toString(row []interface{}) ([]string, error) {
	result := make([]string, 0)
	for i, v := range row {
		var str string
		if number, ok := v.(int); ok {
			str = strconv.Itoa(number)
		} else {
			str, ok = v.(string)
			if !ok {
				return nil, fmt.Errorf("Expected string in column %v: %s", i, v)
			}
		}
		result = append(result, str)
	}
	return result, nil
}

// CREATE TABLE platform_significance (org VARCHAR(255), pipeline VARCHAR(255), total_builds INT, passing_builds INT, canceled_builds INT, setup_failed INT, linux_failures INT, macos_failures INT, windows_failures INT, rbe_failures INT, multi_platform_failures INT, PRIMARY KEY(org, pipeline));
func CreatePlatformSignificance(client *clients.BuildkiteClient, builds int, pipelines ...*data.PipelineID) *PlatformSignificance {
	buildSuccess := CreateBuildSuccess(client, builds, pipelines...)
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"total_builds", false}, Column{"passing_builds", false}, Column{"canceled_builds", false}, Column{"setup_failed", false}, Column{"linux_failures", false}, Column{"macos_failures", false}, Column{"windows_failures", false}, Column{"rbe_failures", false}, Column{"multi_platform_failures", false}}
	return &PlatformSignificance{buildSuccess: buildSuccess, columns: columns}
}
