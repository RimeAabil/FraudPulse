import os
import random
import logging
import asyncio
from fastapi import FastAPI, HTTPException
import mlflow.xgboost
import pandas as pd
from prometheus_client import make_asgi_app, Histogram, Counter

from schemas import TransactionSchema, PredictionResponse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="FraudPulse Model Server", version="2.4.0")

# Prometheus Metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

PREDICTION_LATENCY = Histogram('model_prediction_latency_seconds', 'Time taken to predict fraud', ['variant'])
PREDICTION_REQUESTS = Counter('model_prediction_requests_total', 'Total number of prediction requests', ['variant'])

# Global model state
champion_model = None
challenger_model = None

def load_models():
    global champion_model, challenger_model
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    model_name = os.environ.get("MODEL_NAME", "FraudPulse-XGBoost")
    try:
        mlflow.set_tracking_uri(mlflow_uri)
        # In a real environment, load Production and Staging tags
        champion_model = mlflow.xgboost.load_model(f"models:/{model_name}/latest")
        logger.info("Loaded champion model.")
    except Exception as e:
        logger.warning(f"Could not load models from MLflow: {e}")
        # Graceful degradation logic would go here

@app.on_event("startup")
async def startup_event():
    # Attempt to load model asynchronously or in background to not block startup
    # For now we'll do an initial synchronous load
    load_models()

def extract_features(tx: TransactionSchema):
    # Feature engineering (must match train.py)
    balance_drained = 1 if tx.newbalanceOrig == 0 else 0
    dest_balance_unchanged = 1 if tx.newbalanceDest == tx.oldbalanceDest else 0
    amount_to_balance_ratio = tx.amount / (tx.oldbalanceOrg + 1)
    hour_of_day = tx.step % 24
    is_transfer_or_cashout = 1 if tx.type in ['TRANSFER', 'CASH_OUT'] else 0
    
    type_mapping = {'PAYMENT': 0, 'TRANSFER': 1, 'CASH_OUT': 2, 'DEBIT': 3, 'CASH_IN': 4}
    type_encoded = type_mapping.get(tx.type, -1)
    
    return pd.DataFrame([{
        'amount': tx.amount,
        'oldbalanceOrg': tx.oldbalanceOrg,
        'newbalanceOrig': tx.newbalanceOrig,
        'oldbalanceDest': tx.oldbalanceDest,
        'newbalanceDest': tx.newbalanceDest,
        'balance_drained': balance_drained,
        'dest_balance_unchanged': dest_balance_unchanged,
        'amount_to_balance_ratio': amount_to_balance_ratio,
        'hour_of_day': hour_of_day,
        'is_transfer_or_cashout': is_transfer_or_cashout,
        'type_encoded': type_encoded
    }])

@app.post("/predict", response_model=PredictionResponse)
async def predict(transaction: TransactionSchema):
    if champion_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
        
    ab_fraction = float(os.environ.get("AB_TEST_CHALLENGER_FRACTION", "0.0"))
    
    # A/B Routing
    variant = "champion"
    active_model = champion_model
    
    if challenger_model is not None and random.random() < ab_fraction:
        variant = "challenger"
        active_model = challenger_model

    PREDICTION_REQUESTS.labels(variant=variant).inc()

    with PREDICTION_LATENCY.labels(variant=variant).time():
        features = extract_features(transaction)
        try:
            probability = float(active_model.predict_proba(features)[0][1])
            return PredictionResponse(
                fraud_probability=probability,
                model_version="latest", 
                variant=variant
            )
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise HTTPException(status_code=500, detail="Prediction error")

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "champion_loaded": champion_model is not None,
        "challenger_loaded": challenger_model is not None
    }
