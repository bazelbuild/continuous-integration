package metrics

import (
	"fmt"
	"strconv"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/go-buildkite/buildkite"
)

type BuildsPerChange struct {
	client    *clients.BuildkiteClient
	columns   []Column
	pipelines []string
	builds    int
}

func (bps *BuildsPerChange) Name() string {
	return "builds_per_change"
}

func (bps *BuildsPerChange) Columns() []Column {
	return bps.columns
}

const changelistMetaDataKey = "PiperOrigin-RevId"

func (bps *BuildsPerChange) Collect() (data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(bps.columns))
	buildsPerPipeline := make(map[string]map[int]int)
	for _, pipeline := range bps.pipelines {
		builds, err := bps.client.GetMostRecentBuilds(pipeline, bps.builds)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect builds_per_change statistics for pipeline %s: %v", pipeline, err)
		}
		buildsPerChange := make(map[int]int)
		for _, build := range builds {
			change, err := getChangeNumber(build)
			if err != nil {
				return nil, err
			} else if change < 0 {
				continue
			}
			if _, ok := buildsPerChange[change]; !ok {
				buildsPerChange[change] = 0
			}
			buildsPerChange[change] += 1
		}
		buildsPerPipeline[pipeline] = buildsPerChange
	}
	for pipeline, buildsPerChange := range buildsPerPipeline {
		for change, builds := range buildsPerChange {
			err := result.AddRow(pipeline, change, builds)
			if err != nil {
				return nil, fmt.Errorf("Failed to add result for change %d and pipeline %s: %v", change, pipeline, err)
			}
		}
	}
	return result, nil
}

func getChangeNumber(build buildkite.Build) (int, error) {
	pipeline := *build.Pipeline.Slug
	metaData, ok := build.MetaData.(map[string]interface{})
	if !ok {
		return -1, fmt.Errorf("Invalid meta data on build %d in pipeline %s.", *build.Number, pipeline)
	}
	change, ok := metaData[changelistMetaDataKey]
	if !ok {
		return -1, nil
	}
	changeNumber, err := strconv.Atoi(fmt.Sprintf("%v", change))
	if err != nil {
		return -1, fmt.Errorf("Meta data of build %d in pipeline %s: '%v' is not a valid changelist number.", *build.Number, pipeline, change)
	}
	return changeNumber, nil
}

// CREATE TABLE builds_per_change (pipeline VARCHAR(255), change INT, builds INT, PRIMARY KEY(pipeline, change));
func CreateBuildsPerChange(client *clients.BuildkiteClient, builds int, pipelines ...string) *BuildsPerChange {
	columns := []Column{Column{"pipeline", true}, Column{"change", true}, Column{"builds", false}}
	return &BuildsPerChange{client: client, pipelines: pipelines, columns: columns, builds: builds}
}
