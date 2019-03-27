package data

import (
	"fmt"
)

type Collector interface {
	Collect() (*DataSet, error)
}

type Publisher interface {
	Publish(metricName string, data *DataSet) error
	Name() string
}

type DataSet struct {
	Headers []string
	Data    [][]interface{}
}

func (data *DataSet) AddRow(values ...interface{}) error {
	if len(values) != len(data.Headers) {
		return fmt.Errorf("DataSet has %d columns, but new row has %d.", len(data.Headers), len(values))
	}
	data.Data = append(data.Data, values)
	return nil
}

func CreateDataSet(headers ...string) *DataSet {
	return &DataSet{Headers: headers, Data: make([][]interface{}, len(headers))}
}
