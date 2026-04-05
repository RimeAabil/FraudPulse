.PHONY: up down reset logs train status up-full up-mlops

up:              ## Start core pipeline (Kafka, Spark, Mongo, Dashboard)
	docker compose up -d

up-mlops:        ## Start core + MLOps (MLflow, Model Server)
	docker compose -f docker-compose.yml -f docker-compose.mlops.yml up -d

up-full:         ## Start all services (Core + MLOps + Observability)
	docker compose -f docker-compose.yml -f docker-compose.mlops.yml -f docker-compose.observability.yml up -d

down:            ## Stop core pipeline
	docker compose down

down-full:       ## Stop all services
	docker compose -f docker-compose.yml -f docker-compose.mlops.yml -f docker-compose.observability.yml down

reset:           ## Full reset (wipe volumes)
	./scripts/reset.sh all

reset-full:      ## Full reset all services
	./scripts/reset.sh full

logs:            ## Tail logs of core pipeline
	docker compose logs -f --tail=100

logs-spark:      ## Tail Spark consumer logs exclusively
	docker compose logs -f spark-consumer spark-master spark-worker-1

train:           ## Train XGBoost model locally and register to MLflow
	python src/ml/train.py

status:          ## Check service health
	docker compose ps
