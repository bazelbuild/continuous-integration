package metrics

import (
	"strings"

	"github.com/fweikert/go-buildkite/buildkite"
)

func getPlatfrom(jobName *string) string {
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
	return end.Time.Sub(start.Time).Seconds()
}
