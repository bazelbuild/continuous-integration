package publishers

import (
	"github.com/bazelbuild/continuous-integration/metrics/data"
	"github.com/bazelbuild/continuous-integration/metrics/metrics"
)

type DevNull struct {
}

func (*DevNull) Name() string {
	return "/dev/null"
}

func (*DevNull) RegisterMetric(metric metrics.Metric) error {
	// Nothing to do.
	return nil
}

func (*DevNull) Publish(metric metrics.Metric, newData data.DataSet) error {
	// Nothing to do.
	return nil
}
