package metrics

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type PlatformUsage struct {
	client  clients.BuildkiteClient
	orgs    []string
	columns []Column
	builds  int
}

func (pu *PlatformUsage) Name() string {
	return "platform_usage"
}

func (pu *PlatformUsage) Columns() []Column {
	return pu.columns
}

func (pu *PlatformUsage) Collect() (data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(pu.columns))
	for _, org := range pu.orgs {
		pid := &data.PipelineID{Org: org, Slug: "all"}
		builds, err := pu.client.GetMostRecentBuilds(pid, pu.builds)
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
				err := result.AddRow(org, pipeline, *build.Number, platform, diff)
				if err != nil {
					return nil, fmt.Errorf("Failed to add result for build %d in pipeline %s on platform %s: %v", *build.Number, pipeline, platform, err)
				}
			}
		}
	}
	return result, nil
}

// CREATE TABLE platform_usage (org VARCHAR(255), pipeline VARCHAR(255), build INT, platform VARCHAR(255), usage_seconds FLOAT, PRIMARY KEY(org, pipeline, build, platform));
func CreatePlatformUsage(client clients.BuildkiteClient, builds int, orgs ...string) *PlatformUsage {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"platform", true}, Column{"usage_seconds", false}}
	return &PlatformUsage{client: client, orgs: orgs, columns: columns, builds: builds}
}
