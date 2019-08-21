package metrics

import (
	"fmt"
	"strings"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

const ciWorkerNamePrefix = "bk-"

type ZombieInstances struct {
	computeClient *clients.ComputeEngineClient
	cloudProjects []string

	bkClient clients.BuildkiteClient
	bkOrgs   []string

	gracePeriod time.Duration
	columns     []Column
}

func (zi *ZombieInstances) Name() string {
	return "zombie_instances"
}

func (zi *ZombieInstances) Columns() []Column {
	return zi.columns
}

func (*ZombieInstances) Type() MetricType {
	return TimeBasedMetric
}

func (*ZombieInstances) RelevantDelta() int {
	return 10 * 60 // 10 minutes in seconds
}

func (zi *ZombieInstances) Collect() (data.DataSet, error) {
	agentHostNameIndex, err := zi.getAgentHostNameIndex()
	if err != nil {
		return nil, fmt.Errorf("Failed to fetch Buildkite agents: %v", err)
	}

	instances, err := zi.getInstances()
	if err != nil {
		return nil, fmt.Errorf("Failed to fetch GCE instances: %v", err)
	}

	result := data.CreateDataSet(GetColumnNames(zi.columns))
	for _, instance := range instances {
		if _, ok := agentHostNameIndex[instance.Name]; ok {
			// Agent is up and running
			continue
		}
		if instance.Status == "STOPPING" {
			continue
		}
		onlineTime := time.Since(instance.CreationTime)
		if onlineTime < zi.gracePeriod {
			// VM was started only very recently
			continue
		}
		err = result.AddRow(instance.Project, instance.Zone, instance.Name, instance.Status, onlineTime.Seconds(), time.Now())
		if err != nil {
			return nil, err
		}
	}
	return result, nil
}

func (zi *ZombieInstances) getInstances() ([]*clients.ComputeInstance, error) {
	ciInstances := make([]*clients.ComputeInstance, 0)
	allInstances, err := zi.computeClient.GetAllInstances(zi.cloudProjects)
	if err != nil {
		return nil, err
	}
	for _, instance := range allInstances {
		if strings.HasPrefix(instance.Name, ciWorkerNamePrefix) {
			ciInstances = append(ciInstances, instance)
		}
	}
	return ciInstances, nil
}

func (zi *ZombieInstances) getAgentHostNameIndex() (map[string]bool, error) {
	hostNameIndex := make(map[string]bool)
	for _, org := range zi.bkOrgs {
		agents, err := zi.bkClient.GetAgents(org)
		if err != nil {
			return nil, err
		}
		for _, agent := range agents {
			hostNameIndex[*agent.Hostname] = false
		}
	}
	return hostNameIndex, nil
}

// CREATE TABLE zombie_instances (cloud_project VARCHAR(255), zone VARCHAR(255), instance VARCHAR(255), status VARCHAR(255), seconds_online FLOAT, timestamp DATETIME, PRIMARY KEY(cloud_project, zone, instance));
func CreateZombieInstances(computeClient *clients.ComputeEngineClient, cloudProjects []string, bkClient clients.BuildkiteClient, bkOrgs []string, gracePeriod time.Duration) *ZombieInstances {
	columns := []Column{Column{"cloud_project", true}, Column{"zone", true}, Column{"instance", true}, Column{"status", false}, Column{"seconds_online", false}, Column{"timestamp", false}}
	return &ZombieInstances{computeClient: computeClient, cloudProjects: cloudProjects, bkClient: bkClient, bkOrgs: bkOrgs, columns: columns, gracePeriod: gracePeriod}
}
