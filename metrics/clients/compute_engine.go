package clients

import (
	"context"
	"fmt"
	"time"

	compute "google.golang.org/api/compute/v1"
)

type ComputeInstance struct {
	Name         string
	Zone         string
	Project      string
	Status       string
	CreationTime time.Time
}

type ComputeEngineClient struct {
	service *compute.Service
}

func CreateComputeEngineClient() (*ComputeEngineClient, error) {
	ctx := context.Background()
	service, err := compute.NewService(ctx)
	if err != nil {
		return nil, err
	}
	return &ComputeEngineClient{service: service}, nil
}

func (c *ComputeEngineClient) GetAllInstances(projects []string) ([]*ComputeInstance, error) {
	allInstances := make([]*ComputeInstance, 0)
	for _, project := range projects {
		projectInstances, err := c.GetAllInstanceForProject(project)
		if err != nil {
			return nil, err
		}
		allInstances = append(allInstances, projectInstances...)
	}
	return allInstances, nil
}

func (c *ComputeEngineClient) GetAllInstanceForProject(project string) ([]*ComputeInstance, error) {
	instances := make([]*ComputeInstance, 0)
	request := c.service.Instances.AggregatedList(project)
	for {
		response, err := request.Do()
		if err != nil {
			return nil, fmt.Errorf("Could not retrieve instances for project '%s': %v", project, err)
		}
		for zone, instanceList := range response.Items {
			for _, instance := range instanceList.Instances {
				creationTime, error := time.Parse(time.RFC3339, instance.CreationTimestamp)
				if error != nil {
					return nil, fmt.Errorf("Failed to parse creation time for instance %s/%s: %v", zone, instance.Name, err)
				}
				instances = append(instances, &ComputeInstance{Name: instance.Name, Zone: zone, Project: project, Status: instance.Status, CreationTime: creationTime})
			}
		}
		if response.NextPageToken == "" {
			break
		} else {
			request.PageToken(response.NextPageToken)
		}
	}
	return instances, nil
}
