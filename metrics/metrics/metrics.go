package metrics

import (
	"github.com/fweikert/continuous-integration/metrics/data"
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

func GetColumnNames(columns []Column) []string {
	names := make([]string, len(columns))
	for i, c := range columns {
		names[i] = c.Name
	}
	return names
}
