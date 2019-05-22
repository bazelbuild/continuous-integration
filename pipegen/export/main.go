package main

import (
	"flag"
	"fmt"
	"log"
	"strings"

	"github.com/bazelbuild/continuous-integration/pipegen/config"
)

var (
	apiToken  = flag.String("token", "", "Buildkite API access token that grants access to the GraphQL API. See https://buildkite.com/docs/apis/rest-api#authentication")
	org       = flag.String("org", "bazel", "Buildkite orginization slug")
	debug     = flag.Bool("debug", false, "Enable debugging")
	pipelines = flag.String("pipelines", "", "Comma separated list of pipeline slugs that should be exported. If empty (default), all pipelines will be exported.")
)

func main() {
	flag.Parse()

	c, err := config.ReadFromBuildkite(*org, *apiToken, *debug)
	if err != nil {
		log.Fatalf("Cannot retrieve configuration from Buildkite: %s", err)
	}

	filter := []string{}
	if *pipelines != "" {
		filter = strings.Split(*pipelines, ",")
	}

	yaml, err := c.Yaml(filter...)
	if err != nil {
		log.Fatalf("Could not export configurationm: %v", err)
	}
	fmt.Println(yaml)
}
