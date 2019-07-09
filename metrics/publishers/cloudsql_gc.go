package publishers

import (
	"database/sql"
	"fmt"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/metrics"
)

const columnTypeQuery = "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ? AND COLUMN_NAME IN ?;"

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
	strategy, err := gc.selectStrategy(metric)
	if err != nil {
		return 0, handleError(err)
	}
	err = gc.ensureRequiredColumnsExist(metric, strategy)
	if err != nil {
		return 0, handleError(err)

	}
	rows, err := gc.executeStrategy(metric, strategy)
	if err != nil {
		return 0, handleError(err)
	}
	return rows, nil
}

var knownStrategies = map[metrics.MetricType]gcStrategy{metrics.TimeBasedMetric: timeBasedStrategy{}, metrics.BuildBasedMetric: buildBasedStrategy{}}

func (gc *CloudSqlGc) selectStrategy(metric metrics.GarbageCollectedMetric) (gcStrategy, error) {
	if strategy, ok := knownStrategies[metric.Type()]; ok {
		return strategy, nil
	}
	return nil, fmt.Errorf("Unknown GC strategy '%v'.", metric.Type())
}

func (gc *CloudSqlGc) ensureRequiredColumnsExist(metric metrics.GarbageCollectedMetric, strategy gcStrategy) error {
	actualColumns, err := gc.readActualColumns(metric, strategy)
	if err != nil {
		return fmt.Errorf("Failed to retrieve actual columns from table %s: %v", metric.Name(), err)
	}

	errors := make([]string, 0)
	for column, expectedType := range strategy.RequiredColumns() {
		if actualType, ok := actualColumns[column]; ok {
			if actualType != expectedType {
				errors = append(errors, fmt.Sprintf("Column '%s' has type '%s', but should have '%s'", column, actualType, expectedType))
			}
		} else {
			errors = append(errors, fmt.Sprintf("Missing column '%s'", column))
		}
	}

	if len(errors) > 0 {
		return fmt.Errorf("Table '%s' cannot be garbage collected since it does not have the required structure:\n\t%s", metric.Name(), strings.Join(errors, "\n\t"))
	}
	return nil
}

func (gc *CloudSqlGc) readActualColumns(metric metrics.GarbageCollectedMetric, strategy gcStrategy) (map[string]string, error) {
	keys := getKeys(strategy.RequiredColumns())
	// TODO(fweikert): check if this actually works with prepared statements
	columnString := fmt.Sprintf("('%s')", strings.Join(keys, "', '"))
	rows, err := gc.stmt.Query(metric.Name(), columnString)
	if err != nil {
		return nil, err
	}

	defer rows.Close()
	existingColumns := make(map[string]string)
	var cname, ctype string
	for rows.Next() {
		err := rows.Scan(&cname, &ctype)
		if err != nil {
			return nil, err
		}
		existingColumns[cname] = ctype
	}
	return existingColumns, rows.Err()
}

func getKeys(dict map[string]string) []string {
	keys := make([]string, 0)
	for k := range dict {
		keys = append(keys, k)
	}
	return keys
}

func (gc *CloudSqlGc) executeStrategy(metric metrics.GarbageCollectedMetric, strategy gcStrategy) (int64, error) {
	query := strategy.DeletionQuery(metric.Name(), metric.RelevantDelta())
	result, err := gc.conn.Exec(query)
	if err != nil {
		return 0, err
	}
	rows, err := result.RowsAffected()
	if err != nil {
		return 0, err

	}
	return rows, nil
}

type gcStrategy interface {
	RequiredColumns() map[string]string
	DeletionQuery(string, int) string
}

// Deletes all rows that were created more than X seconds ago
type timeBasedStrategy struct{}

func (timeBasedStrategy) RequiredColumns() map[string]string {
	return map[string]string{"timestamp": "datetime"}
}

//delete t from worker_availability t join (select max(timestamp) as latest from worker_availability) m on timestampdiff(second, t.timestamp, latest) > 3600*24;
func (timeBasedStrategy) DeletionQuery(table string, rangeSeconds int) string {
	return fmt.Sprintf("delete t from %[1]s t join (select max(timestamp) as latest from %[1]s) m on timestampdiff(second, t.timestamp, latest) > %d;", table, rangeSeconds)
}

// Deletes all rows that do no contain data for the X most recent builds for each pipeline
type buildBasedStrategy struct{}

func (buildBasedStrategy) RequiredColumns() map[string]string {
	return map[string]string{"org": "varchar", "pipeline": "varchar", "build": "int"}
}

//select * from platform_usage t join (select org, pipeline, max(build) as latest from platform_usage group by org, pipeline) m on t.org = m.org and t.pipeline = m.pipeline and latest - t.build > 100;
func (buildBasedStrategy) DeletionQuery(table string, buildRange int) string {
	return fmt.Sprintf("select * from %[1]s t join (select org, pipeline, max(build) as latest from %[1]s group by org, pipeline) m on t.org = m.org and t.pipeline = m.pipeline and latest - t.build > %d;", table, buildRange)
}
