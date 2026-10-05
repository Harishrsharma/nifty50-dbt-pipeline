FROM apache/airflow:2.10.5-python3.11

USER airflow

# Install pipeline dependencies inside the Airflow worker environment
RUN pip install --no-cache-dir \
    dbt-postgres \
    yfinance \
    psycopg2-binary