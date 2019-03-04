FROM python:alpine

# Latest release from: https://github.com/bazelbuild/buildtools/releases
RUN apk add curl && \
    curl -Lo /usr/local/bin/buildifier https://github.com/bazelbuild/buildtools/releases/download/0.22.0/buildifier && \
    chown root:root /usr/local/bin/buildifier && \
    chmod 0755 /usr/local/bin/buildifier

COPY --chown=root:root buildifier.py /usr/local/bin/buildifier.py

ENTRYPOINT [ "/usr/local/bin/buildifier.py" ]
