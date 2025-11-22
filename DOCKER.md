# Docker Setup Guide

Quick reference for running Airflow with Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (usually comes with Docker Desktop)
- `.env` file configured with your API keys

## Quick Start

```bash
# 1. Setup (copies CV PDF and prepares environment)
./setup_docker.sh

# 2. Start all services
docker-compose up -d

# 3. Check service status
docker-compose ps

# 4. View logs
docker-compose logs -f
```

## Access Airflow UI

- **URL**: http://localhost:8080
- **Username**: `airflow`
- **Password**: `airflow`

## Common Commands

### Start/Stop Services

```bash
# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-webserver
```

### Execute Commands in Containers

```bash
# Airflow CLI
docker-compose exec airflow-webserver airflow dags list
docker-compose exec airflow-webserver airflow tasks list cv_ingestion_pipeline

# Python shell
docker-compose exec airflow-scheduler python
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up -d --build

# Or rebuild specific service
docker-compose build airflow-webserver
docker-compose up -d airflow-webserver
```

## File Locations in Container

- **DAGs**: `/opt/airflow/dags`
- **App code**: `/opt/airflow/app`
- **Config**: `/opt/airflow/config`
- **CV PDF**: `/opt/airflow/data/cv.pdf`
- **Logs**: `/opt/airflow/logs`

## Environment Variables

Environment variables are loaded from `.env` file and passed to containers. Key variables:

- `OPENAI_API_KEY` - Your OpenAI API key
- `PINECONE_API_KEY` - Your Pinecone API key
- `CV_PDF_PATH` - Path to CV PDF (default: `/opt/airflow/data/cv.pdf` in Docker)
- `PINECONE_INDEX_NAME` - Pinecone index name (default: `alex_cv_index`)

## Troubleshooting

### Services won't start

```bash
# Check if ports are in use
lsof -i :8080  # Airflow webserver
lsof -i :5432  # PostgreSQL

# Check Docker resources
docker system df
docker system prune  # Clean up if needed
```

### DAG not appearing

```bash
# Check DAG syntax
docker-compose exec airflow-webserver airflow dags list-import-errors

# Check if files are mounted
docker-compose exec airflow-webserver ls -la /opt/airflow/dags
```

### Import errors in DAG

```bash
# Check Python path
docker-compose exec airflow-scheduler python -c "import sys; print(sys.path)"

# Check if modules are accessible
docker-compose exec airflow-scheduler python -c "from app.pdf_loader import process_pdf_to_chunks; print('OK')"
```

### CV PDF not found

```bash
# Check if file exists in container
docker-compose exec airflow-scheduler ls -la /opt/airflow/data/

# Copy file manually if needed
docker cp /path/to/cv.pdf ai-pipeline-airflow-webserver-1:/opt/airflow/data/cv.pdf
```

## Service Architecture

- **postgres**: PostgreSQL database for Airflow metadata
- **airflow-webserver**: Airflow web UI (port 8080)
- **airflow-scheduler**: Airflow scheduler (runs DAGs)
- **airflow-init**: One-time initialization service

## Resource Requirements

- **Minimum**: 4GB RAM, 2 CPUs, 10GB disk
- **Recommended**: 8GB RAM, 4 CPUs, 20GB disk

Check resources:
```bash
docker stats
```

