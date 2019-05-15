package clients

import (
	"context"
	"fmt"
	"strings"

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
		return fmt.Errorf("Failed to write time series in project '%s': %v\nMetrics:\n\t%s", request.Name, err, strings.Join(getMetricsFromRequest(request), "\n\t"))
	}
	return nil
}

func getMetricsFromRequest(request *monitoringpb.CreateTimeSeriesRequest) []string {
	metrics := make([]string, 0)
	for _, series := range request.TimeSeries {
		if series != nil && series.Metric != nil {
			metrics = append(metrics, series.Metric.Type)
		}
	}
	return metrics
}

func CreateStackdriverClient() (*StackdriverClient, error) {
	ctx := context.Background()
	client, err := monitoring.NewMetricClient(ctx)
	if err != nil {
		return nil, err
	}
	return &StackdriverClient{client: client}, nil
}
