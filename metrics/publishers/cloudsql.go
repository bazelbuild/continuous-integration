package publishers

import (
	"database/sql"
	"fmt"
	"os"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/metrics"

	"github.com/fweikert/continuous-integration/metrics/data"
	_ "github.com/go-sql-driver/mysql"
)

const insertTemplate = "INSERT INTO %s (%s) VALUES (%s)"

type statement struct {
	prepared *sql.Stmt
	text     string
}

type CloudSql struct {
	conn       *sql.DB
	statements map[string]*statement
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

	columnNames := metrics.GetColumnNames(metric.Columns())
	placeholder := strings.TrimRight(strings.Repeat("?, ", len(columnNames)), ", ")
	insert := fmt.Sprintf(insertTemplate, name, strings.Join(columnNames, ", "), placeholder)

	nonKeyColumnNames := make([]string, 0)
	for _, c := range metric.Columns() {
		if !c.IsKey {
			nonKeyColumnNames = append(nonKeyColumnNames, c.Name)
		}
	}
	if len(nonKeyColumnNames) != len(columnNames) {
		updates := make([]string, len(nonKeyColumnNames))
		for i, c := range nonKeyColumnNames {
			updates[i] = fmt.Sprintf("%s=VALUES(%s)", c, c)
		}
		insert = fmt.Sprintf("%s ON DUPLICATE KEY UPDATE %s", insert, strings.Join(updates, ", "))
	}

	stmt, err := c.createStatement(name, insert)
	if err != nil {
		return err
	}
	c.statements[name] = stmt
	return nil
}

func (c *CloudSql) createStatement(metricName string, text string) (*statement, error) {
	stmt, err := c.conn.Prepare(text)
	if err != nil {
		return nil, fmt.Errorf("Failed to prepare insert statement for metric %s: %v\n\tStatement: %s", metricName, err, text)
	}
	return &statement{prepared: stmt, text: text}, nil
}

func (c *CloudSql) Publish(metricName string, newData data.DataSet) error {
	stmt := c.statements[metricName]
	if stmt == nil {
		return fmt.Errorf("Could not find prepared insert statement for metric %s. Have you called RegisterMetric() first?", metricName)
	}

	for _, row := range newData.GetData().Data {
		_, err := stmt.prepared.Exec(row...)
		if err != nil {
			values := make([]string, len(row))
			for i, v := range row {
				values[i] = fmt.Sprintf("%v", v)
			}
			return fmt.Errorf("Could not insert new data for metric %s: %v\n\tStatement: %s\n\tValues: %s", metricName, err, stmt.text, strings.Join(values, ", "))
		}
	}
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
		statements: make(map[string]*statement),
	}, nil
}

func getConnectionString(user, password, instance, database string, localPort int) string {
	cred := fmt.Sprintf("%s:%s@", user, password)
	if os.Getenv("GAE_INSTANCE") != "" {
		// Running in production.
		return fmt.Sprintf("%sunix(/cloudsql/%s)/%s", cred, instance, database)
	}
	return fmt.Sprintf("%stcp([localhost]:%d)/%s", cred, localPort, database)
}
