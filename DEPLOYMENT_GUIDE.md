# FraudPulse: Complete Platform Deployment Guide

This guide details the exact sequence required to initialize and operate the FraudPulse real-time fraud detection platform. Follow these steps sequentially to ensure total synchronization between the Kafka broker cluster, the Spark distributed engine, and the MLOps tracking layers.

---

## 1. Prerequisites
- **Operating System**: Windows 10/11 with WSL2 (Ubuntu 22.04 recommended).
- **Runtime**: Docker Desktop with Linux Containers enabled.
- **Python Environment**: Python 3.11+ with required dependencies (`pip install -r requirements.txt`).
- **Data Assets**: Ensure the `data/paysim.csv` dataset is present in the project root.

---

## 2. Phase 1: Environment Sanitation
To prevent metadata conflicts in the Kafka KRaft cluster or stale Spark checkpoints, perform a total volume reset.

```powershell
docker compose down -v
```
*Note: The -v flag is critical as it removes the named volumes for MongoDB and Kafka, ensuring a clean state.*

---

## 3. Phase 2: Building the Unified Spark Cluster
The platform uses a custom-built Spark image to ensure binary compatibility (Scala 2.12) and the presence of native libraries (libgomp1) required for XGBoost distributed inference.

```powershell
docker compose build
```

---

## 4. Phase 3: Infrastructure Orchestration
Launch the complete platform, including the core processing logic, the MLOps tracking server, and the observability suite.

```powershell
docker compose -f docker-compose.yml -f docker-compose.mlops.yml -f docker-compose.observability.yml up -d
```
*Infrastructure components launched:*
- **Distributed Ingestion**: 3-Node Kafka Cluster (Replication Factor: 3).
- **Processing Engine**: Spark Master and Distributed Workers.
- **Storage Layer**: MongoDB Document Store.
- **MLOps Layer**: MLflow Tracking Server.
- **Observability Layer**: Prometheus, Grafana, and the Elastic Stack (ELK).

---

## 5. Phase 4: Machine Learning Lifecycle (Training)
The detection engine requires a serialized model file. 

### Step A: MLflow Initialization
Wait approximately 30 seconds for the MLflow server to complete its database migrations. Verify access at http://localhost:5000.

### Step B: Model Generation
```powershell
python src/ml/train.py
```
*Outcome*: This script performs feature engineering, trains an XGBoost classifier, logs metrics to MLflow, and exports the `models/fraud_model.json` artifact for Spark consumption.

---

## 6. Phase 5: Starting the Detection Engine
Restart the Spark Consumer to ensure it identifies the newly generated model artifacts.

```powershell
docker compose restart spark-consumer
```

---

## 7. Phase 6: System Audit and Verification
Execute the automated diagnostic tool to verify the connectivity and health of all components.

```powershell
.\scripts\check_status.ps1
```

---

## Technical Access Matrix

| Service | Port | Description |
| :--- | :--- | :--- |
| **Forensic Dashboard** | 8501 | Real-time Streamlit UI for investigators. |
| **MLOps Tracker** | 5000 | MLflow UI for experiment tracking and model registry. |
| **Engineering Hub** | 3000 | Grafana dashboards for system health and consumer lag. |
| **Log Analytics** | 5601 | Kibana interface for searching distributed logs. |
| **Metrics Store** | 9090 | Prometheus time-series database. |
| **Spark Master** | 8080 | Spark cluster resource management UI. |

---

## Troubleshooting Procedures

| Symptom | Resolution |
| :--- | :--- |
| **UnsatisfiedLinkError (XGBoost)** | This indicates a missing libgomp1 library on the Spark Workers. Ensure Phase 2 (build) was executed correctly. |
| **InvalidClassException (Serialization)** | Indicates a Spark version mismatch. Ensure all nodes are running the unified Bitnami-based custom image. |
| **Empty Dashboard Alerts** | Verify the Spark processing status: `docker logs spark-consumer --tail 100`. Ensure the Producer is active. |

---

**Document Revision: 2026.04.05 - Production Ready.**
