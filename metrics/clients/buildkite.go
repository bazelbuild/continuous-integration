package clients

import (
	"fmt"

	"github.com/fweikert/go-buildkite/buildkite"
)

type BuildkiteClient struct {
	org    string
	client *buildkite.Client
}

func CreateBuildkiteClient(org string, apiToken string, debug bool) (*BuildkiteClient, error) {
	tokenConfig, err := buildkite.NewTokenConfig(apiToken, debug)

	if err != nil {
		return nil, fmt.Errorf("Could not create Buildkite config: %v", err)
	}

	client := buildkite.NewClient(tokenConfig.Client())
	return &BuildkiteClient{org: org, client: client}, nil
}

func (client *BuildkiteClient) GetMostRecentJobs(pipeline string) ([]interface{}, error) {
	return nil, nil
}

func (client *BuildkiteClient) GetAgents() ([]interface{}, error) {
	return nil, nil
}
