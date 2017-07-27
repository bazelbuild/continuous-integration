#!/usr/bin/env bash
# Copyright 2017 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Setup scripts for the remote cache

cat > /root/nginx.conf <<'EOF'

user ci;
worker_processes auto;
pid /run/nginx.pid;

events {
  worker_connections 10000;
  multi_accept on;
}

http {
  sendfile on;
  tcp_nopush on;
  tcp_nodelay on;
  types_hash_max_size 2048;
  default_type application/octet-stream;

  access_log /var/log/nginx/access.log;
  error_log /var/log/nginx/error.log;

  server {
    listen 80;
    client_max_body_size 0;

    location / {
      root /var/cas/cache;
      client_body_temp_path /var/cas/temp;
      dav_methods PUT;
      create_full_put_path off;
      dav_access user:rw group:rw all:r;
    }
  }
}

EOF

cat > /root/purge-cache.py <<'EOF'

from inotify_simple import INotify, flags
from os import close, listdir, unlink, stat
from re import findall
from subprocess import check_output
from sys import argv
from time import time

def folder_size(path):
  stdout = check_output(["du", "-bs", path])
  res = findall("^[0-9]+", stdout)
  return int(res[0])

def purge_files(dir_path, trigger_size, purge_target=0.7):
  """Watch dir_path for files to be added. If the folder size
  exceeds trigger_size, delete files until its size is lte
  trigger_size * purge_target.

  Arguments:
  dir_path -- path to directory to monitor.
  trigger_size -- directory size in bytes that when exceeded
                  triggers purging.
  purge_target -- to what fraction of size the directory
                  contents should be reduced (default 0.7)
  """
  inotify = INotify()
  watch_flags = flags.CREATE | flags.MOVED_TO
  wd = inotify.add_watch(dir_path, watch_flags)
  try:
    while True:
      actual_size_bytes = folder_size(dir_path)
      if actual_size_bytes > trigger_size:
        target_size_bytes = trigger_size * purge_target;

        files = [dir_path + "/" + name for name in listdir(dir_path)]
        files_stat = [(f, stat(f)) for f in files]

        deleted_size_bytes = actual_size_bytes
        deleted_files_count = 0
        start = time()
        for filepath, st in sorted(files_stat, lambda _,t: int(t[1].st_atime)):
         try:
            unlink(filepath)
            deleted_files_count += 1
            deleted_size_bytes -= st.st_size
            if deleted_size_bytes < target_size_bytes:
              break
         except OSError:
            print "Failed to delete file {}".format(filepath)
        end = time()

        print "Deleted {} files, totalling {} bytes in {} seconds".format(deleted_files_count,
                                                                          actual_size_bytes - deleted_size_bytes,
                                                                          end - start)

      # Block until one or more files were created/moved to the folder. We are not
      # interested in the particular file(s).
      inotify.read()
  except KeyboardInterrupt:
    inotify.close()

if __name__ == "__main__":
  purge_files(argv[1], int(argv[2]))

EOF

apt-get -y update
apt-get -y install nginx python-pip
pip install inotify_simple enum34

rm -rf /var/cas

mkdir -p /var/cas/temp
mkdir -p /var/cas/cache
chown -R ci:ci /var/cas

nginx -s quit || true
nginx -c /root/nginx.conf

max_cache_size=$((400 * 1024 * 1024 * 1024))
echo "python /root/purge-cache.py /var/cas/cache ${max_cache_size}" | batch

