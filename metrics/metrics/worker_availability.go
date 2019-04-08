package metrics

import (
	"fmt"
	"strings"
	"time"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type WorkerAvailability struct {
	client  *clients.BuildkiteClient
	columns []Column
}

func (wa *WorkerAvailability) Name() string {
	return "worker_availability"
}

func (wa *WorkerAvailability) Columns() []Column {
	return wa.columns
}

func (wa *WorkerAvailability) Collect() (*data.DataSet, error) {
	ts := time.Now().Unix()
	allPlatforms, err := wa.getIdleAndBusyCountsPerPlatform()
	if err != nil {
		return nil, err
	}
	result := data.CreateDataSet(GetColumnNames(wa.columns))
	for platform, counts := range allPlatforms {
		err = result.AddRow(ts, platform, counts[0], counts[1])
		if err != nil {
			return nil, err
		}
	}
	return result, nil
}

func (wa *WorkerAvailability) getIdleAndBusyCountsPerPlatform() (map[string]*[2]int, error) {
	agents, err := wa.client.GetAgents()
	if err != nil {
		return nil, fmt.Errorf("Cannot retrieve agents from Buildkite: %v", err)
	}

	allPlatforms := make(map[string]*[2]int)
	for _, a := range agents {
		platform, err := getPlatformForHost(*a.Hostname)
		if err != nil {
			return nil, err
		}
		if _, ok := allPlatforms[platform]; !ok {
			allPlatforms[platform] = &[2]int{0, 0}
		}
		var index int
		if a.Job != nil {
			index = 1
		}
		allPlatforms[platform][index] += 1
	}
	return allPlatforms, nil
}

func getPlatformForHost(hostName string) (string, error) {
	pos := strings.LastIndex(hostName, "-")
	if pos < 0 {
		return "", fmt.Errorf("Unknown host name '%s' cannot be resolved to a platform.", hostName)
	}
	return hostName[:pos], nil
}

// CREATE TABLE worker_availability (timestamp BIGINT, platform VARCHAR(255), idle_count INT, busy_count INT, PRIMARY KEY(timestamp, platform));
func CreateWorkerAvailability(client *clients.BuildkiteClient) *WorkerAvailability {
	columns := []Column{Column{"timestamp", true}, Column{"platform", true}, Column{"idle_count", false}, Column{"busy_count", false}}
	return &WorkerAvailability{client: client, columns: columns}
}
