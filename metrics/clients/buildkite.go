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
	var listFunc func(opt *buildkite.BuildsListOptions) ([]buildkite.Build, *buildkite.Response, error)
	if pipeline == "all" {
		listFunc = func(opt *buildkite.BuildsListOptions) ([]buildkite.Build, *buildkite.Response, error) {
			return client.client.Builds.ListByOrg(client.org, opt)
		}
	} else {
		listFunc = func(opt *buildkite.BuildsListOptions) ([]buildkite.Build, *buildkite.Response, error) {
			return client.client.Builds.ListByPipeline(client.org, pipeline, opt)
		}
	}

	wrapperFunc := func(opt buildkite.ListOptions) ([]interface{}, *buildkite.Response, error) {
		buildOpt := buildkite.BuildsListOptions{ListOptions: opt}
		builds, response, err := listFunc(&buildOpt)
		interfaces := make([]interface{}, len(builds))
		for i, b := range builds {
			interfaces[i] = b
		}
		return interfaces, response, err
	}

	results, err := client.getResults(wrapperFunc, atLeastNBuilds)
	if err != nil {
		return nil, fmt.Errorf("Failed to retrieve builds for pipeline %s: %v", pipeline, err)
	}

	builds := make([]buildkite.Build, len(results))
	for i, r := range results {
		builds[i] = r.(buildkite.Build)
	}
	return builds, nil
}

func (client *BuildkiteClient) GetAgents() ([]buildkite.Agent, error) {
	list := func(opt buildkite.ListOptions) ([]interface{}, *buildkite.Response, error) {
		agentOpt := buildkite.AgentListOptions{ListOptions: opt}
		agents, response, err := client.client.Agents.List(client.org, &agentOpt)
		interfaces := make([]interface{}, len(agents))
		for i, a := range agents {
			interfaces[i] = a
		}
		return interfaces, response, err
	}

	results, err := client.getResults(list, -1)
	if err != nil {
		return nil, fmt.Errorf("Failed to retrieve agents: %v", err)
	}

	agents := make([]buildkite.Agent, len(results))
	for i, r := range results {
		agents[i] = r.(buildkite.Agent)
	}
	return agents, nil
}

func (client *BuildkiteClient) getResults(listFunc func(opt buildkite.ListOptions) ([]interface{}, *buildkite.Response, error), minResults int) ([]interface{}, error) {
	all_results := make([]interface{}, 0)
	opt := buildkite.ListOptions{Page: 1, PerPage: 100}
	currPage := 1
	lastPage := 1

	for currPage <= lastPage {
		results, response, err := listFunc(opt)
		if err != nil {
			return nil, fmt.Errorf("Could not get page %d: %v", currPage, err)
		}

		all_results = append(all_results, results...)
		currPage += 1
		opt.Page = currPage
		lastPage = response.LastPage

		if minResults > -1 && len(all_results) >= minResults {
			break
		}
	}

	return all_results, nil
}
