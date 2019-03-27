package service

import (
	"fmt"
	"time"
)

type MetricCollector interface {
	Collect() (map[string]interface{}, error)
}

type MetricPublisher interface {
	Publish(metricName string, data map[string]interface{}) error
	Name() string
}

type metricJob struct {
	name       string
	ticker     *time.Ticker
	collector  MetricCollector
	publishers []MetricPublisher
}

func createJob(name string, updateIntervalSeconds uint, collector MetricCollector, publishers []MetricPublisher) metricJob {
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

func (srv *MetricService) AddMetric(name string, updateIntervalSeconds uint, collector MetricCollector, publishers ...MetricPublisher) error {
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
			data, err := job.collector.Collect()
			if err != nil {
				handler(job.name, fmt.Errorf("Collection failed': %v", err))
				return
			}

			for _, p := range job.publishers {
				err = p.Publish(job.name, data)
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
