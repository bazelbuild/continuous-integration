package publishers

import (
	"database/sql"
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/metrics"
)

const columnTypeQuery = "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '?' AND COLUMN_NAME = '?';"

type CloudSqlGc struct {
	conn *sql.DB
	stmt *sql.Stmt
}

func CreateCloudSqlGc(conn *sql.DB) (*CloudSqlGc, error) {
	stmt, err := conn.Prepare(columnTypeQuery)
	if err != nil {
		return nil, fmt.Errorf("Failed to prepare statement: %v\n\tStatement: %s", err, columnTypeQuery)
	}
	return &CloudSqlGc{conn, stmt}, nil
}

func (gc *CloudSqlGc) Run(metric metrics.GarbageCollectedMetric) (int, error) {
	prefix := fmt.Sprintf("Failed to run Cloud SQL GC for metric %s: ", metric.Name())
	colType, err := gc.resolveIndexColumnType(metric)
	if err != nil {
		return 0, fmt.Errorf("%s%v", prefix, err)
	}

	_ = colType
	/*
		TODO:
		- draft query based on colType
		- delete records based on query
	*/

	return 0, nil
}

//select timestampdiff(second, str_to_date("2019-02-01 09:15:00", GET_FORMAT(DATETIME,'ISO')), str_to_date("2019-02-02 09:15:01", GET_FORMAT(DATETIME,'ISO'))) as foo;

func (gc *CloudSqlGc) resolveIndexColumnType(metric metrics.GarbageCollectedMetric) (string, error) {
	table := metric.Name()
	column := metric.Columns()[metric.SortColumnIndex()].Name

	var colType string
	err := gc.stmt.QueryRow(table, column).Scan(&colType)
	if err != nil {
		return "", fmt.Errorf("Failed to determine type of column '%s' in table '%s': %v", column, table, err)
	}
	return colType, nil
}
