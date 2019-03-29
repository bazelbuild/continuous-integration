package metrics

import (
	"github.com/fweikert/continuous-integration/metrics/data"
)

type Metric interface {
	Name() string
	Headers() []string
	Collect() (*data.DataSet, error)
}
