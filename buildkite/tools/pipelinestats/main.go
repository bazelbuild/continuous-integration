package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"os"
	"sort"
	"strconv"
	"time"

	"github.com/buildkite/go-buildkite/buildkite"
)

type durationPercentiles struct {
	Max   time.Duration
	Min   time.Duration
	Pct90 time.Duration
	Pct70 time.Duration
	Pct50 time.Duration
	Pct30 time.Duration
}

type dayBuildStats struct {
	Day          time.Time
	NumBuilds    int
	NumFailed    int
	NumPassed    int
	BuildTimes   durationPercentiles
	JobWaitTimes map[string]durationPercentiles
}

func optionsForPage(page int) *buildkite.BuildsListOptions {
	return &buildkite.BuildsListOptions{
		ListOptions: buildkite.ListOptions{
			Page:    page,
			PerPage: 100,
		},
	}
}

func fetchAllBuilds(org string, pipeline string, client *buildkite.Client) ([]buildkite.Build, error) {
	page := 0
	var builds []buildkite.Build
	for {
		buildsOnPage, _, err := client.Builds.ListByPipeline(org, pipeline, optionsForPage(page))
		if err != nil {
			return nil, err
		}
		if len(buildsOnPage) == 0 {
			break
		}
		builds = append(builds, buildsOnPage...)
		page++
	}
	return builds, nil
}

func computeDurationPercentiles(durations []time.Duration) durationPercentiles {
	if len(durations) == 0 {
		return durationPercentiles{}
	}

	sort.Slice(durations, func(i, j int) bool {
		return durations[i] < durations[j]
	})

	return durationPercentiles{
		Max:   durations[len(durations)-1],
		Min:   durations[0],
		Pct90: durations[9*len(durations)/10],
		Pct70: durations[7*len(durations)/10],
		Pct50: durations[5*len(durations)/10],
		Pct30: durations[3*len(durations)/10],
	}
}

func computeDayBuildStats(builds []buildkite.Build) *dayBuildStats {
	if len(builds) == 0 {
		return nil
	}
	var stats dayBuildStats
	createdAt := builds[0].CreatedAt
	stats.Day = time.Date(createdAt.Year(), createdAt.Month(), createdAt.Day(), 0, 0, 0, 0,
		createdAt.Location())
	stats.NumBuilds = len(builds)

	var buildTimes []time.Duration
	jobWaitTimes := make(map[string][]time.Duration)
	for _, build := range builds {
		if build.FinishedAt != nil && build.CreatedAt != nil {
			buildTime := time.Duration(0)
			for _, job := range build.Jobs {
				if job.Name == nil || job.StartedAt == nil || job.CreatedAt == nil ||
					job.FinishedAt == nil {
					continue
				}
				waitTime := job.StartedAt.Time.Sub(job.CreatedAt.Time)
				jobBuildTime := job.FinishedAt.Time.Sub(job.StartedAt.Time)
				if jobBuildTime > buildTime {
					// Use the maximum job build time as the duration, instead of the build's
					// start and finish time. This is because retries of jobs also count towards
					// the build's time.
					buildTime = jobBuildTime
				}
				jobWaitTimes[*job.Name] = append(jobWaitTimes[*job.Name], waitTime)
			}
			buildTimes = append(buildTimes, buildTime)
		}

		if *build.State == "passed" {
			stats.NumPassed++
		}
		if *build.State == "failed" {
			stats.NumFailed++
		}
	}

	stats.BuildTimes = computeDurationPercentiles(buildTimes)

	stats.JobWaitTimes = make(map[string]durationPercentiles, len(jobWaitTimes))
	for jobName, durations := range jobWaitTimes {
		stats.JobWaitTimes[jobName] = computeDurationPercentiles(durations)
	}

	return &stats
}

