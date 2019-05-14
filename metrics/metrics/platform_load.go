package metrics

import (
	"fmt"
	"time"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type PlatformLoad struct {
	client  *clients.BuildkiteClient
	columns []Column
	builds  int
}

func (pl *PlatformLoad) Name() string {
	return "platform_load"
}

func (pl *PlatformLoad) Columns() []Column {
	return pl.columns
}

func (pl *PlatformLoad) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(pl.columns))
	builds, err := pl.client.GetMostRecentBuilds("all", pl.builds)
	if err != nil {
		return nil, fmt.Errorf("Cannot get builds to determine platform load: %v", err)
	}

	timestamp := time.Now()
	allPlatforms := make(map[string]bool)
	waiting := make(map[string]int)
	running := make(map[string]int)
	for _, build := range builds {
		for _, job := range build.Jobs {
			// Do not use getPlatform() since it may return "rbe", but here we're only interested in the actual worker OS (which would be "linux" in the rbe case).
			platform := getPlatformFromAgentQueryRules(job.AgentQueryRules)
			if platform == "" || job.CreatedAt == nil || job.FinishedAt != nil {
				continue
			}
			allPlatforms[platform] = true
			switch *job.State {
			case "running":
				running[platform] += 1
			case "scheduled":
				/*
					State "scheduled" = waiting for a worker to become available
					State "waiting" / "waiting_failed" = waiting for another task to finish

					We're only interested in "scheduled" jobs since they may indicate a shortage of workers.
				*/
				waiting[platform] += 1
			}
		}
	}

	for platform := range allPlatforms {
		err := result.AddRow(timestamp, platform, waiting[platform], running[platform])
		if err != nil {
			return nil, fmt.Errorf("Failed to add result for platform %s: %v", platform, err)
		}
	}
	return result, nil
}

// CREATE TABLE platform_load (timestamp DATETIME, platform VARCHAR(255), waiting_jobs INT, running_jobs INT, PRIMARY KEY(timestamp, platform));
func CreatePlatformLoad(client *clients.BuildkiteClient, builds int) *PlatformLoad {
	columns := []Column{Column{"timestamp", true}, Column{"platform", true}, Column{"waiting_jobs", false}, Column{"running_jobs", false}}
	return &PlatformLoad{client: client, columns: columns, builds: builds}
}
