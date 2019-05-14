package metrics

import (
	"context"
	"fmt"

	"github.com/fweikert/continuous-integration/metrics/data"
	"github.com/google/go-github/github"
	"golang.org/x/oauth2"
)

type ReleaseDownloads struct {
	org          string
	repo         string
	client       *github.Client
	minSizeBytes int
	columns      []Column
}

func (rd *ReleaseDownloads) Name() string {
	return "release_downloads"
}

func (rd *ReleaseDownloads) Columns() []Column {
	return rd.columns
}

func (rd *ReleaseDownloads) Collect() (data.DataSet, error) {
	all_releases, err := rd.getReleases()
	if err != nil {
		return nil, fmt.Errorf("Failed to get releases for %s/%s: %v", rd.org, rd.repo, err)
	}

	result := data.CreateDataSet(GetColumnNames(rd.columns))
	for _, release := range all_releases {
		for _, asset := range release.Assets {
			if *asset.Size >= rd.minSizeBytes {
				result.AddRow(*release.TagName, *asset.Name, *asset.DownloadCount)
			}
		}
	}
	return result, nil
}

func (rd *ReleaseDownloads) getReleases() ([]*github.RepositoryRelease, error) {
	all_releases := make([]*github.RepositoryRelease, 0)
	ctx := context.Background()
	opt := github.ListOptions{Page: 1, PerPage: 100}
	currPage := 1
	lastPage := 1

	for currPage <= lastPage {
		releases, response, err := rd.client.Repositories.ListReleases(ctx, rd.org, rd.repo, &opt)
		if err != nil {
			return nil, fmt.Errorf("Could not get page %d: %v", currPage, err)
		}

		all_releases = append(all_releases, releases...)
		currPage += 1
		opt.Page = currPage
		lastPage = response.LastPage
	}

	return all_releases, nil
}

// CREATE TABLE release_downloads (release_name VARCHAR(255), artifact VARCHAR(255), downloads INT, PRIMARY KEY(release_name, artifact));
func CreateReleaseDownloads(org string, repo string, token string, minSizeBytes int) *ReleaseDownloads {
	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: token},
	)
	tc := oauth2.NewClient(ctx, ts)

	client := github.NewClient(tc)
	columns := []Column{Column{"release_name", true}, Column{"artifact", true}, Column{"downloads", false}}
	return &ReleaseDownloads{org: org, repo: repo, client: client, minSizeBytes: minSizeBytes, columns: columns}
}
