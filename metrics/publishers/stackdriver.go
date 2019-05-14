package publishers

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/clients"

	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/continuous-integration/metrics/metrics"
)

type Stackdriver struct {
	client    *clients.StackdriverClient
	projectID string
}

func (sd *Stackdriver) Name() string {
	return "Stackdriver"
}

func (sd *Stackdriver) RegisterMetric(metric metrics.Metric) error {
	// Nothing to do.
	return nil
}

func (sd *Stackdriver) Publish(metricName string, newData data.DataSet) error {
	set, ok := newData.(data.StackDriverTimeSeriesDataSet)
	if !ok {
		return fmt.Errorf("Metric '%s' does not produce a valid StackDriverTimeSeriesDataSet instance", metricName)
	}

	err := sd.client.WriteTimeSeries(set.CreateTimeSeriesRequest(sd.projectID))
	if err != nil {
		return fmt.Errorf("Could not write time series for metric '%s' in project '%s': %v", metricName, sd.projectID, err)
	}
	return nil
}

func CreateStackdriverPublisher(client *clients.StackdriverClient, projectID string) *Stackdriver {
	return &Stackdriver{client: client, projectID: projectID}
}
