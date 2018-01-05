# The http-redir VM

We use a small VM on GCE to redirect certain HTTP requests to canonical destinations (e.g. \*.bazel.io -> \*.bazel.build).

## Installation

 - Create a new CentOS 7 VM on GCE
 - Update everything: `yum upgrade`
 - Install nginx: `yum install nginx`
 - Configure nginx:

```
cat > /etc/nginx/nginx.conf <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
  worker_connections 1024;
}

http {
  include             /etc/nginx/mime.types;
  default_type        application/octet-stream;

  # Redirect variations of the main website URL to the canonical one.
  server {
    listen 80;
    server_name bazel.build www.bazel.build bazel.io www.bazel.io;
    rewrite ^ https://bazel.build$request_uri permanent;
  }

  # Redirect http:// to https:// and *.bazel.io to *.bazel.build.
  server {
    listen 80;
    server_name ~^(?<subdomain>.+)\.bazel\.(?<tld>.+)$;
    rewrite ^ https://$subdomain.bazel.build$request_uri permanent;
  }

  # Catch-all default server that just returns an error.
  server {
    listen 80 default_server;
    server_name _;
    add_header Content-Type text/plain;
    return 200 "Bazel Redirection Service";
  }
}
EOF
```
 - Enable the nginx service: `systemctl enable nginx`
 - Start the nginx service: `systemctl start nginx`
