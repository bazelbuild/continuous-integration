package data

import (
	"fmt"
	"strings"
)

type DataSet struct {
	Headers []string
	Data    [][]interface{}
}

func (data *DataSet) AddRow(values ...interface{}) error {
	if len(values) != len(data.Headers) {
		return fmt.Errorf("DataSet has %d columns (%s), but new row has %d (values: %s).", len(data.Headers), strings.Join(data.Headers, ", "), len(values), strings.Join(GetRowAsStrings(values), ", "))
	}
	data.Data = append(data.Data, values)
	return nil
}

func (data *DataSet) String() string {
	lines := make([]string, len(data.Data)+1)
	lines[0] = strings.Join(data.Headers, "\t")
	for i, row := range data.Data {
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

func CreateDataSet(headers []string) *DataSet {
	return &DataSet{Headers: headers, Data: make([][]interface{}, 0)}
}
