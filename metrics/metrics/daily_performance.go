package metrics

import (
	"fmt"
	"sort"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
	"github.com/buildkite/go-buildkite/buildkite"
)

type percentiles struct {
	median float64
	p90    float64
	p95    float64
	p99    float64
}

type dailyStatistics struct {
	buildTimes []float64
	builds     int
}

func (ds *dailyStatistics) addBuild(build *buildkite.Build) {
	ds.builds++
	ds.buildTimes = append(ds.buildTimes, getDifferenceSeconds(build.ScheduledAt, build.FinishedAt))
}

func (ds *dailyStatistics) calculatePercentiles() *percentiles {
	sort.Float64s(ds.buildTimes)
	return &percentiles{median: ds.getPercentile(50), p90: ds.getPercentile(90), p95: ds.getPercentile(95), p99: ds.getPercentile(99)}
}

func (ds *dailyStatistics) getPercentile(percent int) float64 {
	index := int(len(ds.buildTimes) * percent / 100.0)
	return ds.buildTimes[index]
}

type DailyPerformance struct {
	client      clients.BuildkiteClient
	pipelines   []*data.PipelineID
	columns     []Column
	lastNBuilds int
}

func (dp *DailyPerformance) Name() string {
	return "daily_performance"
}

func (dp *DailyPerformance) Columns() []Column {
	return dp.columns
}

func (dp *DailyPerformance) Collect() (data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(dp.columns))
	for _, pipeline := range dp.pipelines {
		builds, err := dp.client.GetMostRecentBuilds(pipeline, dp.lastNBuilds)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect daily performance statistics for pipeline %s: %v", pipeline, err)
		}
		statisticsPerDay := make(map[time.Time]*dailyStatistics)
		for _, build := range builds {
			if build.FinishedAt == nil || build.State == nil || *build.State != "passed" {
				continue
			}

			key := getMidnight(build.ScheduledAt.Time)
			if _, ok := statisticsPerDay[key]; !ok {
				statisticsPerDay[key] = &dailyStatistics{}
			}
			statisticsPerDay[key].addBuild(&build)
		}
		for dt, statistics := range statisticsPerDay {
			p := statistics.calculatePercentiles()
			err := result.AddRow(pipeline.Org, pipeline.Slug, dt, statistics.builds, p.median, p.p90, p.p95, p.p99)
			if err != nil {
				return nil, fmt.Errorf("Failed to add result for %s in %s: %v", dt, pipeline.Slug, err)
			}
		}
	}
	return result, nil
}

func getMidnight(t time.Time) time.Time {
	return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, t.Location())
}

// CREATE TABLE daily_performance (org VARCHAR(255), pipeline VARCHAR(255), day DATE, passed_builds INT, median_seconds FLOAT, p90_seconds FLOAT, p95_seconds FLOAT, p99_seconds FLOAT, PRIMARY KEY(org, pipeline, day));
func CreateDailyPerformance(client clients.BuildkiteClient, lastNBuilds int, pipelines ...*data.PipelineID) *DailyPerformance {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"day", true}, Column{"passed_builds", false}, Column{"median_seconds", false}, Column{"p90_seconds", false}, Column{"p95_seconds", false}, Column{"p99_seconds", false}}
	return &DailyPerformance{client: client, pipelines: pipelines, columns: columns, lastNBuilds: lastNBuilds}
}
