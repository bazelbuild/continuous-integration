package publishers

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/continuous-integration/metrics/metrics"
)

type Stdout struct {
}

func (stdout *Stdout) Name() string {
	return "Stdout"
}

func (stdout *Stdout) RegisterMetric(metric metrics.Metric) error {
	// Nothing to do.
	return nil
}

func (stdout *Stdout) Publish(metricName string, newData *data.DataSet) error {
	fmt.Printf("Metric %s:\n%s\n", metricName, newData)
	return nil
}
