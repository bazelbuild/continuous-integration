package clients

import (
	"fmt"

	"github.com/buildkite/go-buildkite/buildkite"
)

type BuildkiteAPI interface {
	ListAgents(org string, page, perPage int) ([]buildkite.Agent, int, error)
	ListBuildyByOrg(org string, page, perPage int) ([]buildkite.Build, int, error)
	ListBuildsByPipeline(org, pipeline string, page, perPage int) ([]buildkite.Build, int, error)
}

type BuildkiteAPIWrapper struct {
	client *buildkite.Client
}

func CreateBuildkiteAPI(apiToken string, debug bool) (BuildkiteAPI, error) {
	tokenConfig, err := buildkite.NewTokenConfig(apiToken, debug)
	if err != nil {
		return nil, fmt.Errorf("Could not create Buildkite config: %v", err)
	}
	return &BuildkiteAPIWrapper{
			client: buildkite.NewClient(tokenConfig.Client()),
		},
		nil
}

func (bk *BuildkiteAPIWrapper) ListAgents(org string, page, perPage int) ([]buildkite.Agent, int, error) {
	opt := buildkite.AgentListOptions{ListOptions: buildkite.ListOptions{Page: page, PerPage: perPage}}
	agents, response, err := bk.client.Agents.List(org, &opt)
	return agents, getLastPage(response), err
}

func (bk *BuildkiteAPIWrapper) ListBuildyByOrg(org string, page, perPage int) ([]buildkite.Build, int, error) {
	opt := buildkite.BuildsListOptions{ListOptions: buildkite.ListOptions{Page: page, PerPage: perPage}}
	builds, response, err := bk.client.Builds.ListByOrg(org, &opt)
	return builds, getLastPage(response), err
}

func (bk *BuildkiteAPIWrapper) ListBuildsByPipeline(org, pipeline string, page, perPage int) ([]buildkite.Build, int, error) {
	opt := buildkite.BuildsListOptions{ListOptions: buildkite.ListOptions{Page: page, PerPage: perPage}}
	builds, response, err := bk.client.Builds.ListByPipeline(org, pipeline, &opt)
	return builds, getLastPage(response), err
}

func getLastPage(response *buildkite.Response) int {
	if response == nil {
		return 0
	}
	return response.LastPage
}
