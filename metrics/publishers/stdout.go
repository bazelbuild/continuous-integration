package publishers

import (
	"fmt"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/continuous-integration/metrics/metrics"
)

type formatter func(*data.DataSet) string

func PlainText(newData *data.DataSet) string {
	return newData.String()
}

func Csv(newData *data.DataSet) string {
	lines := make([]string, len(newData.Data))
	for i, row := range newData.Data {
		lines[i] = strings.Join(data.GetRowAsStrings(row), ";")
	}
	return strings.Join(lines, "\n")
}

type Stdout struct {
	formatFunc formatter
}

func (stdout *Stdout) Name() string {
	return "Stdout"
}

func (stdout *Stdout) RegisterMetric(metric metrics.Metric) error {
	// Nothing to do.
	return nil
}

func (stdout *Stdout) Publish(metricName string, newData *data.DataSet) error {
	fmt.Printf("Metric %s:\n%s\n", metricName, stdout.formatFunc(newData))
	return nil
}

func CreateStdoutPublisher(formatFunc formatter) *Stdout {
	return &Stdout{formatFunc: formatFunc}
}
