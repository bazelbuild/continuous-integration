package config

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"sort"
	"strings"

	"gopkg.in/yaml.v2"

	"github.com/fweikert/continuous-integration/buildkite/tools/pipeline_generator/proxy"
)

type Config struct {
	Pipelines []Pipeline `yaml:"pipelines"`
}

type Pipeline struct {
	Name          string         `yaml:"name"`
	Slug          string         `yaml:"slug"`
	Description   string         `yaml:"description,omitempty"`
	Configuration string         `yaml:"configuration,omitempty"`
	Public        bool           `yaml:"public"`
	Steps         []Step         `yaml:"steps,omitempty"`
	Teams         []TeamAccess   `yaml:"teams,omitempty"`
	Schedules     []Schedule     `yaml:"schedules,omitempty"`
	BuildSkipping *BuildSkipping `yaml:"build_skipping,omitempty"`
	Repository    *Repository    `yaml:"repository,omitempty"`
	Provider      *Provider      `yaml:"provider,omitempty"`
}

type Step struct {
	Name                 string            `yaml:"name"`
	Type                 string            `yaml:"type"`
	Command              string            `yaml:"command,omitempty"`
	Agents               []string          `yaml:"agents,omitempty"`
	Branches             string            `yaml:"branches,omitempty"`
	ArtifactPaths        string            `yaml:"artifact_paths,omitempty"`
	Timeout              int               `yaml:"timeout,omitempty"`
	Concurrency          int               `yaml:"concurrency,omitempty"`
	Parallelism          int               `yaml:"parallelism,omitempty"`
	EnvironmentVariables map[string]string `yaml:"env,omitempty"`
}

type BuildSkipping struct {
	SkipIntermediateBuilds   bool   `yaml:"skip_queued_branch_builds,omitempty"`
	SkipBranches             string `yaml:"skip_queued_branch_builds_filter,omitempty"`
	CancelIntermediateBuilds bool   `yaml:"cancel_running_branch_builds,omitempty"`
	CancelBranches           string `yaml:"cancel_running_branch_builds_filter,omitempty"`
}

type Repository struct {
	RepositoryUrl  string `yaml:"repository,omitempty"`
	DefaultBranch  string `yaml:"default_branch,omitempty"`
	BranchLimiting string `yaml:"branch_limiting,omitempty"`
}

type TeamAccess struct {
	Name        string `yaml:"name"`
	AccessLevel string `yaml:"access_level"`
}

type Schedule struct {
	CronInterval         string   `yaml:"cron_interval,omitempty"`
	Description          string   `yaml:"description,omitempty"`
	BuildMessage         string   `yaml:"build_message,omitempty"`
	Commit               string   `yaml:"commit,omitempty"`
	Branch               string   `yaml:"branch,omitempty"`
	EnvironmentVariables []string `yaml:"env,omitempty"`
	Enabled              bool     `yaml:"enabled"`
}

// TODO(fwe): Get url and name from GraphQL?
type Provider struct {
	WebhookUrl string                 `yaml:"webhook_url"`
	Settings   map[string]interface{} `yaml:"settings"`
}

func ReadConfig(path string) (*Config, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("Failed to open config '%s': %v", path, err)
	}
	defer file.Close()

	content, err := ioutil.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("Failed to read config '%s': %v", path, err)
	}

	c := Config{}
	err = yaml.Unmarshal(content, &c)
	if err != nil {
		return nil, fmt.Errorf("Config '%s' is not valid YAML: %v", path, err)
	}
	c.sortPipelines()
	return &c, nil
}

func ReadFromBuildkite(org, apiToken string, debug bool) (*Config, error) {
	p, err := proxy.CreateProxy(org, apiToken, debug)
	if err != nil {
		log.Fatalf("Cannot connect to Buildkite: %s", err)
	}

	allPipelines, err := p.GetPipelines()
	if err != nil {
		return nil, fmt.Errorf("Cannot retrieve pipelines: %s", err)
	}

	c := Config{make([]Pipeline, len(allPipelines))}
	for ip, pipeline := range allPipelines {
		c.Pipelines[ip] = *convertPipeline(pipeline)
	}
	c.sortPipelines()

	return &c, nil
}

func (config *Config) sortPipelines() {
	sort.Slice(config.Pipelines, func(i, j int) bool { return config.Pipelines[i].Slug < config.Pipelines[j].Slug })
}

