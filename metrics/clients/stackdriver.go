package clients

import (
	"context"
	"fmt"

	monitoring "cloud.google.com/go/monitoring/apiv3"
	monitoringpb "google.golang.org/genproto/googleapis/monitoring/v3"
)

const metricType = "custom.googleapis.com/custom_measurement"

type StackdriverClient struct {
	client  *monitoring.MetricClient
	project string
	metric  string
}

func (sc *StackdriverClient) WriteTimeSeries(request *monitoringpb.CreateTimeSeriesRequest) error {
	ctx := context.Background()
	if err := sc.client.CreateTimeSeries(ctx, request); err != nil {
		return fmt.Errorf("Failed to write time series for metric '%s' in project '%s': %v ", sc.metric, sc.project, err)
	}
	return nil
}

func CreateStackdriverClient(project, metric string) (*StackdriverClient, error) {
	ctx := context.Background()
	client, err := monitoring.NewMetricClient(ctx)
	if err != nil {
		return nil, err
	}
	return &StackdriverClient{client: client, project: project, metric: metric}, nil
}
