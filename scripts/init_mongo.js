db = db.getSiblingDB('fraud_db');

db.createCollection('transactions');

db.transactions.createIndex({ "processed_at": -1 });
db.transactions.createIndex({ "fraud_flag": 1 });
db.transactions.createIndex({ "risk_level": 1 });
db.transactions.createIndex({ "type": 1 });
db.transactions.createIndex({ "amount": 1 });

print("Database and indexes initialized.");
