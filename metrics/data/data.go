package data

import (
	"fmt"
	"strings"
)

type DataSet interface {
	GetData() *LegacyDataSet
}

type LegacyDataSet struct {
	Headers []string
	Data    [][]interface{}
}

func (data *LegacyDataSet) String() string {
	lines := make([]string, len(data.Data)+1)
	lines[0] = strings.Join(data.Headers, "\t")
	for i, row := range data.Data {
		lines[i+1] = strings.Join(GetRowAsStrings(row), "\t")
	}
	return strings.Join(lines, "\n")
}

func CreateDataSet(headers []string) *LegacyDataSet {
	return &LegacyDataSet{Headers: headers, Data: make([][]interface{}, 0)}
}

func (lds *LegacyDataSet) GetData() *LegacyDataSet {
	return lds
}

func (lds *LegacyDataSet) AddRow(values ...interface{}) error {
	if len(values) != len(lds.Headers) {
		return fmt.Errorf("DataSet has %d columns (%s), but new row has %d (values: %s).", len(lds.Headers), strings.Join(lds.Headers, ", "), len(values), strings.Join(GetRowAsStrings(values), ", "))
	}
	lds.Data = append(lds.Data, values)
	return nil
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
