package publishers

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/data"
)

type CloudSql struct {
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

func (c CloudSql) Name() string {
	return "Cloud SQL"
}

func CreateCloudSqlPublisher() CloudSql {
	return CloudSql{}
}
