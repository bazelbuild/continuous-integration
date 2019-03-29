package publishers

import (
	"database/sql"
	"fmt"
	"os"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/metrics"

	"github.com/fweikert/continuous-integration/metrics/data"
)

const insertTemplate = "INSERT INTO %s (%s) VALUES (%s)"

type CloudSql struct {
	conn       *sql.DB
	statements map[string]*sql.Stmt
}

func (c *CloudSql) Name() string {
	return "Cloud SQL"
}

func (c *CloudSql) RegisterMetric(metric metrics.Metric) error {
	err := c.ensureTableExists(metric)
	if err != nil {
		return err
	}
	return c.prepareInsertStatement(metric)
}

func (c *CloudSql) ensureTableExists(metric metrics.Metric) error {
	// TODO(fweikert): implement
	return nil
}

func (c *CloudSql) prepareInsertStatement(metric metrics.Metric) error {
	name := metric.Name()
	if _, ok := c.statements[name]; ok {
		return fmt.Errorf("Metrics %s has already been registered for publisher %s.", name, c.Name())
	}

	headers := metric.Headers()
	placeholder := strings.TrimRight(strings.Repeat("?, ", len(headers)), ", ")
	insert := fmt.Sprintf(insertTemplate, name, strings.Join(headers, ", "), placeholder)

	stmt, err := c.conn.Prepare(insert)
	if err != nil {
		return fmt.Errorf("Failed to prepare insert statement for metric %s: %v", name, err)
	}
	c.statements[name] = stmt
	return nil
}

func (c *CloudSql) Publish(metricName string, newData *data.DataSet) error {
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
	return &CloudSql{
		conn:       conn,
		statements: make(map[string]*sql.Stmt),
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
