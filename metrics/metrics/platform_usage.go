package metrics

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type PlatformUsage struct {
	client  *clients.BuildkiteClient
	columns []Column
	builds  int
}

func (pu *PlatformUsage) Name() string {
	return "platform_usage"
}

func (pu *PlatformUsage) Columns() []Column {
	return pu.columns
}

func (pu *PlatformUsage) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(pu.columns))
	builds, err := pu.client.GetMostRecentBuilds("all", pu.builds)
	if err != nil {
		return nil, fmt.Errorf("Cannot collect platform usage: %v", err)
	}

	for _, build := range builds {
		pipeline := *build.Pipeline.Slug
		for _, job := range build.Jobs {
			platform := getPlatform(job)
			if platform == "" {
				continue
			}
			diff := getDifferenceSeconds(job.StartedAt, job.FinishedAt)
			if diff < 0 {
				continue
			}
			err := result.AddRow(pipeline, *build.Number, platform, diff)
			if err != nil {
				return nil, fmt.Errorf("Failed to add result for build %d in pipeline %s on platform %s: %v", *build.Number, pipeline, platform, err)
			}
		}
	}
	return result, nil
}

// CREATE TABLE platform_usage (pipeline VARCHAR(255), build INT, platform VARCHAR(255), usage_seconds FLOAT, PRIMARY KEY(pipeline, build, platform));
func CreatePlatformUsage(client *clients.BuildkiteClient, builds int) *PlatformUsage {
	columns := []Column{Column{"pipeline", true}, Column{"build", true}, Column{"platform", true}, Column{"usage_seconds", false}}
	return &PlatformUsage{client: client, columns: columns, builds: builds}
}
