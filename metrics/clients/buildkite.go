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

func (client *BuildkiteClient) GetMostRecentBuilds(pipeline string, atLeastNBuilds int) ([]buildkite.Build, error) {
	all_builds := make([]buildkite.Build, 0)
	opt := buildkite.BuildsListOptions{ListOptions: buildkite.ListOptions{Page: 1, PerPage: 100}}
	currPage := 1
	lastPage := 1

	for currPage <= lastPage {
		fmt.Printf("GET %d of %d", currPage, lastPage)
		builds, response, err := client.client.Builds.ListByPipeline(client.org, pipeline, &opt)
		if err != nil {
			return nil, fmt.Errorf("Could not get page %d of builds for pipeline %s: %v", currPage, pipeline, err)
		}

		all_builds = append(all_builds, builds...)
		currPage += 1
		opt.Page = currPage
		lastPage = response.LastPage

		if atLeastNBuilds > -1 && len(all_builds) >= atLeastNBuilds {
			break
		}
	}

	return all_builds, nil
}

func (client *BuildkiteClient) GetAgents() ([]buildkite.Agent, error) {
	all_agents := make([]buildkite.Agent, 0)
	opt := buildkite.AgentListOptions{ListOptions: buildkite.ListOptions{Page: 1, PerPage: 100}}
	currPage := 1
	lastPage := 1

	for currPage <= lastPage {
		agents, response, err := client.client.Agents.List(client.org, &opt)
		if err != nil {
			return nil, fmt.Errorf("Could not get page %d of agents: %v", currPage, err)
		}

		all_agents = append(all_agents, agents...)
		currPage += 1
		opt.Page = currPage
		lastPage = response.LastPage
	}

	return all_agents, nil
}
