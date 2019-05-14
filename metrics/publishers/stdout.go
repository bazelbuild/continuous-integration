package publishers

import (
	"fmt"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/fweikert/continuous-integration/metrics/metrics"
)

type formatter func(string, data.DataSet) string

func PlainText(metricName string, newData data.DataSet) string {
	return fmt.Sprintf("Metric %s:\n%s\n", metricName, newData.String())
}

func Csv(metricName string, newData data.DataSet) string {
	lines := make([]string, len(newData.GetData()))
	for i, row := range newData.GetData() {
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

func (stdout *Stdout) Publish(metricName string, newData data.DataSet) error {
	fmt.Println(stdout.formatFunc(metricName, newData))
	return nil
}

func CreateStdoutPublisher(formatFunc formatter) *Stdout {
	return &Stdout{formatFunc: formatFunc}
}
