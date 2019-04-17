package main

import (
	"flag"
	"fmt"
	"log"

	"github.com/fweikert/continuous-integration/buildkite/tools/pipeline_generator/config"
)

var (
	apiToken   = flag.String("token", "", "Buildkite API access token that has 'read pipelines' privileges. See https://buildkite.com/docs/apis/rest-api#authentication")
	org        = flag.String("org", "bazel", "Buildkite orginization slug")
	debug      = flag.Bool("debug", false, "Enable debugging")
	configPath = flag.String("config", "", "Location to read the pipeline configuration from.")
)

func main() {
	flag.Parse()

	fileConfig, err := config.ReadConfig(*configPath)
	if err != nil {
		log.Fatalf("Failed to retrieve config: %s", err)
	}

	deployedConfig, err := config.ReadFromBuildkite(*org, *apiToken, *debug)
	if err != nil {
		log.Fatalf("Cannot retrieve configuration from Buildkite: %s", err)
	}

	result, err := fileConfig.Compare(deployedConfig)
	if err != nil {
		fmt.Printf("Cannot compare configurations: %v", err)
	}
	fmt.Println(result)
}
