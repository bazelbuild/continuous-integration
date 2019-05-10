package metrics

import (
	"fmt"
	"strings"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type Flakiness struct {
	client    *clients.GcsClient
	columns   []Column
	gcsBucket string
	gcsSuffix string
	pipelines []string
}

func (f *Flakiness) Name() string {
	return "flakiness"
}

func (f *Flakiness) Columns() []Column {
	return f.columns
}

func (f *Flakiness) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(f.columns))
	for _, pipeline := range f.pipelines {
		contents, err := f.client.ReadAllFiles(f.gcsBucket, f.gcsSuffix+pipeline)
		if err != nil {
			return nil, err
		}
		fmt.Println(pipeline)
		for k, _ := range contents {
			fmt.Printf("\t%s\n", k)
		}
		/*		err = result.AddRow(row[0], row[1], row[4], row[5], false)
				if err != nil {
					return nil, fmt.Errorf("Pipeline %s: Failed to add result for job %s of build %s: %v", str[0], str[2], str[1], err)
				}*/
	}
	return result, nil
}

// TODO(fweikert): use "build INT" once we store build numbers instead of build IDs.
// CREATE TABLE flakiness (pipeline VARCHAR(255), build VARCHAR(255), target VARCHAR(255), passed_count INT, failed_count INT, PRIMARY KEY(pipeline, build, target));
func CreateFlakiness(client *clients.GcsClient, gcsBucket, gcsBasePath string, pipelines ...string) *Flakiness {
	columns := []Column{Column{"pipeline", true}, Column{"build", true}, Column{"target", true}, Column{"passed_count", false}, Column{"failed_count", false}}
	gcsSuffix := gcsBasePath
	if !strings.HasSuffix(gcsBasePath, "/") {
		gcsSuffix = gcsBasePath + "/"
	}
	return &Flakiness{client: client, columns: columns, gcsBucket: gcsBucket, gcsSuffix: gcsSuffix, pipelines: pipelines}
}
