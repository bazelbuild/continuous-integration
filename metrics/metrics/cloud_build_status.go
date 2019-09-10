package metrics

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"sync"
	"time"

	pubsub "cloud.google.com/go/pubsub/apiv1"
	"github.com/bazelbuild/continuous-integration/metrics/data"
	timestamp "github.com/golang/protobuf/ptypes/timestamp"
	metricpb "google.golang.org/genproto/googleapis/api/metric"
	monitoredres "google.golang.org/genproto/googleapis/api/monitoredres"
	monitoringpb "google.golang.org/genproto/googleapis/monitoring/v3"
	pubsubpb "google.golang.org/genproto/googleapis/pubsub/v1"
)

const (
	cloudBuildBaseMetricType = "custom.googleapis.com/bazel/cloudbuild"
)

var (
	buildSuccessState = "SUCCESS"
)

type buildResult struct {
	ID         string     `json:"id"`
	ProjectID  string     `json:"projectId"`
	Status     string     `json:"status"`
	FinishTime *time.Time `json:"finishTime"`
	Source     struct {
		RepoSource struct {
			RepoName   string `json:"repoName"`
			BranchName string `json:"branchName"`
		} `json:"repoSource"`
	} `json:"source"`
}

func (br *buildResult) toRow() (*cloudBuildStatusRow, error) {
	if br.FinishTime == nil {
		return nil, fmt.Errorf("build %s hasn't finished yet", br.ID)
	}
	src := br.Source.RepoSource
	return &cloudBuildStatusRow{
		ts:      *br.FinishTime,
		build:   br.ID,
		repo:    src.RepoName,
		branch:  src.BranchName,
		success: br.success(),
	}, nil
}

func (br *buildResult) success() bool {
	return br.Status == buildSuccessState
}

func (br *buildResult) finished() bool {
	return br.FinishTime != nil
}

type CloudBuildStatus struct {
	subscriber   *pubsub.SubscriberClient
	subscription string
	columns      []Column

	mux     sync.Mutex
	results []*buildResult
	errors  []string
}

func (cbs *CloudBuildStatus) Name() string {
	return "cloud_build_status"
}

func (cbs *CloudBuildStatus) Columns() []Column {
	return cbs.columns
}

func (*CloudBuildStatus) Type() MetricType {
	return TimeBasedMetric
}

func (*CloudBuildStatus) RelevantDelta() int {
	return 2 * 24 * 60 * 60 // Two days in seconds
}

// CREATE TABLE cloud_build_status (timestamp DATETIME, build VARCHAR(255), source VARCHAR(255), success BOOL, PRIMARY KEY(timestamp, build));
func CreateCloudBuildStatus(ctx context.Context, projectID, subscriptionID string) (*CloudBuildStatus, error) {
	subscriber, err := pubsub.NewSubscriberClient(ctx)
	if err != nil {
		return nil, err
	}

	columns := []Column{Column{"timestamp", true}, Column{"build", true}, Column{"source", false}, Column{"success", false}}
	subscription := fmt.Sprintf("projects/%s/subscriptions/%s", projectID, subscriptionID)
	results := make([]*buildResult, 0)
	errors := make([]string, 0)
	cbs := &CloudBuildStatus{subscriber: subscriber, subscription: subscription, columns: columns, results: results, errors: errors}
	go cbs.listen(ctx)
	return cbs, nil
}

func (cbs *CloudBuildStatus) listen(ctx context.Context) {
	req := pubsubpb.PullRequest{
		Subscription: cbs.subscription,
		MaxMessages:  10,
	}

	for {
		res, err := cbs.subscriber.Pull(ctx, &req)
		if err != nil {
			cbs.recordError(err)
			continue
		}

		for _, m := range res.ReceivedMessages {
			if err := cbs.handleMessage(m.Message.Data); err != nil {
				cbs.recordError(err)
			}
			err := cbs.subscriber.Acknowledge(ctx, &pubsubpb.AcknowledgeRequest{
				Subscription: cbs.subscription,
				AckIds:       []string{m.AckId},
			})
			if err != nil {
				cbs.recordError(err)
			}
		}
	}
}

func (cbs *CloudBuildStatus) handleMessage(data []byte) error {
	result := new(buildResult)
	if err := json.Unmarshal(data, result); err != nil {
		return fmt.Errorf("invalid JSON message: %v", err)
	}

	if result.finished() {
		cbs.mux.Lock()
		cbs.results = append(cbs.results, result)
		cbs.mux.Unlock()
	}
	return nil
}

func (cbs *CloudBuildStatus) recordError(err error) {
	cbs.mux.Lock()
	cbs.errors = append(cbs.errors, err.Error())
	cbs.mux.Unlock()
}

func (cbs *CloudBuildStatus) Collect() (data.DataSet, error) {
	cbs.mux.Lock()
	defer cbs.mux.Unlock()

	if len(cbs.errors) > 0 {
		err := fmt.Errorf("failed to collect data due to previous errors:\n%s", strings.Join(cbs.errors, "\n"))
		cbs.errors = make([]string, 0)
		return nil, err
	}
	result := &cloudBuildStatusSet{headers: GetColumnNames(cbs.columns)}
	if len(cbs.results) > 0 {
		for _, r := range cbs.results {
			if row, err := r.toRow(); err != nil {
				return nil, err
			} else {
				result.rows = append(result.rows, row)
			}
		}
		cbs.results = make([]*buildResult, 0)
	}
	return result, nil
}

// TODO(fweikert): refactor Stackdriver code here and in platform_load
type cloudBuildStatusRow struct {
	ts      time.Time
	repo    string
	branch  string
	build   string
	success bool
}

type cloudBuildStatusSet struct {
	headers []string
	rows    []*cloudBuildStatusRow
}

func (s *cloudBuildStatusSet) GetData() *data.LegacyDataSet {
	rawSet := data.CreateDataSet(s.headers)
	for _, row := range s.rows {
		source := fmt.Sprintf("%s/%s", row.repo, row.branch)
		rawRow := []interface{}{row.ts, row.build, source, row.success}
		rawSet.Data = append(rawSet.Data, rawRow)
	}
	return rawSet
}

func (s *cloudBuildStatusSet) CreateTimeSeriesRequest(projectID string) *monitoringpb.CreateTimeSeriesRequest {
	series := make([]*monitoringpb.TimeSeries, len(s.rows))
	for i, row := range s.rows {
		series[i] = row.createTimeSeries()
	}
	return &monitoringpb.CreateTimeSeriesRequest{
		Name:       "projects/" + projectID,
		TimeSeries: series,
	}
}

func (r *cloudBuildStatusRow) createTimeSeries() *monitoringpb.TimeSeries {
	ts := &timestamp.Timestamp{
		Seconds: r.ts.Unix(),
	}
	t := fmt.Sprintf("%s/%s/%s", cloudBuildBaseMetricType, r.repo, r.branch)
	t = strings.Replace(t, "-", "_", -1)
	log.Printf("Publishing time series for metric '%s'\n", t)
	return &monitoringpb.TimeSeries{
		Metric: &metricpb.Metric{
			Type: t,
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
				Value: &monitoringpb.TypedValue_BoolValue{
					BoolValue: r.success,
				},
			},
		}},
	}
}
