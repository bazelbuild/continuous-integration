package publishers

import (
	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/continuous-integration/metrics/metrics"
)

type Stackdriver struct {
}

func (sd *Stackdriver) Name() string {
	return "Stackdriver"
}

func (sd *Stackdriver) RegisterMetric(metric metrics.Metric) error {
	// Nothing to do.
	return nil
}

func (sd *Stackdriver) Publish(metricName string, newData data.DataSet) error {
	return nil
}

func CreateStackdriverPublisher() *Stackdriver {
	return &Stackdriver{}
}