func convertPipeline(pipeline *proxy.Pipeline) *Pipeline {
	steps := make([]Step, len(pipeline.Steps))
	for is, step := range pipeline.Steps {
		steps[is] = Step{Name: getStringValue(step.Name),
			Type:                 getStringValue(step.Type),
			Command:              getStringValue(step.Command),
			Agents:               step.AgentQueryRules,
			Branches:             getStringValue(step.BranchConfiguration),
			ArtifactPaths:        getStringValue(step.ArtifactPaths),
			Timeout:              getIntValue(step.TimeoutInMinutes),
			Concurrency:          getIntValue(step.Concurrency),
			Parallelism:          getIntValue(step.Parallelism),
			EnvironmentVariables: step.Env,
		}
	}

	teams := make([]TeamAccess, len(pipeline.Details.Access))
	for i, t := range pipeline.Details.Access {
		teams[i] = TeamAccess{
			Name:        t.TeamName,
			AccessLevel: t.AccessLevel}
	}

	schedules := make([]Schedule, len(pipeline.Details.Schedules))
	for i, s := range pipeline.Details.Schedules {
		schedules[i] = Schedule{
			Description:          s.Label,
			CronInterval:         s.Cronline,
			BuildMessage:         s.Message,
			Commit:               s.Commit,
			Branch:               s.Branch,
			EnvironmentVariables: s.Env,
			Enabled:              s.Enabled}
	}

	repo := Repository{
		RepositoryUrl:  getStringValue(pipeline.Repository),
		DefaultBranch:  getStringValue(pipeline.DefaultBranch),
		BranchLimiting: getStringValue(pipeline.BranchConfiguration)}
	provider := Provider{
		WebhookUrl: getStringValue(pipeline.Provider.WebhookURL),
		Settings:   pipeline.Provider.Settings}
	skip := BuildSkipping{
		SkipIntermediateBuilds:   pipeline.SkipQueuedBranchBuilds,
		SkipBranches:             getStringValue(pipeline.SkipBueuedBranchBuildsFilter),
		CancelIntermediateBuilds: pipeline.CancelRunningBranchBuilds,
		CancelBranches:           getStringValue(pipeline.CancelRunningBranchBuildsFilter)}

	return &Pipeline{Name: getStringValue(pipeline.Name),
		Slug:          getStringValue(pipeline.Slug),
		Description:   getStringValue(pipeline.Description),
		Public:        pipeline.Details.Public,
		Steps:         steps,
		Configuration: getStringValue(pipeline.Configuration),
		Teams:         teams,
		Schedules:     schedules,
		BuildSkipping: &skip,
		Repository:    &repo,
		Provider:      &provider}
}

func getStringValue(ptr *string) string {
	if ptr == nil {
		return ""
	}
	return *ptr
}

func getIntValue(ptr *int) int {
	if ptr == nil {
		return 0
	}
	return *ptr
}

func (config *Config) Yaml(pipelines ...string) (string, error) {
	toExport, err := config.filterPipelines(pipelines)
	if err != nil {
		return "", fmt.Errorf("Cannot filter pipelines: %v", err)
	}

	s, err := yaml.Marshal(toExport)
	if err != nil {
		return "", fmt.Errorf("Cannot convert configuration to YAML: %v", err)
	}
	return string(s), nil
}

func (config *Config) filterPipelines(pipelines []string) ([]Pipeline, error) {
	if len(pipelines) == 0 {
		return config.Pipelines, nil
	}

	filter := make(map[string]bool)
	for _, p := range pipelines {
		filter[p] = false
	}

	result := make([]Pipeline, 0, len(pipelines))
	for _, p := range config.Pipelines {
		if _, ok := filter[p.Slug]; ok {
			result = append(result, p)
			delete(filter, p.Slug)
		}
	}

	if len(filter) > 0 {
		unknown := make([]string, 0, len(filter))
		for key, _ := range filter {
			unknown = append(unknown, key)
		}
		format := func(p []string) string {
			return strings.Join(p, "\n\t- ")
		}

		return nil, fmt.Errorf("Unknown pipelines:\n\t- %s.\nAvailable pipelines:\n\t- %s", format(unknown), format(config.getSlugs()))
	}

	return result, nil
}

func (config *Config) getSlugs() []string {
	return getSlugs(config.Pipelines)
}

func getSlugs(pipelines []Pipeline) []string {
	slugs := make([]string, len(pipelines))
	for i, p := range pipelines {
		slugs[i] = p.Slug
	}
	return slugs
}

func (config *Config) String() string {
	return fmt.Sprintf("Found %d pipelines:\n\t- %s", len(config.Pipelines), strings.Join(config.getSlugs(), "\n\t- "))
}

func (config *Config) Compare(other *Config) (string, error) {
	if other == nil {
		return "", fmt.Errorf("Cannot compare to a nil config.")
	} else if config == other {
		return "", nil
	}

	var c, o int
	var added, missing, same []Pipeline
	for c < len(config.Pipelines) && o < len(other.Pipelines) {
		configPipe := config.Pipelines[c]
		otherPipe := other.Pipelines[o]

		log.Print(configPipe)

		if configPipe.Slug < otherPipe.Slug {
			added = append(added, configPipe)
			c += 1
		} else if configPipe.Slug == otherPipe.Slug {
			same = append(same, configPipe)
			c += 1
			o += 1
		} else {
			missing = append(missing, otherPipe)
			o += 1
		}
	}

	formatter := func(pipelines []Pipeline) string { return strings.Join(getSlugs(pipelines), ", ") }

	// TODO(fweikert): actually print added, missing and same.
	result := fmt.Sprintf("Additional pipelines: %s\nMissing pipelines: %s\nSame pipelines: %s\n", formatter(added), formatter(missing), formatter(same))
	return result, nil
}
