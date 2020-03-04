package metrics

import (
	"fmt"
	"log"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"github.com/buildkite/go-buildkite/buildkite"
)

func getPlatform(job *buildkite.Job) string {
	platform := getPlatformFromJobName(job.Name)
	if platform == "" {
		platform = getPlatformFromAgentQueryRules(job.AgentQueryRules)
	}
	return platform
}

var shardRE = regexp.MustCompile(`\(shard (\d+)\)$`)

func getShardFromJobName(job string) int {
	groups := shardRE.FindStringSubmatch(job)
	if groups == nil {
		return 0
	}

	// Should not fail due to \d
	shard, _ := strconv.Atoi(groups[1])
	return shard
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

func isFinishedWorkerTask(job *buildkite.Job) bool {
	// Name == nil -> "wait" step
	// StartedAt == nil -> step was cancelled while waiting for an agent
	// FinishedAt == nil -> step is still running
	return job != nil && job.Name != nil && job.RunnableAt != nil && job.FinishedAt != nil
}

const skipTasksEnvVar = "CI_SKIP_TASKS"

func getSkippedTasks(build buildkite.Build) string {
	if data, ok := build.Env[skipTasksEnvVar]; ok {
		if skippedTasks, ok := data.(string); ok {
			return skippedTasks
		}
	}
	return ""
}

type event struct {
	*buildkite.Timestamp
	runDelta int
}

type jobsPerformance struct {
	firstJobRunnableAt           *buildkite.Timestamp
	totalWaitSeconds             float64
	totalRunSeconds              float64
	longestRunningTaskName       string
	longestRunningTaskRunSeconds float64
	passed                       bool
}

func analyzeJobsPerformance(jobs []*buildkite.Job) (*jobsPerformance, error) {
	events := make([]event, 0)
	result := &jobsPerformance{passed: true}
	for _, job := range jobs {
		if job.State == nil || *job.State != "passed" {
			result.passed = false
		}

		if !isFinishedWorkerTask(job) {
			continue
		}

		if result.firstJobRunnableAt == nil || job.RunnableAt.Time.Before(result.firstJobRunnableAt.Time) {
			result.firstJobRunnableAt = job.RunnableAt
		}

		// Job lifecycle: scheduled -> created -> runnable -> started -> finished
		// wait time = started - runnable
		// run time = finished - started
		// total time = finished - runnable
		// Scheduled and created are affected by "wait" steps, so we don't look at them here.
		duration := getDifferenceSeconds(job.RunnableAt, job.FinishedAt)
		if duration > result.longestRunningTaskRunSeconds {
			result.longestRunningTaskName = *job.Name
			result.longestRunningTaskRunSeconds = duration
		}
	}
	sortFunc := func(i, j int) bool { return events[i].Time.Before(events[j].Time) }
	sort.Slice(events, sortFunc)

	runningTasks := 0
	prevTime := result.firstJobRunnableAt
	for _, evt := range events {
		elapsed := getDifferenceSeconds(prevTime, evt.Timestamp)
		if runningTasks == 0 {
			result.totalWaitSeconds += elapsed
		} else {
			result.totalWaitSeconds += elapsed
		}

		runningTasks += evt.runDelta
		prevTime = evt.Timestamp
	}
	if runningTasks > 0 {
		return nil, fmt.Errorf("There are %d unfinished jobs", runningTasks)
	}
	return result, nil
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
