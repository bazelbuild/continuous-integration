FROM azul/zulu-openjdk-alpine:19
ARG DEPENDENCY=dependency
COPY ${DEPENDENCY}/BOOT-INF/lib /app/lib
COPY ${DEPENDENCY}/META-INF /app/META-INF
COPY ${DEPENDENCY}/BOOT-INF/classes /app
ENTRYPOINT ["java", "-cp", "/app:/app/lib/*", "build.bazel.dashboard.Application"]
