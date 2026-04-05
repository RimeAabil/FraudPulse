import os
import logging
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_drift(reference_data_path, current_data_path):
    try:
        logger.info("Loading reference and current data for drift detection...")
        ref_df = pd.read_csv(reference_data_path)
        cur_df = pd.read_csv(current_data_path)
        
        # Only take features we care about (exclude targets)
        if 'isFraud' in ref_df.columns: ref_df = ref_df.drop(columns=['isFraud', 'isFlaggedFraud'])
        if 'isFraud' in cur_df.columns: cur_df = cur_df.drop(columns=['isFraud', 'isFlaggedFraud'])

        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=ref_df, current_data=cur_df)
        
        report_dict = report.as_dict()
        drift_detected = report_dict["metrics"][0]["result"]["dataset_drift"]
        share_of_drifted_features = report_dict["metrics"][0]["result"]["share_of_drifted_columns"]
        
        logger.info(f"Drift Detected: {drift_detected}")
        logger.info(f"Share of Drifted Features: {share_of_drifted_features:.2%}")
        
        if drift_detected:
            logger.warning("DATA DRIFT DETECTED! Suggest triggering re-training pipeline.")
            # In production, trigger Airflow/Jenkins webhook here.
        else:
            logger.info("Data distribution looks stable.")
            
    except Exception as e:
        logger.error(f"Error during drift detection: {e}")

if __name__ == '__main__':
    # Stub for the drift detector running on cron
    data_dir = 'data' if os.path.exists('data') else '../../data'
    processed_dir = f'{data_dir}/processed'
    
    # Ideally, ref_df = training data, cur_df = newly collected data from previous week
    # Here using test data vs a subset as an example
    ref_path = f"{processed_dir}/X_test.csv"
    cur_path = f"{processed_dir}/X_test.csv" # MOCK: Needs actual live data path
    
    detect_drift(ref_path, cur_path)
