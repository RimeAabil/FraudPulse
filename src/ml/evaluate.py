import os
import logging
import pandas as pd
import mlflow
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    try:
        mlflow.set_tracking_uri(mlflow_uri)
    except Exception as e:
        logger.error(f"MLflow setup failed: {e}")

    logger.info("Loading test data...")
    try:
        data_dir = 'data/processed' if os.path.exists('data') else '../../data/processed'
        X_test = pd.read_csv(os.path.join(data_dir, 'X_test.csv'))
        y_test = pd.read_csv(os.path.join(data_dir, 'y_test.csv')).squeeze()
    except FileNotFoundError:
        logger.error("Test data not found. Run train.py first.")
        return
        
    logger.info("Loading model from MLflow Registry...")
    model_name = os.environ.get("MODEL_NAME", "FraudPulse-XGBoost")
    try:
        # Load the latest production or latest version
        model = mlflow.xgboost.load_model(f"models:/{model_name}/latest")
    except Exception as e:
        logger.error(f"Model not found in MLflow ({e}). Make sure train.py has run successfully and registered the model.")
        return
        
    logger.info("Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_prob)
    f1 = f1_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    
    logger.info(f"AUC-ROC: {auc:.4f}")
    logger.info(f"F1 Score: {f1:.4f}")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall: {recall:.4f}")
    logger.info(f"Confusion Matrix:\n{cm}")
    
    logger.info("Evaluation complete.")

if __name__ == '__main__':
    main()
