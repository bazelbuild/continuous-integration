package service

import (
	"fmt"
	"log"
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
	err := job.initialize()
	if err != nil {
		handler(job.metric.Name(), err)
		return
	}

	go func(currentJob metricJob) {
		for ; true; <-currentJob.ticker.C {
			currentJob.run(handler)
		}
	}(*job)
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

func (job *metricJob) run(handler ErrorHandler) {
	name := job.metric.Name()
	log.Printf("Collecting data for metric %s\n", name)
	newData, err := job.metric.Collect()
	if err != nil {
		handler(name, fmt.Errorf("Collection failed': %v", err))
		return
	}
	for _, p := range job.publishers {
		log.Printf("Publishing data for metric %s to %s\n", name, p.Name())
		err = p.Publish(name, newData)
		if err != nil {
			handler(name, fmt.Errorf("Publishing to %s failed': %v", p.Name(), err))
		}
	}
}

func (job *metricJob) stop() {
	job.ticker.Stop()
}

func createJob(metric metrics.Metric, updateIntervalMinutes uint, publisherInstances []publishers.Publisher) metricJob {
	return metricJob{metric: metric, ticker: time.NewTicker(time.Duration(updateIntervalMinutes) * time.Minute), publishers: publisherInstances}
}

type ErrorHandler func(string, error)

type MetricService struct {
	jobs    map[string]metricJob
	handler ErrorHandler
}

func CreateService(handler ErrorHandler) *MetricService {
	return &MetricService{jobs: make(map[string]metricJob), handler: handler}
}

func (srv *MetricService) AddMetric(metric metrics.Metric, updateIntervalMinutes uint, publisherInstances ...publishers.Publisher) error {
	name := metric.Name()
	if _, ok := srv.jobs[name]; ok {
		return fmt.Errorf("There is already a job for metric '%s'", name)
	}
	srv.jobs[name] = createJob(metric, updateIntervalMinutes, publisherInstances)
	return nil
}

func (srv *MetricService) RunJobsOnce() {
	for _, j := range srv.jobs {
		err := j.initialize()
		if err != nil {
			srv.handler(j.metric.Name(), err)
			return
		}
		j.run(srv.handler)
	}
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
