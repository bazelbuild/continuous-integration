package clients

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"

	"cloud.google.com/go/storage"
	"google.golang.org/api/iterator"
)

type GcsClient struct {
	client *storage.Client
}

func CreateGcsClient() (*GcsClient, error) {
	ctx := context.Background()
	client, err := storage.NewClient(ctx)
	if err != nil {
		return nil, err
	}
	return &GcsClient{client: client}, nil
}

func (g *GcsClient) ReadAllFiles(bucket, directory string) (map[string][]byte, error) {
	log.Printf("Reading all files in bucket %s and directory %s", bucket, directory)
	files, err := g.listFiles(bucket, directory)
	if err != nil {
		return nil, fmt.Errorf("Failed to list files in directory %s in bucket %s: %v", directory, bucket, err)
	}

	data := make(map[string][]byte)
	for _, f := range files {
		content, err := g.readFile(bucket, f)
		if err != nil {
			return nil, fmt.Errorf("Failed to read file %s in bucket %s: %v", f, bucket, err)
		}
		data[f] = content
	}
	return data, nil
}

func (g *GcsClient) listFiles(bucket, directory string) ([]string, error) {
	names := make([]string, 0)
	ctx := context.Background()
	q := &storage.Query{Prefix: directory}
	it := g.client.Bucket(bucket).Objects(ctx, q)
	for {
		attrs, err := it.Next()
		if err == iterator.Done {
			break
		} else if err != nil {
			return nil, err
		}
		names = append(names, attrs.Name)
	}
	return names, nil
}

func (g *GcsClient) readFile(bucket, object string) ([]byte, error) {
	ctx := context.Background()
	rc, err := g.client.Bucket(bucket).Object(object).NewReader(ctx)
	if err != nil {
		return nil, err
	}
	defer rc.Close()

	data, err := ioutil.ReadAll(rc)
	if err != nil {
		return nil, err
	}
	return data, nil
}
