FROM sbtscala/scala-sbt:eclipse-temurin-jammy-17.0.10_7_1.10.1_2.12.19 AS builder
WORKDIR /build
COPY build.sbt .
COPY src ./src
RUN sbt package

FROM bitnamilegacy/spark:3.5.1
USER root
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /build/target/scala-2.12/fraudpulse_2.12-1.0.jar /app/
RUN chown -R 1001:1001 /app /tmp/checkpoints || true
USER 1001
