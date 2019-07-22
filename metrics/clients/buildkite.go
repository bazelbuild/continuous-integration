package clients

import (
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/data"
	"github.com/buildkite/go-buildkite/buildkite"
)

type BuildkiteClient interface {
	GetMostRecentBuilds(*data.PipelineID, int) ([]buildkite.Build, error)
	GetAgents(string) ([]buildkite.Agent, error)
}

type cacheEntry struct {
	sampled time.Time
	values  []interface{}
}

type Clock interface {
	CurrentTime() time.Time
}

type DefaultClock struct{}

func (DefaultClock) CurrentTime() time.Time {
	return time.Now()
}

type CachedBuildkiteClient struct {
	api BuildkiteAPI

	mu           sync.Mutex
	cacheTimeout time.Duration
	agentCache   map[string]cacheEntry
	buildCache   map[string]cacheEntry
	clock        Clock
}

func CreateCachedBuildkiteClient(api BuildkiteAPI, cacheTimeout time.Duration) *CachedBuildkiteClient {
	return &CachedBuildkiteClient{
		api:          api,
		cacheTimeout: cacheTimeout,
		agentCache:   make(map[string]cacheEntry),
		buildCache:   make(map[string]cacheEntry),
		clock:        DefaultClock{},
	}
}

func (client *CachedBuildkiteClient) GetMostRecentBuilds(pipeline *data.PipelineID, atLeastNBuilds int) ([]buildkite.Build, error) {
	var listFunc func(int, int) ([]buildkite.Build, int, error)
	if pipeline.Slug == "all" {
		listFunc = func(page, perPage int) ([]buildkite.Build, int, error) {
			return client.api.ListBuildyByOrg(pipeline.Org, page, perPage)
		}
	} else {
		listFunc = func(page, perPage int) ([]buildkite.Build, int, error) {
			return client.api.ListBuildsByPipeline(pipeline.Org, pipeline.Slug, page, perPage)
		}
	}

	wrapperFunc := func(page, perPage int) ([]interface{}, int, error) {
		builds, lastPage, err := listFunc(page, perPage)
		interfaces := make([]interface{}, len(builds))
		for i, b := range builds {
			interfaces[i] = b
		}
		return interfaces, lastPage, err
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

func (client *CachedBuildkiteClient) GetAgents(org string) ([]buildkite.Agent, error) {
	list := func(page, perPage int) ([]interface{}, int, error) {
		agents, lastPage, err := client.api.ListAgents(org, page, perPage)
		interfaces := make([]interface{}, len(agents))
		for i, a := range agents {
			interfaces[i] = a
		}
		return interfaces, lastPage, err
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

func (client *CachedBuildkiteClient) getResults(listFunc func(int, int) ([]interface{}, int, error), lastN int, cache map[string]cacheEntry, cacheKey string) ([]interface{}, error) {
	client.mu.Lock()
	defer client.mu.Unlock()
	if entry, ok := cache[cacheKey]; ok {
		if client.clock.CurrentTime().Sub(entry.sampled) <= client.cacheTimeout {
			if lastN < 0 {
				return entry.values[:], nil
			} else if lastN <= len(entry.values) {
				return entry.values[:lastN], nil
			}
		}
		delete(cache, cacheKey)
	}

	results, err := client.getUncachedResults(listFunc, lastN, cacheKey)
	if err != nil {
		return nil, err
	}
	cache[cacheKey] = cacheEntry{
		values:  results,
		sampled: client.clock.CurrentTime(),
	}
	return results, nil
}

func (client *CachedBuildkiteClient) getUncachedResults(listFunc func(int, int) ([]interface{}, int, error), lastN int, cacheKey string) ([]interface{}, error) {
	all_results := make([]interface{}, 0)
	perPage := 100
	if 0 < lastN && lastN < perPage {
		perPage = lastN
	}
	currPage := 1
	lastPage := 1

	for currPage <= lastPage {
		log.Printf("Buildkite: Fetching page %d for '%s' (last=%d).\n", currPage, cacheKey, lastPage)
		var results []interface{}
		var err error
		results, lastPage, err = listFunc(currPage, perPage)
		if err != nil {
			return nil, fmt.Errorf("Could not get page %d: %v", currPage, err)
		}

		all_results = append(all_results, results...)
		currPage += 1

		if lastN > -1 && len(all_results) >= lastN {
			break
		}
	}

	if 0 < lastN && lastN < len(all_results) {
		all_results = all_results[:lastN]
	}

	return all_results, nil
}

func (client *CachedBuildkiteClient) setClock(clock Clock) {
	client.clock = clock
}
