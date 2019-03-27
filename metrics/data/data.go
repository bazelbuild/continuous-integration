package data

import (
	"fmt"
	"strings"
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
		formattedValues := make([]string, len(values))
		for i, v := range values {
			formattedValues[i] = fmt.Sprintf("%v", v)
		}

		return fmt.Errorf("DataSet has %d columns (%s), but new row has %d (values: %s).", len(data.Headers), strings.Join(data.Headers, ", "), len(values), strings.Join(formattedValues, ", "))
	}
	data.Data = append(data.Data, values)
	return nil
}

func CreateDataSet(headers ...string) *DataSet {
	return &DataSet{Headers: headers, Data: make([][]interface{}, len(headers))}
}
