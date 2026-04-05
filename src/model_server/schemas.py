from pydantic import BaseModel
from typing import Optional

class TransactionSchema(BaseModel):
    step: int
    type: str
    amount: float
    nameOrig: str
    oldbalanceOrg: float
    newbalanceOrig: float
    nameDest: str
    oldbalanceDest: float
    newbalanceDest: float
    isFraud: Optional[int] = None
    isFlaggedFraud: Optional[int] = None

class PredictionResponse(BaseModel):
    fraud_probability: float
    model_version: str
    variant: str
