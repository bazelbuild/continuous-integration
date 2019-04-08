package metrics

import (
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/clients"
	"github.com/fweikert/continuous-integration/metrics/data"
)

type BuildSuccess struct {
	client    *clients.BuildkiteClient
	pipelines []string
	columns   []Column
	builds    int
}

func (bs *BuildSuccess) Name() string {
	return "build_success"
}

func (bs *BuildSuccess) Columns() []Column {
	return bs.columns
}

func (bs *BuildSuccess) Collect() (*data.DataSet, error) {
	result := data.CreateDataSet(GetColumnNames(bs.columns))
	for _, pipeline := range bs.pipelines {
		builds, err := bs.client.GetMostRecentBuilds(pipeline, bs.builds)
		if err != nil {
			return nil, fmt.Errorf("Cannot collect build success statistics for pipeline %s: %v", pipeline, err)
		}
		for _, build := range builds {
			platformStates := make(map[string]*state)
			for _, job := range build.Jobs {
				platform := getPlatfrom(job)
				if platform == "" {
					continue
				}
				mergeState(platformStates, platform, *job.State)
			}
			err := result.AddRow(pipeline, *build.Number, getState(platformStates, "linux"), getState(platformStates, "macos"), getState(platformStates, "windows"), getState(platformStates, "rbe"))
			if err != nil {
				return nil, fmt.Errorf("Failed to add result for build %d: %v", *build.Number, err)
			}
		}
	}
	return result, nil
}

type state struct {
	Name     string
	Priority uint
}

var allStates = getAllStates()

const canceledState = "canceled"
const failedState = "failed"
const passingState = "passed"
const runningState = "running"

func getAllStates() map[string]*state {
	// Our states are different from the Buildkite states (e.g. our "canceled" states includes "canceled" and "canceling").
	/// They also have a priority that defines how multiple states for a given platform are aggregated into a single state.
	states := make(map[string]*state)

	canceled := &state{canceledState, 3}
	states["canceled"] = canceled
	states["canceling"] = canceled

	states["failed"] = &state{failedState, 2}

	running := &state{runningState, 1}
	states["running"] = running
	states["scheduled"] = running
	states["blocked"] = running

	states["passed"] = &state{passingState, 0}

	return states
}

func mergeState(platformStates map[string]*state, platform, buildkiteState string) {
	newState, ok := allStates[buildkiteState]
	if !ok {
		return
	}
	oldState, ok := platformStates[platform]
	if ok {
		if newState.Priority > oldState.Priority {
			platformStates[platform] = newState
		}
	} else {
		platformStates[platform] = newState
	}
}

func getState(platformStates map[string]*state, platform string) string {
	state, ok := platformStates[platform]
	if !ok || state == nil {
		return ""
	}
	return state.Name
}

// CREATE TABLE build_success (pipeline VARCHAR(255), build INT, linux VARCHAR(255), macos VARCHAR(255), windows VARCHAR(255), rbe VARCHAR(255), PRIMARY KEY(pipeline, build));
func CreateBuildSuccess(client *clients.BuildkiteClient, builds int, pipelines ...string) *BuildSuccess {
	columns := []Column{Column{"pipeline", true}, Column{"build", true}, Column{"linux", false}, Column{"macos", false}, Column{"windows", false}, Column{"rbe", false}}
	return &BuildSuccess{client: client, pipelines: pipelines, columns: columns, builds: builds}
}
