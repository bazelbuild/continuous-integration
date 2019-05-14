package clients

import (
	"context"
	"fmt"

	monitoring "cloud.google.com/go/monitoring/apiv3"
	monitoringpb "google.golang.org/genproto/googleapis/monitoring/v3"
)

const metricType = "custom.googleapis.com/custom_measurement"

type StackdriverClient struct {
	client *monitoring.MetricClient
}

func (sc *StackdriverClient) WriteTimeSeries(request *monitoringpb.CreateTimeSeriesRequest) error {
	ctx := context.Background()
	if err := sc.client.CreateTimeSeries(ctx, request); err != nil {
		return fmt.Errorf("Failed to write time series for project '%s': %v ", request.Name, err)
	}
	return nil
}

func CreateStackdriverClient() (*StackdriverClient, error) {
	ctx := context.Background()
	client, err := monitoring.NewMetricClient(ctx)
	if err != nil {
		return nil, err
	}
	return &StackdriverClient{client: client}, nil
}
