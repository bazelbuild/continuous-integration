package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/philwo/go-buildkite/buildkite"
)

var (
	apiToken   = flag.String("token", os.Getenv("BUILDKITE_API_TOKEN"), "Buildkite API token with read_agents permission (you can also set this via the BUILDKITE_API_TOKEN environment variable)")
	orgName    = flag.String("organization", os.Getenv("BUILDKITE_ORG"), "Buildkite organization that this agent belongs to (you can also set this via the BUILDKITE_ORG environment variable)")
	listenAddr = flag.String("listen", ":8080", "which address and port to listen on")
)

func main() {
	flag.Parse()

	if *apiToken == "" || *orgName == "" {
		flag.PrintDefaults()
		os.Exit(1)
	}

	config, err := buildkite.NewTokenConfig(*apiToken, false)
	if err != nil {
		log.Fatalf("client config failed: %s", err)
	}

	client := buildkite.NewClient(config.Client())

	hostname, err := os.Hostname()
	if err != nil {
		log.Fatalf("could not get hostname: %s", err)
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		agents, _, err := client.Agents.List(*orgName, &buildkite.AgentListOptions{Hostname: hostname})
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "ERROR: could not get agent list: %s", err)
			return
		}

		if len(agents) > 0 {
			fmt.Fprintf(w, "OK")
		} else {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, "ERROR: agent offline?")
		}
	})

	http.ListenAndServe(*listenAddr, nil)
}