func buildStatsPerDay(builds []buildkite.Build) ([]*dayBuildStats, []string) {
	if len(builds) == 0 {
		return []*dayBuildStats{}, []string{}
	}

	sort.Slice(builds, func(i, j int) bool {
		return builds[i].CreatedAt.Time.Before(builds[j].CreatedAt.Time)
	})

	var stats []*dayBuildStats
	day := 0
	var dayBuilds []buildkite.Build
	jobNamesMap := make(map[string]bool)
	for _, build := range builds {
		if day != build.CreatedAt.Day() {
			if len(dayBuilds) > 0 {
				dayStats := computeDayBuildStats(dayBuilds)
				for jobName := range dayStats.JobWaitTimes {
					jobNamesMap[jobName] = true
				}
				stats = append(stats, dayStats)
			}

			dayBuilds = nil
			day = build.CreatedAt.Day()
		}
		dayBuilds = append(dayBuilds, build)
	}

	if len(dayBuilds) > 0 {
		dayStats := computeDayBuildStats(dayBuilds)
		for jobName := range dayStats.JobWaitTimes {
			jobNamesMap[jobName] = true
		}
		stats = append(stats, dayStats)

	}

	var jobNames []string
	for jobName := range jobNamesMap {
		jobNames = append(jobNames, jobName)
	}
	sort.Strings(jobNames)

	return stats, jobNames
}

func durationPercentilesFieldNames(prefix string) []string {
	fieldNames := []string{"Max", "Min", "Pct90", "Pc70", "Pct50", "Pct30"}
	for i, value := range fieldNames {
		fieldNames[i] = prefix + "." + value
	}
	return fieldNames
}

func appendDurationPercentiles(line []string, stats *durationPercentiles) []string {
	line = append(line, strconv.Itoa(int(stats.Max.Seconds())))
	line = append(line, strconv.Itoa(int(stats.Min.Seconds())))
	line = append(line, strconv.Itoa(int(stats.Pct90.Seconds())))
	line = append(line, strconv.Itoa(int(stats.Pct70.Seconds())))
	line = append(line, strconv.Itoa(int(stats.Pct50.Seconds())))
	line = append(line, strconv.Itoa(int(stats.Pct30.Seconds())))

	return line
}

func main() {
	apiToken := os.Getenv("BUILDKITE_API_TOKEN")
	if apiToken == "" {
		fmt.Println("BUILDKITE_API_TOKEN environment variable not set.")
		os.Exit(1)
	}
	pipelineSlug := flag.String("pipeline_slug", "", "Slug of the Buildkite pipeline")
	flag.Parse()

	if *pipelineSlug == "" {
		flag.Usage()
		os.Exit(1)
	}

	config, _ := buildkite.NewTokenConfig(apiToken, false)
	client := buildkite.NewClient(config.Client())

	builds, _ := fetchAllBuilds("bazel", *pipelineSlug, client)
	stats, jobNames := buildStatsPerDay(builds)

	writer := csv.NewWriter(os.Stdout)
	defer writer.Flush()

	csvHeaders := []string{"Day", "NumBuilds", "NumFailed", "NumPassed"}
	csvHeaders = append(csvHeaders, durationPercentilesFieldNames("BuildTimes")...)
	for _, jobName := range jobNames {
		csvHeaders = append(csvHeaders, durationPercentilesFieldNames("WaitTimes["+jobName+"]")...)
	}
	writer.Write(csvHeaders)

	for _, dayStats := range stats {
		var line []string
		line = append(line, dayStats.Day.Format("2006-01-02"))
		line = append(line, strconv.Itoa(dayStats.NumBuilds))
		line = append(line, strconv.Itoa(dayStats.NumFailed))
		line = append(line, strconv.Itoa(dayStats.NumPassed))

		line = appendDurationPercentiles(line, &dayStats.BuildTimes)

		for _, jobName := range jobNames {
			if waitTimes, ok := dayStats.JobWaitTimes[jobName]; ok {
				line = appendDurationPercentiles(line, &waitTimes)
			} else {
				line = appendDurationPercentiles(line, &durationPercentiles{})
			}
		}
		writer.Write(line)
	}
}
