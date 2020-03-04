package publishers

import (
	"fmt"
	"strings"

	"github.com/bazelbuild/continuous-integration/metrics/data"
	"github.com/bazelbuild/continuous-integration/metrics/metrics"
)

type formatter func(string, data.DataSet) string

func PlainText(metricName string, newData data.DataSet) string {
	return fmt.Sprintf("Metric %s:\n%s\n", metricName, newData.GetData().String())
}

func Csv(metricName string, newData data.DataSet) string {
	rows := newData.GetData().Data
	lines := make([]string, len(rows))
	for i, row := range rows {
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

func (stdout *Stdout) Publish(metric metrics.Metric, newData data.DataSet) error {
	//fmt.Println(stdout.formatFunc(metric.Name(), newData))
	return nil
}

func CreateStdoutPublisher(formatFunc formatter) *Stdout {
	return &Stdout{formatFunc: formatFunc}
}
