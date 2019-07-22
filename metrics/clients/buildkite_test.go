package clients

import (
	"fmt"
	"testing"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/data"
	"github.com/buildkite/go-buildkite/buildkite"
)

func TestAgentCacheExpiration(t *testing.T) {
	expectedAgents := createAgents(20)
	api, client, clock := setUp(expectedAgents, nil, time.Duration(10)*time.Second)

	check := func(agents []buildkite.Agent) {
		if len(agents) != len(expectedAgents) {
			t.Errorf("Incorrect number of agents: want %d, got %d", len(expectedAgents), len(agents))
		}
	}

	actualAgents, _ := client.GetAgents("org")
	check(actualAgents)

	clock.AdvanceSeconds(9)
	actualAgents, _ = client.GetAgents("org")
	check(actualAgents)

	if api.agentRequests > 1 {
		t.Error("Response should have been cached, but an API call was made instead")
	}

	clock.AdvanceSeconds(1)
	actualAgents, _ = client.GetAgents("org")
	check(actualAgents)

	if api.agentRequests > 1 {
		t.Error("Response should have been cached, but an API call was made instead")
	}

	clock.AdvanceSeconds(1)
	actualAgents, _ = client.GetAgents("org")
	check(actualAgents)

	if api.agentRequests != 2 {
		t.Error("Expected a second API call due to cache expiration")
	}
}

func TestBuildCacheExpiration(t *testing.T) {
	expectedBuilds := createBuilds(10)
	api, client, clock := setUp(nil, expectedBuilds, time.Duration(10)*time.Second)

	check := func(builds []buildkite.Build) {
		if len(builds) != len(expectedBuilds) {
			t.Errorf("Incorrect number of builds: want %d, got %d", len(expectedBuilds), len(builds))
		}
	}

	pid := data.PipelineID{Org: "org", Slug: "pipe"}
	actualBuilds, _ := client.GetMostRecentBuilds(&pid, 10)
	check(actualBuilds)

	clock.AdvanceSeconds(9)
	actualBuilds, _ = client.GetMostRecentBuilds(&pid, 10)
	check(actualBuilds)

	if api.buildRequests > 1 {
		t.Error("Response should have been cached, but an API call was made instead")
	}

	clock.AdvanceSeconds(1)
	actualBuilds, _ = client.GetMostRecentBuilds(&pid, 10)
	check(actualBuilds)

	if api.buildRequests > 1 {
		t.Error("Response should have been cached, but an API call was made instead")
	}

	clock.AdvanceSeconds(1)
	actualBuilds, _ = client.GetMostRecentBuilds(&pid, 10)
	check(actualBuilds)

	if api.buildRequests != 2 {
		t.Error("Expected a second API call due to cache expiration")
	}
}

func TestBuildCacheWithDifferentLastNArguments(t *testing.T) {
	expectedBuilds := createBuilds(10)
	api, client, clock := setUp(nil, expectedBuilds, time.Duration(10)*time.Second)

	check := func(builds []buildkite.Build, expectedCount int) {
		if len(builds) != expectedCount {
			t.Errorf("Incorrect number of builds: want %d, got %d", expectedCount, len(builds))
		}
	}

	pid := data.PipelineID{Org: "org", Slug: "pipe"}
	actualBuilds, _ := client.GetMostRecentBuilds(&pid, 10)
	check(actualBuilds, len(expectedBuilds))

	clock.AdvanceSeconds(1)
	subsetCount := 5
	actualBuilds, _ = client.GetMostRecentBuilds(&pid, subsetCount)
	check(actualBuilds, subsetCount)

	if api.buildRequests > 1 {
		t.Error("Response should have been cached, but an API call was made instead")
	}

	for _, build := range actualBuilds {
		if *build.Number < 0 || subsetCount <= *build.Number {
			t.Errorf("Response should have contained first %d builds with numbers in range [0; %d], but we got a build with number %d", subsetCount, subsetCount, *build.Number)
		}
	}
}

func TestBuildCacheMissDueToTooSmallCache(t *testing.T) {
	expectedBuilds := createBuilds(10)
	api, client, clock := setUp(nil, expectedBuilds, time.Duration(10)*time.Second)

	lastN := 10
	pid := data.PipelineID{Org: "org", Slug: "pipe"}
	client.GetMostRecentBuilds(&pid, lastN)

	clock.AdvanceSeconds(1)
	client.GetMostRecentBuilds(&pid, lastN+1)

	if api.buildRequests != 2 {
		t.Errorf("Expected 2 API calls since the second lastN value was greater than the previous one, but got %d", api.buildRequests)
	}
}

func createAgents(count int) []buildkite.Agent {
	agents := make([]buildkite.Agent, count)
	for i := 0; i < count; i += 1 {
		name := fmt.Sprintf("Agent_%d", i)
		agents[i] = buildkite.Agent{Name: &name}
	}
	return agents
}

func createBuilds(count int) []buildkite.Build {
	builds := make([]buildkite.Build, count)
	for i := 0; i < count; i += 1 {
		j := i
		builds[i] = buildkite.Build{Number: &j}
	}
	return builds
}

func setUp(agents []buildkite.Agent, builds []buildkite.Build, cacheTimeout time.Duration) (*fakeBuildkiteAPIClient, *CachedBuildkiteClient, *fakeClock) {
	api := &fakeBuildkiteAPIClient{agents: agents, builds: builds}
	client := CreateCachedBuildkiteClient(api, cacheTimeout)
	clock := &fakeClock{Time: time.Now()}
	client.setClock(clock)
	return api, client, clock
}

type fakeClock struct {
	time.Time
}

func (fc *fakeClock) CurrentTime() time.Time {
	return fc.Time
}

func (fc *fakeClock) AdvanceSeconds(seconds int) {
	fc.Time = fc.Time.Add(time.Duration(seconds) * time.Second)
}

type fakeBuildkiteAPIClient struct {
	agents        []buildkite.Agent
	builds        []buildkite.Build
	agentRequests int
	buildRequests int
}

func (fc *fakeBuildkiteAPIClient) ListAgents(org string, page, perPage int) ([]buildkite.Agent, int, error) {
	fc.agentRequests += 1
	return fc.agents, 1, nil
}

func (fc *fakeBuildkiteAPIClient) ListBuildyByOrg(org string, page, perPage int) ([]buildkite.Build, int, error) {
	fc.buildRequests += 1
	return fc.builds, 1, nil
}

func (fc *fakeBuildkiteAPIClient) ListBuildsByPipeline(org, pipeline string, page, perPage int) ([]buildkite.Build, int, error) {
	fc.buildRequests += 1
	return fc.builds, 1, nil
}
