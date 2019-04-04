package metrics

import (
	"fmt"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type BuildSuccess struct {
	client    *clients.BuildkiteClient
	pipelines []string
	columns   []Column
}

func (bs *BuildSuccess) Name() string {
	return "build_success"
}

func (bs *BuildSuccess) Columns() []Column {
	return bs.columns
}

func (bs *BuildSuccess) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(bs.columns))
	for _, pipeline := range bs.pipelines {
		builds, err := bs.client.GetMostRecentBuilds(pipeline, 100)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect build success statistics for pipeline %s: %v", pipeline, err)
		}
		for _, build := range builds {
			platformStates := make(map[string]string)
			includeBuild := true

			for _, job := range build.Jobs {
				if *job.State != "passed" && *job.State != "failed" {
					includeBuild = false
					break
				}
				platform := getOperatingSystem(*job.Name)
				if platform == "" {
					continue
				}
				mergeState(platformStates, platform, *job.State)
			}
			if includeBuild {
				err := result.AddRow(pipeline, *build.Number, platformStates["linux"], platformStates["macos"], platformStates["windows"])
				if err != nil {
					return nil, fmt.Errorf("Failed to add result for build %d: %v", *build.Number, err)
				}
			}
		}
	}
	return result, nil
}

func getOperatingSystem(jobName string) string {
	if strings.Contains(jobName, "ubuntu") {
		return "linux"
	} else if strings.Contains(jobName, "windows") {
		return "windows"
	} else if strings.Contains(jobName, "darwin") {
		return "macos"
	} else {
		return ""
	}
}

func mergeState(platformStates map[string]string, platform, newState string) {
	oldState, ok := platformStates[platform]
	if ok {
		if oldState == "failed" || newState == "failed" {
			platformStates[platform] = "failed"
		} else {
			platformStates[platform] = "passed"
		}
	} else {
		platformStates[platform] = newState
	}
}

// CREATE TABLE build_success (pipeline VARCHAR(255), build INT, linux VARCHAR(255), macos VARCHAR(255), windows VARCHAR(255), PRIMARY KEY(pipeline, build));
func CreateBuildSuccess(client *clients.BuildkiteClient, pipelines ...string) *BuildSuccess {
	columns := []Column{Column{"pipeline", true}, Column{"build", true}, Column{"linux", false}, Column{"macos", false}, Column{"windows", false}}
	return &BuildSuccess{client: client, pipelines: pipelines, columns: columns}
}
