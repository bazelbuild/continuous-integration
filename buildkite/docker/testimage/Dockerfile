FROM busybox:stable AS testimage-base
RUN mkdir /tmp/base

FROM testimage-base AS testimage-target1
RUN mkdir /tmp/base/target1

FROM testimage-base AS testimage-target2-nojdk
RUN mkdir /tmp/base/target2

FROM testimage-target2-nojdk AS testimage-target3
RUN mkdir /tmp/base/target3
