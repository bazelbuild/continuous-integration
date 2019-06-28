package metrics

import (
	"log"
	"strings"

	"github.com/fweikert/go-buildkite/buildkite"
)

func getPlatform(job *buildkite.Job) string {
	platform := getPlatformFromJobName(job.Name)
	if platform == "" {
		platform = getPlatformFromAgentQueryRules(job.AgentQueryRules)
	}
	return platform
}

func getPlatformFromAgentQueryRules(rules []string) string {
	for _, r := range rules {
		parts := strings.Split(r, "=")
		if len(parts) == 2 && parts[0] == "queue" {
			if parts[1] == "default" {
				return "linux"
			} else {
				return parts[1]
			}
		}
	}
	return ""
}

func getPlatformFromJobName(jobName *string) string {
	if jobName == nil {
		return ""
	} else if strings.Contains(*jobName, "ubuntu") {
		return "linux"
	} else if strings.Contains(*jobName, "windows") {
		return "windows"
	} else if strings.Contains(*jobName, "darwin") {
		return "macos"
	} else if strings.Contains(*jobName, "gcloud") {
		return "rbe"
	} else {
		return ""
	}
}

func getDifferenceSeconds(start *buildkite.Timestamp, end *buildkite.Timestamp) float64 {
	if start == nil || end == nil {
		return -1
	}
	seconds := end.Time.Sub(start.Time).Seconds()
	if seconds < 0 {
		if seconds > -1 {
			// Some timestamps don't include milliseconds, which is probably a bug in the Buildkite API.
			// For now we ignore any differences that are smaller than a second.
			return 0
		}
		log.Fatalf("TIME ERROR: start %v is later than end %v: %v\n", start, end, seconds)
	}
	return seconds
}
