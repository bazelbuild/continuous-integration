package metrics

import (
	"fmt"
	"time"

	"github.com/bazelbuild/continuous-integration/metrics/clients"
	"github.com/bazelbuild/continuous-integration/metrics/data"
	timestamp "github.com/golang/protobuf/ptypes/timestamp"
	metricpb "google.golang.org/genproto/googleapis/api/metric"
	monitoredres "google.golang.org/genproto/googleapis/api/monitoredres"
	monitoringpb "google.golang.org/genproto/googleapis/monitoring/v3"
)

const baseMetricType = "custom.googleapis.com/bazel/ci"

type PlatformLoad struct {
	client  clients.BuildkiteClient
	orgs    []string
	columns []Column
	builds  int
}

func (pl *PlatformLoad) Name() string {
	return "platform_load"
}

func (pl *PlatformLoad) Columns() []Column {
	return pl.columns
}

func (*PlatformLoad) Type() MetricType {
	return TimeBasedMetric
}

func (*PlatformLoad) RelevantDelta() int {
	return 2 * 24 * 60 * 60 // Two days in seconds
}

func (pl *PlatformLoad) Collect() (data.DataSet, error) {
	result := &loadDataSet{headers: GetColumnNames(pl.columns), ts: time.Now(), rows: make([]*loadDataRow, 0)}
	for _, org := range pl.orgs {
		pid := &data.PipelineID{Org: org, Slug: "all"}
		builds, err := pl.client.GetMostRecentBuilds(pid, pl.builds)
		if err != nil {
			return nil, fmt.Errorf("Cannot get builds to determine platform load: %v", err)
		}

		allPlatforms := make(map[string]bool)
		waiting := make(map[string]int)
		running := make(map[string]int)
		for _, build := range builds {
			for _, job := range build.Jobs {
				// Do not use getPlatform() since it may return "rbe", but here we're only interested in the actual worker OS (which would be "linux" in the rbe case).
				platform := getPlatformFromAgentQueryRules(job.AgentQueryRules)
				if platform == "" || job.CreatedAt == nil || job.FinishedAt != nil {
					continue
				}
				allPlatforms[platform] = true
				switch *job.State {
				case "running":
					running[platform] += 1
				case "scheduled", "runnable":
					/*
						State "scheduled" / "runnable" = waiting for a worker to become available
						State "waiting" / "waiting_failed" = waiting for another task to finish

						We're only interested in "scheduled" and "runnable" jobs since they may indicate a shortage of workers.
					*/
					waiting[platform] += 1
				}

			}
		}

		for platform := range allPlatforms {
			row := &loadDataRow{org: org, platform: platform, waitingJobs: waiting[platform], runningJobs: running[platform]}
			result.rows = append(result.rows, row)
		}
	}
	return result, nil
}

// CREATE TABLE platform_load (timestamp DATETIME, org VARCHAR(255), platform VARCHAR(255), waiting_jobs INT, running_jobs INT, PRIMARY KEY(org, timestamp, platform));
func CreatePlatformLoad(client clients.BuildkiteClient, builds int, orgs ...string) *PlatformLoad {
	columns := []Column{Column{"timestamp", true}, Column{"org", true}, Column{"platform", true}, Column{"waiting_jobs", false}, Column{"running_jobs", false}}
	return &PlatformLoad{client: client, orgs: orgs, columns: columns, builds: builds}
}

type loadDataRow struct {
	org         string
	platform    string
	waitingJobs int
	runningJobs int
}

type loadDataSet struct {
	headers []string
	ts      time.Time
	rows    []*loadDataRow
}

func (lds *loadDataSet) GetData() *data.LegacyDataSet {
	rawSet := data.CreateDataSet(lds.headers)
	for _, row := range lds.rows {
		rawRow := []interface{}{lds.ts, row.org, row.platform, row.waitingJobs, row.runningJobs}
		rawSet.Data = append(rawSet.Data, rawRow)
	}
	return rawSet
}

func (lds *loadDataSet) CreateTimeSeriesRequest(projectID string) *monitoringpb.CreateTimeSeriesRequest {
	ts := &timestamp.Timestamp{
		Seconds: lds.ts.Unix(),
	}
	series := make([]*monitoringpb.TimeSeries, len(lds.rows)*3)
	for i, row := range lds.rows {
		series[3*i] = createTimeSeries(ts, row.org, row.platform, "waiting_jobs", row.waitingJobs)
		series[3*i+1] = createTimeSeries(ts, row.org, row.platform, "running_jobs", row.runningJobs)
		series[3*i+2] = createTimeSeries(ts, row.org, row.platform, "required_workers", row.waitingJobs+row.runningJobs)
	}
	return &monitoringpb.CreateTimeSeriesRequest{
		Name:       "projects/" + projectID,
		TimeSeries: series,
	}
}

func createTimeSeries(ts *timestamp.Timestamp, org, platform, metricType string, value int) *monitoringpb.TimeSeries {
	return &monitoringpb.TimeSeries{
		Metric: &metricpb.Metric{
			Type: fmt.Sprintf("%s/%s/%s/%s", baseMetricType, org, platform, metricType),
		},
		Resource: &monitoredres.MonitoredResource{
			Type: "global",
		},
		Points: []*monitoringpb.Point{{
			Interval: &monitoringpb.TimeInterval{
				StartTime: ts,
				EndTime:   ts,
			},
			Value: &monitoringpb.TypedValue{
				Value: &monitoringpb.TypedValue_Int64Value{
					Int64Value: int64(value),
				},
			},
		}},
	}
}
