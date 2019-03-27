package service

import (
	"fmt"
	"time"

	"github.com/fweikert/continuous-integration/metrics/data"
)

type metricJob struct {
	name       string
	ticker     *time.Ticker
	collector  data.Collector
	publishers []data.Publisher
}

func createJob(name string, updateIntervalSeconds uint, collector data.Collector, publishers []data.Publisher) metricJob {
	return metricJob{name: name, ticker: time.NewTicker(time.Duration(updateIntervalSeconds) * time.Second), collector: collector, publishers: publishers}
}

type ErrorHandler func(string, error)

type MetricService struct {
	jobs    map[string]metricJob
	handler ErrorHandler
}

func CreateService(handler ErrorHandler) *MetricService {
	return &MetricService{jobs: make(map[string]metricJob), handler: handler}
}

func (srv *MetricService) AddMetric(name string, updateIntervalSeconds uint, collector data.Collector, publishers ...data.Publisher) error {
	if _, ok := srv.jobs[name]; ok {
		return fmt.Errorf("There is already a job named '%s'", name)
	}
	srv.jobs[name] = createJob(name, updateIntervalSeconds, collector, publishers)
	return nil
}

func (srv *MetricService) Start() {
	for _, j := range srv.jobs {
		j.start(srv.handler)
	}
}

func (srv *MetricService) Stop() {
	for _, j := range srv.jobs {
		j.stop()
	}
}

func (job *metricJob) start(handler ErrorHandler) {
	go func() {
		for range job.ticker.C {
			newData, err := job.collector.Collect()
			if err != nil {
				handler(job.name, fmt.Errorf("Collection failed': %v", err))
				return
			}

			for _, p := range job.publishers {
				err = p.Publish(job.name, newData)
				if err != nil {
					handler(job.name, fmt.Errorf("Publishing to %s failed': %v", p.Name(), err))
				}
			}
		}
	}()
}

func (j *metricJob) stop() {
	j.ticker.Stop()
}
