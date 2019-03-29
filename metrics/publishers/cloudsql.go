package publishers

import (
	"database/sql"
	"fmt"
	"os"

	"github.com/fweikert/continuous-integration/metrics/metrics"

	"github.com/fweikert/continuous-integration/metrics/data"
)

const insertStatement = ""

type CloudSql struct {
	conn   *sql.DB
	insert *sql.Stmt
}

func (c CloudSql) Name() string {
	return "Cloud SQL"
}

func (c CloudSql) RegisterMetric(metric metrics.Metric) error {
	// 1. Prepare statemets
	// 2. Check that table exists (or create onw)
	return nil
}

func (c CloudSql) Publish(metricName string, newData *data.DataSet) error {
	fmt.Printf("Got %v from %s\n", newData, metricName)
	// 1. Lock table
	// 2. insert row, ignore
	// http://bogdan.org.ua/2007/10/18/mysql-insert-if-not-exists-syntax.html
	// https://dev.mysql.com/doc/refman/8.0/en/insert-on-duplicate.html
	// https://stackoverflow.com/questions/3164505/mysql-insert-record-if-not-exists-in-table
	return nil
}

func CreateCloudSqlPublisher(user, password, instance, database string, localPort int) (*CloudSql, error) {
	conn, err := sql.Open("mysql", getConnectionString(user, password, instance, database, localPort))
	if err != nil {
		return nil, fmt.Errorf("Could not establish connection to database: %v", err)
	}
	if err := conn.Ping(); err != nil {
		conn.Close()
		return nil, fmt.Errorf("Connection to database is bad: %v", err)
	}

	insert, err := conn.Prepare(insertStatement)
	if err != nil {
		return nil, fmt.Errorf("Failed to prepare insert statement: %v", err)
	}

	return &CloudSql{
		conn:   conn,
		insert: insert,
	}, nil
}

func getConnectionString(user, password, instance, database string, localPort int) string {
	cred := "%s:%s@"
	if os.Getenv("GAE_INSTANCE") != "" {
		// Running in production.
		return fmt.Sprintf("%sunix(/cloudsql/%s)/%s", cred, instance, database)
	}
	return fmt.Sprintf("%stcp([localhost]:%d)/%s", cred, localPort, database)
}
