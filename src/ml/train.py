import os
import logging
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import mlflow
import mlflow.xgboost

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Setup MLflow
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    try:
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment(os.environ.get("MLFLOW_EXPERIMENT_NAME", "FraudPulse-XGBoost"))
        logger.info(f"Connected to MLflow at {mlflow_uri}")
    except Exception as e:
        logger.error(f"Failed to connect to MLflow: {e}")

    data_path = 'data/paysim.csv'
    if not os.path.exists(data_path):
        data_path = '../../data/paysim.csv'
        if not os.path.exists(data_path):
            logger.error(f"Dataset {data_path} not found.")
            return

    logger.info("Loading dataset...")
    df = pd.read_csv(data_path)

    logger.info("Engineering features...")
    df['balance_drained'] = (df['newbalanceOrig'] == 0).astype(int)
    df['dest_balance_unchanged'] = (df['newbalanceDest'] == df['oldbalanceDest']).astype(int)
    df['amount_to_balance_ratio'] = df['amount'] / (df['oldbalanceOrg'] + 1)
    df['hour_of_day'] = df['step'] % 24
    df['is_transfer_or_cashout'] = df['type'].isin(['TRANSFER', 'CASH_OUT']).astype(int)

    type_mapping = {t: i for i, t in enumerate(df['type'].unique())}
    df['type_encoded'] = df['type'].map(type_mapping)

    feature_cols = [
        'amount', 'oldbalanceOrg', 'newbalanceOrig', 'oldbalanceDest', 'newbalanceDest',
        'balance_drained', 'dest_balance_unchanged', 'amount_to_balance_ratio', 
        'hour_of_day', 'is_transfer_or_cashout', 'type_encoded'
    ]

    X = df[feature_cols]
    y = df['isFraud']

    logger.info("Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Save test dataset for validation
    data_dir = 'data/processed' if os.path.exists('data') else '../../data/processed'
    os.makedirs(data_dir, exist_ok=True)
    X_test.to_csv(os.path.join(data_dir, 'X_test.csv'), index=False)
    y_test.to_csv(os.path.join(data_dir, 'y_test.csv'), index=False)
    
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    
    with mlflow.start_run(run_name="xgb-training"):
        mlflow.log_params({
            "n_estimators": 100,
            "max_depth": 6,
            "scale_pos_weight": scale_pos_weight,
            "random_state": 42
        })

        logger.info("Training XGBoost model...")
        model = xgb.XGBClassifier(
            scale_pos_weight=scale_pos_weight,
            eval_metric='logloss',
            random_state=42,
            n_estimators=100,
            max_depth=6
        )
        model.fit(X_train, y_train)

        # Evaluate immediately to log metrics
        from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        metrics = {
            "auc_roc": roc_auc_score(y_test, y_prob),
            "f1": f1_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred)
        }
        mlflow.log_metrics(metrics)
        logger.info(f"Model Metrics: {metrics}")

        # Register Model to MLflow
        model_name = os.environ.get("MODEL_NAME", "FraudPulse-XGBoost")
        try:
            mlflow.xgboost.log_model(model, "fraud_model", registered_model_name=model_name)
            logger.info(f"Model registered to MLflow as {model_name}")
        except Exception as e:
            logger.error(f"Could not register model in MLflow: {e}")

        # Save backwards compatible files for local Spark Scala consumer
        model_dir = 'models' if os.path.exists('models') or os.path.exists('data') else '../../models'
        os.makedirs(model_dir, exist_ok=True)
        model.save_model(os.path.join(model_dir, 'fraud_model.json'))
        
        import json
        with open(os.path.join(model_dir, 'feature_cols.json'), 'w') as f:
            json.dump({'feature_cols': feature_cols, 'type_mapping': type_mapping}, f)

        logger.info("Training complete.")

if __name__ == '__main__':
    main()
