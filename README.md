

# FraudPulse
### Real-Time Fraud Detection Pipeline

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-KRaft-black?style=flat-square&logo=apachekafka)
![Spark](https://img.shields.io/badge/Spark-3.5-E25A1C?style=flat-square&logo=apachespark&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-blue?style=flat-square)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)

A streaming pipeline that ingests financial transactions, scores them for fraud with a trained classifier, and surfaces flagged activity on a live dashboard — built to work through the full anatomy of a real-time ML system: ingestion, distributed processing, model serving, and observability.

</div>

---

##  Overview

FraudPulse combines Kafka, Spark, XGBoost, and MongoDB into a streaming fraud-detection pipeline, with a Streamlit dashboard for reviewing flagged transactions. Below is an honest breakdown of what's built and validated versus what's implemented but still being pushed toward full production load — so the scope is clear at a glance.

##  Architecture

![Architecture](./architecture.png)

```mermaid
graph TD
    subgraph "Ingestion Layer"
        P[Python Producer] -->|Async Streams| K[Kafka Cluster]
    end

    subgraph "Processing Layer"
        K -->|Structured Streaming| S[Spark Consumer]
        S -->|Distributed Inference| X[XGBoost4J-Spark]
    end

    subgraph "Persistence & MLOps"
        S -->|Forensic Storage| M[MongoDB]
        T[Offline Training] -->|Model Registry| MF[MLflow Server]
        MF -->|Model Artifacts| S
    end

    subgraph "Visualization & Monitoring"
        M -->|Live Query| D[Streamlit Dashboard]
        K -->|Metrics| PM[Prometheus]
        S -->|Metrics| PG[Pushgateway]
        PG --> PM
        PM -->|Alerting| G[Grafana]
    end
```

##  Built & validated end-to-end

| Piece | What it does |
|---|---|
|  **Producer → Kafka** | Python producer (`confluent-kafka`) streams transactions from the PaySim dataset into a Kafka topic, using idempotent production to avoid duplicate records on retry |
|  **Model training** | XGBoost classifier trained and evaluated on PaySim, with experiments tracked in `notebooks/` |
|  **MongoDB storage** | Scored transactions persisted for forensic querying |
|  **Streamlit dashboard** | Live view of flagged transactions for investigators |
|  **Containerized services** | Producer, MongoDB, and dashboard run via Docker Compose |

##  Built, in progress toward full validation

- **Spark Structured Streaming (Scala)** — a distributed XGBoost4J inference consumer in `src/spark/` that subscribes to the Kafka topic for real-time scoring. The architecture is in place; the next milestone is load-testing it under sustained streaming throughput and publishing real latency numbers.
- **MLflow / Prometheus / Grafana / ELK** — the full observability and MLOps stack is configured (`docker-compose.mlops.yml`, `docker-compose.observability.yml`); next step is running it long enough to generate real dashboards and alerting data.

## 🛠️ Stack

| Layer | Technology |
|---|---|
| Ingestion | Apache Kafka (KRaft mode), confluent-kafka |
| Processing | Apache Spark Structured Streaming (Scala) |
| ML | XGBoost, XGBoost4J-Spark |
| Storage | MongoDB |
| Dashboard | Streamlit |
| Observability | Prometheus, Grafana, ELK |

##  Quickstart

```bash
docker compose down -v
docker compose build
docker compose up -d
python src/ml/train.py
docker compose restart spark-consumer
```

| Service | URL |
|---|---|
| Dashboard | `localhost:8501` |
| MLflow | `localhost:5000` |
| Spark UI | `localhost:8080` |

##  Structure

```
src/
├── producer/     → Kafka producer
├── spark/        → Scala streaming consumer + inference
├── ml/           → training & feature engineering
└── dashboard/    → Streamlit app
notebooks/        → EDA & model experiments
scripts/, config/ → diagnostics & service config
```

##  Roadmap

- [ ] Load-test the Spark consumer under sustained throughput and publish real numbers
- [ ] Automated tests for producer + dashboard logic
- [ ] Bring the observability stack fully online with live monitoring data

##  Why I built this

I wanted real, working exposure to every layer of a streaming ML system — not just the theory. The ingestion, model training, storage, and dashboard layers all run end-to-end today; the distributed streaming inference layer is what I'm actively taking through load testing next.

