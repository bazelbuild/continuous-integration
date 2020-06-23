FROM nginx:alpine AS bazel-slack-inviter-slackin

ADD nginx.conf /etc/nginx/nginx.conf

ADD run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
