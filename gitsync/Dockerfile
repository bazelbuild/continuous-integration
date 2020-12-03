FROM ubuntu:18.04

# https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN apt-get update \
 && apt-get install -y \
        curl \
        git \
        lsb-release \
        openssh-client \
        gnupg2 \
 && export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" \
 && echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
 && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
 && apt-get update \
 && apt-get install -y google-cloud-sdk \
 && gcloud config set core/disable_usage_reporting true \
 && gcloud config set component_manager/disable_update_check true \
 && gcloud --version \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --user-group --shell /bin/bash gitsync

RUN mkdir -p /home/gitsync/.ssh
COPY ssh_config /home/gitsync/.ssh/config
COPY known_hosts /home/gitsync/.ssh/known_hosts
COPY gitsync.sh /home/gitsync/gitsync.sh
RUN chown -R gitsync:gitsync /home/gitsync

USER gitsync
RUN git config --global http.cookiefile /home/gitsync/.gitcookies

WORKDIR /home/gitsync
ENTRYPOINT [ "/home/gitsync/gitsync.sh" ]
