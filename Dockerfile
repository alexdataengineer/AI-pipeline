FROM apache/airflow:2.8.0

USER root

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy requirements and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Set PYTHONPATH so Airflow can find our modules
ENV PYTHONPATH=/opt/airflow:/opt/airflow/app:/opt/airflow/config

