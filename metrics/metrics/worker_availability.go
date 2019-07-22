package metrics

import (
	"fmt"
	"strings"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

type WorkerAvailability struct {
	client  clients.BuildkiteClient
	orgs    []string
	columns []Column
}

func (wa *WorkerAvailability) Name() string {
	return "worker_availability"
}

func (wa *WorkerAvailability) Columns() []Column {
	return wa.columns
}

func (wa *WorkerAvailability) Type() MetricType {
	return TimeBasedMetric
}

func (wa *WorkerAvailability) RelevantDelta() int {
	return 24 * 60 * 60 // 24 hours
}

func (wa *WorkerAvailability) Collect() (data.DataSet, error) {
	ts := time.Now()
	result := data.CreateDataSet(GetColumnNames(wa.columns))
	for _, org := range wa.orgs {
		allPlatforms, err := wa.getIdleAndBusyCountsPerPlatform(org)
		if err != nil {
			return nil, err
		}
		for platform, counts := range allPlatforms {
			err = result.AddRow(ts, org, platform, counts[0], counts[1])
			if err != nil {
				return nil, err
			}
		}
	}
	return result, nil
}

func (wa *WorkerAvailability) getIdleAndBusyCountsPerPlatform(org string) (map[string]*[2]int, error) {
	agents, err := wa.client.GetAgents(org)
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

// CREATE TABLE worker_availability (timestamp DATETIME, org VARCHAR(255), platform VARCHAR(255), idle_count INT, busy_count INT, PRIMARY KEY(timestamp, org, platform));
func CreateWorkerAvailability(client clients.BuildkiteClient, orgs ...string) *WorkerAvailability {
	columns := []Column{Column{"timestamp", true}, Column{"org", true}, Column{"platform", true}, Column{"idle_count", false}, Column{"busy_count", false}}
	return &WorkerAvailability{client: client, orgs: orgs, columns: columns}
}
