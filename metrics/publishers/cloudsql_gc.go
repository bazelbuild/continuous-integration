package publishers

import (
	"database/sql"
	"fmt"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/metrics"
)

const columnTypeQuery = "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = ? AND COLUMN_NAME = ?;"

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

func (gc *CloudSqlGc) Run(metric metrics.GarbageCollectedMetric) (int64, error) {
	handleError := func(err error) error {
		return fmt.Errorf("Failed to run Cloud SQL GC for metric %s: %v", metric.Name(), err)
	}
	query, err := gc.createDeleteQuery(metric)
	if err != nil {
		return 0, handleError(err)
	}
	result, err := gc.conn.Exec(query)
	if err != nil {
		return 0, handleError(err)

	}
	rows, err := result.RowsAffected()
	if err != nil {
		return 0, handleError(err)

	}
	return rows, nil
}

//delete t from worker_availability t join (select max(timestamp) as latest from worker_availability) m on timestampdiff(second, t.timestamp, latest) > 3600*24;
//select * from platform_usage t join (select org, pipeline, max(build) as latest from platform_usage group by org, pipeline) m on t.org = m.org and t.pipeline = m.pipeline and latest - t.build > 100;

func (gc *CloudSqlGc) createDeleteQuery(metric metrics.GarbageCollectedMetric) (string, error) {
	colType, err := gc.resolveIndexColumnType(metric)
	if err != nil {
		return "", err
	}

	table := metric.Name()
	column := metric.Index().Name
	var pattern string
	switch strings.ToUpper(colType) {
	case "DATETIME":
		pattern = "timestampdiff(second, t.%s, latest)"
	case "TINYINT", "SMALLINT", "MEDIUMINT", "INT", "INTEGER", "BIGINT":
		pattern = "latest - t.%s"
	default:
		return "", fmt.Errorf("Unsupported type '%s' for column '%s'", colType, metric.Index().Name)
	}

	query := fmt.Sprintf("delete t from %[1]s t join (select max(%[2]s) as latest from %[1]s) m on %[3]s > %d;", table, column, fmt.Sprintf(pattern, column), metric.RelevantDelta())
	return query, nil
}

func (gc *CloudSqlGc) resolveIndexColumnType(metric metrics.GarbageCollectedMetric) (string, error) {
	table := metric.Name()
	column := metric.Index().Name

	var colType string
	err := gc.stmt.QueryRow(table, column).Scan(&colType)
	if err != nil {
		return "", fmt.Errorf("Failed to determine type of column '%s' in table '%s': %v", column, table, err)
	}
	return colType, nil
}
