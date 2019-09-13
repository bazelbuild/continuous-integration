package main

import (
	"context"
	"fmt"
	"log"

	"cloud.google.com/go/datastore"
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

const settingsName = ""

type Settings struct {
	BuildkiteOrgs                []string
	BuildkiteApiToken            string
	BuildkiteDebug               bool
	BuildkitePipelines           []string // TODO: make this field private
	BuildkiteCacheTimeoutMinutes int
	GitHubOrg                    string
	GitHubRepo                   string
	GitHubApiToken               string
	CloudSqlUser                 string
	CloudSqlPassword             string
	CloudSqlInstance             string
	CloudSqlDatabase             string
	CloudSqlLocalPort            int
	CloudProjects                []string
}

func ReadSettingsFromDatastore(projectID, settingsName string) (*Settings, error) {
	ctx := context.Background()
	client, err := datastore.NewClient(ctx, projectID)
	if err != nil {
		return nil, fmt.Errorf("Could not connect to Datastore of project %s: %v", projectID, err)
	}

	settings := make([]*Settings, 0)
	q := datastore.NewQuery(settingsName)

	_, err = client.GetAll(ctx, q, &settings)
	if err != nil {
		if efm, ok := err.(*datastore.ErrFieldMismatch); ok {
			log.Printf("Datastore: ignoring unexpected field '%s'\n", efm.FieldName)
		} else {
			return nil, fmt.Errorf("Could not list Datastore entities with name %s in project %s: %v", settingsName, projectID, err)
		}
	}
	if len(settings) != 1 {
		return nil, fmt.Errorf("Expected exactly one Datastore entry with name %s in project %s, but got %d.", settingsName, projectID, len(settings))
	}
	return settings[0], nil
}

func (s *Settings) GetPipelineIDs() ([]*data.PipelineID, error) {
	result := make([]*data.PipelineID, len(s.BuildkitePipelines))
	for i, v := range s.BuildkitePipelines {
		p, err := data.CreatePipelineID(v)
		if err != nil {
			return nil, err
		}
		result[i] = p
	}
	return result, nil
}
