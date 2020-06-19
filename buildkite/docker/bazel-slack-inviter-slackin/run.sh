#!/usr/bin/env sh

sed -i "s|\${PORT}|${PORT}|" /etc/nginx/nginx.conf
exec nginx -g 'daemon off;'
