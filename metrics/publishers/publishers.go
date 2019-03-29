package publishers

import (
	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/continuous-integration/metrics/metrics"
)

type Publisher interface {
	Name() string
	RegisterMetric(metric metrics.Metric) error
	Publish(metricName string, newData *data.DataSet) error
}
