package publishers

import "fmt"

type CloudSql struct {
}

func (c CloudSql) Publish(metricName string, data map[string]interface{}) error {
	fmt.Printf("Got %v from %s\n", data, metricName)
	return nil
}

func (c CloudSql) Name() string {
	return "Cloud SQL"
}

func CreateCloudSqlPublisher() CloudSql {
	return CloudSql{}
}
