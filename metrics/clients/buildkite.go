package clients

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/fweikert/continuous-integration/metrics/data"

	"github.com/fweikert/go-buildkite/buildkite"
)

type BuildkiteClient interface {
	GetMostRecentBuilds(*data.PipelineID, int) ([]buildkite.Build, error)
	GetAgents(string) ([]buildkite.Agent, error)
}

type cacheEntry struct {
	sampled time.Time
	values  []interface{}
}

type SimpleBuildkiteClient struct {
	client *buildkite.Client

	mu           sync.Mutex
	cacheTimeout time.Duration
	agentCache   map[string]cacheEntry
	buildCache   map[string]cacheEntry
}

func CreateBuildkiteClient(apiToken string, debug bool, cacheTimeout time.Duration) (BuildkiteClient, error) {
	tokenConfig, err := buildkite.NewTokenConfig(apiToken, debug)
	if err != nil {
		return nil, fmt.Errorf("Could not create Buildkite config: %v", err)
	}
	return &SimpleBuildkiteClient{
			client:       buildkite.NewClient(tokenConfig.Client()),
			cacheTimeout: cacheTimeout,
			agentCache:   make(map[string]cacheEntry),
			buildCache:   make(map[string]cacheEntry),
		},
		nil
}

func (client *SimpleBuildkiteClient) GetMostRecentBuilds(pipeline *data.PipelineID, atLeastNBuilds int) ([]buildkite.Build, error) {
	var listFunc func(opt *buildkite.BuildsListOptions) ([]buildkite.Build, *buildkite.Response, error)
	if pipeline.Slug == "all" {
		listFunc = func(opt *buildkite.BuildsListOptions) ([]buildkite.Build, *buildkite.Response, error) {
			return client.client.Builds.ListByOrg(pipeline.Org, opt)
		}
	} else {
		listFunc = func(opt *buildkite.BuildsListOptions) ([]buildkite.Build, *buildkite.Response, error) {
			return client.client.Builds.ListByPipeline(pipeline.Org, pipeline.Slug, opt)
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

	results, err := client.getResults(wrapperFunc, atLeastNBuilds, client.buildCache, pipeline.String())
	if err != nil {
		return nil, fmt.Errorf("Failed to retrieve builds for pipeline %s: %v", pipeline, err)
	}

	builds := make([]buildkite.Build, len(results))
	for i, r := range results {
		builds[i] = r.(buildkite.Build)
	}
	return builds, nil
}

func (client *SimpleBuildkiteClient) GetAgents(org string) ([]buildkite.Agent, error) {
	list := func(opt buildkite.ListOptions) ([]interface{}, *buildkite.Response, error) {
		agentOpt := buildkite.AgentListOptions{ListOptions: opt}
		agents, response, err := client.client.Agents.List(org, &agentOpt)
		interfaces := make([]interface{}, len(agents))
		for i, a := range agents {
			interfaces[i] = a
		}
		return interfaces, response, err
	}

	results, err := client.getResults(list, -1, client.agentCache, org)
	if err != nil {
		return nil, fmt.Errorf("Failed to retrieve agents: %v", err)
	}

	agents := make([]buildkite.Agent, len(results))
	for i, r := range results {
		agents[i] = r.(buildkite.Agent)
	}
	return agents, nil
}

func (client *SimpleBuildkiteClient) getResults(listFunc func(opt buildkite.ListOptions) ([]interface{}, *buildkite.Response, error), lastN int, cache map[string]cacheEntry, cacheKey string) ([]interface{}, error) {
	client.mu.Lock()
	defer client.mu.Unlock()
	if entry, ok := cache[cacheKey]; ok {
		if time.Since(entry.sampled) <= client.cacheTimeout && len(entry.values) >= lastN {
			return entry.values[:lastN], nil
		}
		delete(cache, cacheKey)
	}

	results, err := client.getUncachedResults(listFunc, lastN, cacheKey)
	if err != nil {
		return nil, err
	}
	cache[cacheKey] = cacheEntry{
		values:  results,
		sampled: time.Now(),
	}
	return results, nil
}

func (client *SimpleBuildkiteClient) getUncachedResults(listFunc func(opt buildkite.ListOptions) ([]interface{}, *buildkite.Response, error), lastN int, cacheKey string) ([]interface{}, error) {
	all_results := make([]interface{}, 0)
	perPage := 100
	if 0 < lastN && lastN < perPage {
		perPage = lastN
	}
	opt := buildkite.ListOptions{Page: 1, PerPage: perPage}
	currPage := 1
	lastPage := 1

	for currPage <= lastPage {
		log.Printf("Buildkite: Fetching page %d for '%s' (last=%d).\n", currPage, cacheKey, lastPage)
		results, response, err := listFunc(opt)
		if err != nil {
			return nil, fmt.Errorf("Could not get page %d: %v", currPage, err)
		}

		all_results = append(all_results, results...)
		currPage += 1
		opt.Page = currPage
		lastPage = response.LastPage

		if lastN > -1 && len(all_results) >= lastN {
			break
		}
	}

	if 0 < lastN && lastN < len(all_results) {
		all_results = all_results[:lastN]
	}

	return all_results, nil
}
