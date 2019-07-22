package metrics

import (
	"github.com/bazelbuild/continuous-integration/metrics/data"
)

type Column struct {
	Name  string
	IsKey bool
}

type Metric interface {
	Name() string
	Columns() []Column
	Collect() (data.DataSet, error)
}

type MetricType int

const (
	TimeBasedMetric MetricType = iota
	BuildBasedMetric
)

type GarbageCollectedMetric interface {
	Metric
	Type() MetricType
	RelevantDelta() int
}

func GetColumnNames(columns []Column) []string {
	names := make([]string, len(columns))
	for i, c := range columns {
		names[i] = c.Name
	}
	return names
}
