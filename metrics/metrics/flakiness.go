package metrics

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"regexp"
	"strconv"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type Flakiness struct {
	client    *clients.GcsClient
	columns   []Column
	gcsBucket string
	gcsSuffix string
	pipelines []*data.PipelineID
}

func (f *Flakiness) Name() string {
	return "flakiness"
}

func (f *Flakiness) Columns() []Column {
	return f.columns
}

func (f *Flakiness) Collect() (data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(f.columns))
	for _, pipeline := range f.pipelines {
		gcsPath := f.gcsSuffix + pipeline.Slug
		contents, err := f.client.ReadAllFiles(f.gcsBucket, gcsPath)
		if err != nil {
			return nil, err
		}
		if len(contents) == 0 {
			log.Printf("There is no flakiness data for pipeline %s in GCS location %s/%s", pipeline, f.gcsBucket, gcsPath)
			continue
		}

		for fileName, content := range contents {
			build, err := getBuildNumber(fileName)
			if err != nil {
				return nil, fmt.Errorf("Invalid flaky data file %s in %s/%s: %v", fileName, f.gcsBucket, gcsPath, err)
			}

			messages, err := getFlakyMessages(content)
			if err != nil {
				return nil, fmt.Errorf("Failed to parse flaky data file %s in %s/%s: %v", fileName, f.gcsBucket, gcsPath, err)
			}

			for _, msg := range messages {
				err = result.AddRow(pipeline.Org, pipeline.Slug, build, msg.ID.Summary.Label, len(msg.Summary.Passed), len(msg.Summary.Failed))
				if err != nil {
					return nil, fmt.Errorf("Failed to add flakiness data for build #%d of pipeline %s: %v", build, pipeline, err)
				}
			}
		}
	}
	return result, nil
}

func getFlakyMessages(content []byte) ([]message, error) {
	messages := make([]message, 0)
	for _, line := range bytes.Split(content, []byte("\n")) {
		if len(line) == 0 {
			continue
		}

		var msg message
		err := json.Unmarshal([]byte(line), &msg)
		if err != nil {
			return nil, fmt.Errorf("JSON parse error: %v. Line:\n%s", err, line)
		}
		if msg.Summary.Status == "FLAKY" {
			messages = append(messages, msg)
		}
	}
	return messages, nil
}

func getBuildNumber(fileName string) (int, error) {
	re := regexp.MustCompile(`(\d+).json$`)
	matches := re.FindStringSubmatch(fileName)
	if len(matches) == 2 {
		if build, err := strconv.Atoi(matches[1]); err == nil {
			return build, nil
		}
	}
	return 0, fmt.Errorf("Flakiness data file names must be 'some_path/<build_number.json>. Invalid given value: %s", fileName)
}

type message struct {
	ID struct {
		Summary struct {
			Label string `json:"label"`
		} `json:"testSummary"`
	}
	Summary struct {
		Passed []struct{ uri string } `json:"passed"`
		Failed []struct{ uri string } `json:"failed"`
		Status string                 `json:"overallStatus"`
	} `json:"testSummary"`
}

// CREATE TABLE flakiness (org VARCHAR(255), pipeline VARCHAR(255), build INT, target VARCHAR(255), passed_count INT, failed_count INT, PRIMARY KEY(org, pipeline, build, target));
func CreateFlakiness(client *clients.GcsClient, gcsBucket, gcsBasePath string, pipelines ...*data.PipelineID) *Flakiness {
	columns := []Column{Column{"org", true}, Column{"pipeline", true}, Column{"build", true}, Column{"target", true}, Column{"passed_count", false}, Column{"failed_count", false}}
	gcsSuffix := gcsBasePath
	if !strings.HasSuffix(gcsBasePath, "/") {
		gcsSuffix = gcsBasePath + "/"
	}
	return &Flakiness{client: client, columns: columns, gcsBucket: gcsBucket, gcsSuffix: gcsSuffix, pipelines: pipelines}
}
