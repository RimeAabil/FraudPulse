# 📘 FraudPulse : The "Perfect Run" Operations Guide

This guide ensures you can deploy the entire platform from scratch with 100% confidence. Follow these steps in order.

---

## 🏗️ 1. The "Cold Start" Sequence
If you want to reset everything and start fresh, run these commands.

### Step A: Clean slate
```powershell
docker compose down -v
```
*   **What it does:** Stops all containers and **wipes the volumes** (database, Kafka data, Spark checkpoints).
*   **⚠️ Danger:** This deletes all previously processed transactions. Use this only for a fresh demo.

### Step B: Launch Infrastructure (Core + MLOps)
```powershell
docker compose -f docker-compose.yml -f docker-compose.mlops.yml up -d
```
*   **What it does:** Launches Kafka, MongoDB, Spark Cluster, MLflow, and the Dashboard.
*   **⏳ Wait Time:** 60-90 seconds.
*   **⚠️ Trouble:** If it says `network not found`, I fixed that in the YAML. If a container stays in `starting`, check `docker logs <name>`.

---

## 🧠 2. The Training Phase (AI/ML)
You must train the model *before* the Spark consumer can successfully detect fraud.

### Step A: Verify MLflow is alive
Open [http://localhost:5000](http://localhost:5000) in your browser. 
*   **Success:** You see the MLflow UI.

### Step B: Run Training
```powershell
# Ensure your venv is active
python src/ml/train.py
```
*   **What it does:** Reads the dataset, trains an XGBoost model, logs metrics to MLflow, and saves `fraud_model.json` to the `models/` folder.
*   **⚠️ Trouble:** If it fails to connect to MLflow, ensured Docker is running. The local model files will still be saved.

---

## 🌊 3. The Streaming Phase (Data Flow)
Now that the model exists, we can start the processing engine.

### Step A: Restart the Consumer
```powershell
docker compose restart spark-consumer
```
*   **Why?** Spark needs to load the `fraud_model.json` at startup. Since we launched it *before* training, we must restart it to pick up the new model.
*   **🔍 Check:** `docker logs spark-consumer --tail 50`. Look for `Query started`.

### Step B: Start the Producer (The "Data Tap")
```powershell
docker compose up -d --build producer
```
*   **What it does:** Starts the Python script that reads the `paysim.csv` and streams it into Kafka.
*   **🔍 Check:** `docker logs producer --tail 20`. You should see `Produced 100 events...`.

---

## 📊 4. The Dashboard (Forensics)
Open [http://localhost:8501](http://localhost:8501).

*   **Initial text:** "// INITIALIZING NETWORK STREAM..." (Normal for the first 30 seconds).
*   **Success:** Live alerts start popping up in Red (Fraud) or Blue (Legitimate).

---

## 🛡️ 5. Troubleshooting Cheat Sheet

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| **Empty Dashboard** | Spark Consumer is dead | `docker compose restart spark-consumer` |
| **Spark version error** | Version mismatch | `docker compose build spark-consumer` (Fixed in Dockerfile) |
| **Kafka Connection Error** | Kafka not ready yet | Wait 30s. Kafka KRaft mode takes time to elect a leader. |
| **Port 5000 Conflict** | AirPlay or other app | Check if anything else is on port 5000 (usually `AirPlay Receiver` on macOS/Win). |

---

## ✅ 6. Automated Health Check
Run my diagnostic script to verify everything:
```powershell
.\scripts\check_status.ps1
```
