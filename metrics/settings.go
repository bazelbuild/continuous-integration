package main

import (
	"context"
	"fmt"

	"cloud.google.com/go/datastore"
)

const settingsName = ""

type Settings struct {
	BuildkiteOrg       string
	BuildkiteApiToken  string
	BuildkiteDebug     bool
	BuildkitePipelines []string
	GitHubOrg          string
	GitHubRepo         string
	GitHubApiToken     string
	CloudSqlUser       string
	CloudSqlPassword   string
	CloudSqlInstance   string
	CloudSqlDatabase   string
	CloudSqlLocalPort  int
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
		return nil, fmt.Errorf("Could not list Datastore entities with name %s in project %s: %v", settingsName, projectID, err)
	}
	if len(settings) != 1 {
		return nil, fmt.Errorf("Expected exactly one Datastore entry with name %s in project %s, but got %d.", settingsName, projectID, len(settings))
	}
	return settings[0], nil
}
