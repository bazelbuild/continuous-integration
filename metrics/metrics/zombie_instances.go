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
		err = result.AddRow(time.Now(), instance.Project, instance.Zone, instance.Name, instance.Status, onlineTime.Seconds())
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

// CREATE TABLE zombie_instances (timestamp DATETIME, cloud_project VARCHAR(255), zone VARCHAR(255), instance VARCHAR(255), status VARCHAR(255), seconds_online FLOAT, PRIMARY KEY(timestamp, cloud_project, zone, instance));
func CreateZombieInstances(computeClient *clients.ComputeEngineClient, cloudProjects []string, bkClient clients.BuildkiteClient, bkOrgs []string, gracePeriod time.Duration) *ZombieInstances {
	columns := []Column{Column{"timestamp", true}, Column{"cloud_project", true}, Column{"zone", true}, Column{"instance", true}, Column{"status", false}, Column{"seconds_online", false}}
	return &ZombieInstances{computeClient: computeClient, cloudProjects: cloudProjects, bkClient: bkClient, bkOrgs: bkOrgs, columns: columns, gracePeriod: gracePeriod}
}
