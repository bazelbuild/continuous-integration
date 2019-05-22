package proxy

import (
	"fmt"

	"github.com/fweikert/go-buildkite/buildkite"
)

type RestClient struct {
	org    string
	client *buildkite.Client
}

func CreateRestClient(org string, apiToken string, debug bool) (*RestClient, error) {
	tokenConfig, err := buildkite.NewTokenConfig(apiToken, debug)

	if err != nil {
		return nil, fmt.Errorf("Could not createa Buildkite config: %v", err)
	}

	client := buildkite.NewClient(tokenConfig.Client())
	return &RestClient{org: org, client: client}, nil
}

func (client *RestClient) GetBasicSettings() ([]buildkite.Pipeline, error) {
	all_pipelines := make([]buildkite.Pipeline, 0)
	opt := buildkite.PipelineListOptions{ListOptions: buildkite.ListOptions{Page: 1, PerPage: 100}}
	currPage := 1
	lastPage := 1

	for currPage <= lastPage {
		pipelines, response, err := client.client.Pipelines.List(client.org, &opt)
		if err != nil {
			return nil, fmt.Errorf("Could not get page %d of pipelines: %v", currPage, err)
		}

		all_pipelines = append(all_pipelines, pipelines...)
		currPage += 1
		opt.Page = currPage
		lastPage = response.LastPage
	}

	return all_pipelines, nil
}
