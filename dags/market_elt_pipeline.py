from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ==============================================================================
# DEFAULT TASK ARGUMENTS
# These settings apply to every single task inside this DAG unless overridden.
# ==============================================================================
default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,        # If yesterday's run failed, today's run still executes
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,                    # If an API or network call fails, retry automatically
    "retry_delay": timedelta(minutes=2), # Wait 2 minutes before retrying
}

# ==============================================================================
# DAG DEFINITION (Directed Acyclic Graph)
# The DAG is the master workflow container that schedules and links tasks.
# ==============================================================================
with DAG(
    dag_id="market_data_elt_pipeline",
    default_args=default_args,
    description="Automated Medallion ELT: Python Extract -> dbt Silver/Gold -> dbt Tests",
    
    # Schedule: How often to run. '@daily' means once every midnight.
    schedule_interval="@daily",
    
    # start_date: When the DAG starts existing in the Airflow scheduler's calendar.
    start_date=datetime(2026, 1, 1),
    
    # catchup=False: CRITICAL! If True, Airflow would attempt to trigger runs
    # for EVERY day between Jan 1, 2026 and today. False means only run from now on.
    catchup=False,
    
    tags=["finance", "medallion", "dbt", "postgres"],
) as dag:

    # --------------------------------------------------------------------------
    # TASK 1: BRONZE LAYER EXTRACTION
    # Uses BashOperator to execute our extraction script.
    # We pass connection details as environment variables so the script knows
    # it is running inside the Docker network.
    # --------------------------------------------------------------------------
    extract_bronze = BashOperator(
        task_id="extract_market_data_to_bronze",
        bash_command="python /opt/airflow/extract_options.py",
        env={
            "DB_HOST": "nifty_warehouse", # Points to Postgres container DNS
            "DB_PORT": "5432",            # Container's internal port
            "DB_NAME": "market_data",
            "DB_USER": "admin",
            "DB_PASSWORD": "password123",
        },
    )

    # --------------------------------------------------------------------------
    # TASK 2: SILVER & GOLD LAYER TRANSFORMATIONS
    # Runs 'dbt run' using the portable profiles-dir we placed in the project.
    # This executes stg_market_data (Silver View) and fct_daily_market_performance (Gold Table).
    # --------------------------------------------------------------------------
    dbt_transform = BashOperator(
        task_id="dbt_transform_silver_and_gold",
        bash_command=(
            "cd /opt/airflow/market_pipeline && "
            "dbt run --profiles-dir . --target docker"
        ),
    )

    # --------------------------------------------------------------------------
    # TASK 3: AUTOMATED DATA QUALITY GATEWAY
    # Runs 'dbt test' against the newly created tables.
    # If any test fails (null values, unexpected trends), this task fails in RED,
    # alerting engineers before bad data is queried by stakeholders.
    # --------------------------------------------------------------------------
    dbt_test = BashOperator(
        task_id="dbt_run_schema_tests",
        bash_command=(
            "cd /opt/airflow/market_pipeline && "
            "dbt test --profiles-dir . --target docker"
        ),
    )

    # ==============================================================================
    # PIPELINE DEPENDENCY GRAPH (Lineage)
    # The '>>' (bitshift) operator defines execution order:
    # 1. extract_bronze MUST finish successfully before dbt_transform starts.
    # 2. dbt_transform MUST finish successfully before dbt_test starts.
    # If extract_bronze fails, dbt never runs, preventing partial or broken updates.
    # ==============================================================================
    extract_bronze >> dbt_transform >> dbt_test