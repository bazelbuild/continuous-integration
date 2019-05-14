package data

import (
	"fmt"
	"strings"
)

type DataSet interface {
	AddRow(values ...interface{}) error
	GetHeaders() []string
	GetData() [][]interface{}
	String() string
}

type DefaultDataSet struct {
	headers []string
	data    [][]interface{}
}

func (data *DefaultDataSet) AddRow(values ...interface{}) error {
	if len(values) != len(data.headers) {
		return fmt.Errorf("DataSet has %d columns (%s), but new row has %d (values: %s).", len(data.headers), strings.Join(data.headers, ", "), len(values), strings.Join(GetRowAsStrings(values), ", "))
	}
	data.data = append(data.data, values)
	return nil
}

func (data *DefaultDataSet) GetHeaders() []string {
	return data.headers
}

func (data *DefaultDataSet) GetData() [][]interface{} {
	return data.data
}

func (data *DefaultDataSet) String() string {
	lines := make([]string, len(data.data)+1)
	lines[0] = strings.Join(data.headers, "\t")
	for i, row := range data.data {
		lines[i+1] = strings.Join(GetRowAsStrings(row), "\t")
	}
	return strings.Join(lines, "\n")
}

func GetRowAsStrings(row []interface{}) []string {
	stringValues := make([]string, len(row))
	for i, v := range row {
		if str, ok := v.(string); ok {
			stringValues[i] = str
		} else {
			stringValues[i] = fmt.Sprintf("%v", v)
		}
	}
	return stringValues
}

func CreateDataSet(headers []string) DataSet {
	return &DefaultDataSet{headers: headers, data: make([][]interface{}, 0)}
}
