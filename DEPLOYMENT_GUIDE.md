# 📘 FraudPulse : Complete Platform Deployment Guide

This guide details the "Perfect Sequence" to launch the FraudPulse real-time fraud detection platform. Follow these steps exactly to ensure your Spark cluster, Kafka nodes, and AI models are perfectly synchronized.

---

## 🏗️ 1. Prerequisites
*   **System**: Windows 10/11 with WSL2 enabled.
*   **Docker**: Docker Desktop (ensure Linux containers mode is active).
*   **Python**: Version 3.11+ (for the ML training script).
*   **Data**: Ensure `data/paysim.csv` exists in your project root.

---

## 🧹 2. Phase 1: Total Environment Reset
Always start with a clean slate to avoid "stale" Kafka metadata or Spark checkpoints.

```powershell
docker compose down -v
```
*   **Why?**: `-v` wipes the volumes. This ensures Kafka starts a fresh leader election and MongoDB starts empty.

---

## ⚙️ 3. Phase 2: Building the Unified Engine
We use a **Unified Spark Image** to ensure that the Master, Worker, and Consumer all have the exact same Scala version and the `libgomp1` library (required for XGBoost).

```powershell
docker compose build
```
*   **Why?**: This builds the custom Dockerfile in `src/spark` which contains the GNU OpenMP library.

---

## 🚀 4. Phase 3: Launching Infrastructure
We combine the core infrastructure with the MLOps (MLflow) tracking server.

```powershell
docker compose -f docker-compose.yml -f docker-compose.mlops.yml up -d
```
*   **Why?**: This launches:
    *   **Kafka Cluster (3 Nodes)**: Real-time message brokering.
    *   **MongoDB**: Forensic data storage.
    *   **MLflow**: Experiment and model tracking server.
    *   **Spark Cluster**: The distributed computation engine.

---

## 🧠 5. Phase 4: AI Model Training
The system needs a trained model before it can detect fraud.

### Step A: Wait for MLflow (⏳ 30s)
Wait 30 seconds for MLflow to finish its internal database migration. Check `http://localhost:5000` in your browser.

### Step B: Run Training
```powershell
# Ensure you are in your python venv
python src/ml/train.py
```
*   **What it does**: 
    1. Trains an XGBoost model on the `paysim.csv` dataset.
    2. Logs the run to MLflow (metrics like F1-Score, Precision).
    3. Saves `models/fraud_model.json` (the file Spark will load).

---

## 🏎️ 6. Phase 5: Starting the Detection Engine
Now that the model file exists, let's start the processing.

```powershell
docker compose restart spark-consumer
```
*   **Why?**: The Spark Consumer loads the model **at startup**. Since we launched it *before* training, we must restart it to pick up the new `fraud_model.json`.

---

## 🛡️ 7. Phase 6: System Health Check
Run the automated diagnostic tool to verify every component:

```powershell
.\scripts\check_status.ps1
```
*   **Success Indicator**: 6/6 Successful.

---

## 📊 8. Phase 7: Real-Time Verification
1.  **Producer Logs**: Check data production (`docker logs producer --tail 20`). Look for `🚀 Produced...` messages.
2.  **Spark Logs**: Check processing (`docker logs spark-consumer --tail 100`). Look for `Writing batch X to MongoDB`.
3.  **Dashboard**: Open [http://localhost:8501](http://localhost:8501). Watch the "Live Fraud Alerts" appear in red!

---

## 🆘 Troubleshooting Tips

| Error | Fix |
| :--- | :--- |
| **`UnsatisfiedLinkError` (XGBoost)** | You missed the `docker compose build` step. Rebuild the Spark image. |
| **`InvalidClassException` (Spark)** | Ensure all nodes are using the same Bitnami-based image. |
| **`Connection to node 1 could not be established`** | Kafka is still starting. Wait 30s for the KRaft election to finish. |
| **Empty Dashboard** | Check MongoDB count: `docker exec mongodb mongosh fraud_db --eval "db.transactions.countDocuments()"` |

---

**Built with ❤️ by your AI Pair Programmer for the Final Project Jury.**
