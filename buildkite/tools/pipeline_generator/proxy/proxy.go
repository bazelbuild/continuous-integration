package proxy

import (
	"fmt"

	"github.com/fweikert/go-buildkite/buildkite"
)

type Pipeline struct {
	*buildkite.Pipeline
	Details *PipelineAccessAndSchedules
}

type Proxy struct {
	org           string
	apiToken      string
	restClient    *RestClient
	graphQlClient *GraphQlClient
}

func CreateProxy(org, apiToken string, debug bool) (*Proxy, error) {
	restClient, err := CreateRestClient(org, apiToken, debug)

	if err != nil {
		return nil, fmt.Errorf("Cannot get client config: %s", err)
	}

	graphqlClient := CreateGraphQlClient(org, apiToken, debug)
	return &Proxy{org: org, restClient: restClient, graphQlClient: graphqlClient}, nil
}

func (proxy *Proxy) GetPipelines() ([]*Pipeline, error) {
	basicSettings, err := proxy.restClient.GetBasicSettings()
	if err != nil {
		return nil, fmt.Errorf("Cannot retrieve pipelines for org '%s' from the REST API: %s", proxy.org, err)
	}

	accessAndSchedules, err := proxy.graphQlClient.GetAccessAndSchedules()
	if err != nil {
		return nil, fmt.Errorf("Cannot retrieve pipelines for org '%s' from the GraphQL API: %s", proxy.org, err)
	}

	return proxy.mergeData(basicSettings, accessAndSchedules)
}

func (proxy *Proxy) mergeData(basicSettings []buildkite.Pipeline, accessAndSchedules []*PipelineAccessAndSchedules) ([]*Pipeline, error) {
	restCount := len(basicSettings)
	graphQlCount := len(accessAndSchedules)
	if restCount != graphQlCount {
		return nil, fmt.Errorf("Buildkite API returned %d pipelines for org '%s', but the GraphQL API returned %d.", restCount, proxy.org, graphQlCount)
	}

	index := make(map[string]*buildkite.Pipeline)
	for i, bs := range basicSettings {
		index[*bs.Name] = &basicSettings[i]
	}

	mergedData := make([]*Pipeline, restCount)
	for i, aas := range accessAndSchedules {
		if bs, ok := index[aas.Name]; !ok {
			return nil, fmt.Errorf("GraphQL API returned pipeline '%s', which was not returned by the REST API.", aas.Name)
		} else {
			mergedData[i] = &Pipeline{bs, aas}
		}
	}

	return mergedData, nil
}
