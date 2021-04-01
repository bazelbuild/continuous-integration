FROM python:alpine

COPY --chown=root:root buildifier.py /usr/local/bin/buildifier.py

RUN chmod 0755 /usr/local/bin/buildifier.py

ENTRYPOINT [ "/usr/local/bin/buildifier.py" ]
