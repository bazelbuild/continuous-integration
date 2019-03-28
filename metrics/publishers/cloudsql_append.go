package publishers

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/data"
)

type CloudSql struct {
}

func (c CloudSql) Publish(metricName string, newData *data.DataSet) error {
	fmt.Printf("Got %v from %s\n", newData, metricName)
	return nil
}

func (c CloudSql) Name() string {
	return "Cloud SQL"
}

func CreateCloudSqlPublisher() CloudSql {
	return CloudSql{}
}
