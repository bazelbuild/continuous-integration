package clients

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"

	"cloud.google.com/go/storage"
	"google.golang.org/api/iterator"
)

type CloudStorageClient struct {
	client *storage.Client
}

func CreateCloudStorageClient() (*CloudStorageClient, error) {
	ctx := context.Background()
	client, err := storage.NewClient(ctx)
	if err != nil {
		return nil, err
	}
	return &CloudStorageClient{client: client}, nil
}

func (c *CloudStorageClient) ReadAllFiles(bucket, directory string) (*cloudStorageFileIter, error) {
	log.Printf("Reading all files in bucket %s and directory %s", bucket, directory)
	files, err := c.listFiles(bucket, directory)
	if err != nil {
		return nil, fmt.Errorf("Failed to list files in directory %s in bucket %s: %v", directory, bucket, err)
	}

	iter := &cloudStorageFileIter{client: c.client, bucket: bucket, files: files}
	return iter, nil
}

func (c *CloudStorageClient) listFiles(bucket, directory string) ([]string, error) {
	names := make([]string, 0)
	ctx := context.Background()
	q := &storage.Query{Prefix: directory}
	it := c.client.Bucket(bucket).Objects(ctx, q)
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

type cloudStorageFileIter struct {
	client *storage.Client
	bucket string
	files  []string
	pos    int
}

func (iter *cloudStorageFileIter) HasNext() bool {
	return iter.pos < len(iter.files)
}

func (iter *cloudStorageFileIter) Get() (string, []byte, error) {
	pos := iter.pos
	if pos >= len(iter.files) {
		pos = len(iter.files) - 1
	}
	iter.pos += 1

	name := iter.files[pos]
	content, err := iter.readFile(name)
	if err != nil {
		err = fmt.Errorf("Failed to read file %s in bucket %s: %v", name, iter.bucket, err)
	}
	return name, content, err
}

func (iter *cloudStorageFileIter) readFile(object string) ([]byte, error) {
	ctx := context.Background()
	rc, err := iter.client.Bucket(iter.bucket).Object(object).NewReader(ctx)
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
