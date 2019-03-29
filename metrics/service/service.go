package service

import (
	"fmt"
	"time"

	"github.com/fweikert/continuous-integration/metrics/metrics"
	"github.com/fweikert/continuous-integration/metrics/publishers"
)

type metricJob struct {
	ticker     *time.Ticker
	metric     metrics.Metric
	publishers []publishers.Publisher
}

func (job *metricJob) start(handler ErrorHandler) {
	name := job.metric.Name()
	err := job.initialize()
	if err != nil {
		handler(name, err)
		return
	}

	go func() {
		for range job.ticker.C {
			newData, err := job.metric.Collect()
			if err != nil {
				handler(name, fmt.Errorf("Collection failed': %v", err))
				return
			}
			for _, p := range job.publishers {
				err = p.Publish(name, newData)
				if err != nil {
					handler(name, fmt.Errorf("Publishing to %s failed': %v", p.Name(), err))
				}
			}
		}
	}()
}

func (job *metricJob) initialize() error {
	for _, publisher := range job.publishers {
		err := publisher.RegisterMetric(job.metric)
		if err != nil {
			return err
		}
	}
	return nil
}

func (job *metricJob) stop() {
	job.ticker.Stop()
}

func createJob(metric metrics.Metric, updateIntervalSeconds uint, publisherInstances []publishers.Publisher) metricJob {
	return metricJob{metric: metric, ticker: time.NewTicker(time.Duration(updateIntervalSeconds) * time.Second), publishers: publisherInstances}
}

type ErrorHandler func(string, error)

type MetricService struct {
	jobs    map[string]metricJob
	handler ErrorHandler
}

func CreateService(handler ErrorHandler) *MetricService {
	return &MetricService{jobs: make(map[string]metricJob), handler: handler}
}

func (srv *MetricService) AddMetric(metric metrics.Metric, updateIntervalSeconds uint, publisherInstances ...publishers.Publisher) error {
	name := metric.Name()
	if _, ok := srv.jobs[name]; ok {
		return fmt.Errorf("There is already a job for metric '%s'", name)
	}
	srv.jobs[name] = createJob(metric, updateIntervalSeconds, publisherInstances)
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
