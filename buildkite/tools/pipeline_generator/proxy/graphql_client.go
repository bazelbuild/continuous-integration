package proxy

import (
	"context"
	"fmt"
	"log"

	"github.com/machinebox/graphql"
)

const defaultEndpoint = "https://graphql.buildkite.com/v1"

// TODO(fwe): support paging once we have more than 500 pipelines
const pipelineQuery = `
query ($org: ID!){
  organization(slug: $org) {
    pipelines(first: 500) {
      edges {
        node {
          name
          public
          teams(first: 500) {
            edges {
              node {
                team {
                  name
                }
                accessLevel
              }
            }
          }
          schedules {
            edges {
              node {
                env
                enabled
                id
                label
                cronline
                branch
                commit
                message
              }
            }
          }
        }
      }
    }
  }
}
`

type response struct {
	Organization struct {
		Pipelines struct {
			Edges []struct {
				Node struct {
					Name   string `json:"name"`
					Public bool   `json:"public"`
					Teams  struct {
						Edges []struct {
							Node struct {
								Team struct {
									Name string `json:"name"`
								} `json:"team"`
								AccessLevel string `json:"accessLevel"`
							} `json:"node"`
						} `json:"edges"`
					} `json:"teams"`
					Schedules struct {
						Edges []struct {
							Node struct {
								Id       string   `json:"id"`
								Label    string   `json:"label"`
								Cronline string   `json:"cronline"`
								Branch   string   `json:"branch"`
								Commit   string   `json:"commit"`
								Env      []string `json:"env"`
								Enabled  bool     `json:"enabled"`
								Message  string   `json:"message"`
							} `json:"node"`
						} `json:"edges"`
					} `json:"schedules"`
				} `json:"node"`
			} `json:"edges"`
		} `json:"pipelines"`
	} `json:"organization"`
}

type Access struct {
	TeamName    string
	AccessLevel string
}

type Schedule struct {
	Id       string
	Label    string
	Cronline string
	Branch   string
	Commit   string
	Env      []string
	Enabled  bool
	Message  string
}

type PipelineAccessAndSchedules struct {
	Name   string
	Public bool
	Access []Access
	Schedules []Schedule
}

type GraphQlClient struct {
	org           string
	graphqlClient *graphql.Client
	request       *graphql.Request
}

func CreateGraphQlClient(org string, apiToken string, debug bool) *GraphQlClient {
	graphqlClient := graphql.NewClient(defaultEndpoint)
	if debug {
		graphqlClient.Log = func(s string) { log.Println(s) }
	}

	request := graphql.NewRequest(pipelineQuery)
	request.Var("org", org)
	request.Header.Set("Authorization", fmt.Sprintf("Bearer %s", apiToken))

	return &GraphQlClient{org: org, graphqlClient: graphqlClient, request: request}
}

func (client *GraphQlClient) GetAccessAndSchedules() ([]*PipelineAccessAndSchedules, error) {
	ctx := context.Background()
	var resp response
	if err := client.graphqlClient.Run(ctx, client.request, &resp); err != nil {
		return nil, err
	}

	return extractAccessAndSchedulesFromResponse(resp), nil
}

func extractAccessAndSchedulesFromResponse(resp response) []*PipelineAccessAndSchedules {
	edges := resp.Organization.Pipelines.Edges
	result := make([]*PipelineAccessAndSchedules, len(edges))
	for i, e := range edges {
		access := make([]Access, len(e.Node.Teams.Edges))
		for ia, a := range e.Node.Teams.Edges {
			access[ia] = Access{
				TeamName:    a.Node.Team.Name,
				AccessLevel: a.Node.AccessLevel}
		}

		schedules := make([]Schedule, len(e.Node.Schedules.Edges))
		for is, s := range e.Node.Schedules.Edges {
			schedules[is] = Schedule{
				Id:       s.Node.Id,
				Label:    s.Node.Label,
				Cronline: s.Node.Cronline,
				Branch:   s.Node.Branch,
				Commit:   s.Node.Commit,
				Env:      s.Node.Env,
				Enabled:  s.Node.Enabled,
				Message:  s.Node.Message}
		}

		result[i] = &PipelineAccessAndSchedules{
			Name:      e.Node.Name,
			Public:    e.Node.Public,
			Access:    access,
			Schedules: schedules}
	}

	return result
}