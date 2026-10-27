from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id = "ETL_BANK_TRANSACTION",
    start_date = datetime(2026, 1, 1),
    schedule = None,
    catchup = False,
    tags = ["python", "etl"],
) as dag:

    bronze_transaction = BashOperator(
        task_id="bronze_transaction",
        bash_command=(
            'python /opt/airflow/scripts/brz_extract_gsheet_to_db.py "transaction" "transaction_id" "transactions" "truncate"'
        ),
    )

    bronze_customer = BashOperator(
            task_id="bronze_customer",
            bash_command=(
                'python /opt/airflow/scripts/brz_extract_gsheet_to_db.py "master_customer" "cif_number" "master_customers" "truncate"'
            ),
        )

    bronze_account = BashOperator(
            task_id="bronze_account",
            bash_command=(
                'python /opt/airflow/scripts/brz_extract_gsheet_to_db.py "master_account" "account_number" "master_accounts" "truncate"'
            ),
        )
    
    bronze_transaction_code = BashOperator(
            task_id="bronze_transaction_code",
            bash_command=(
                'python /opt/airflow/scripts/brz_extract_gsheet_to_db.py "master_transaction_code" "transaction_code" "master_transaction_codes" "truncate"'
            ),
        )

    bronze_bank_code = BashOperator(
            task_id="bronze_bank_code",
            bash_command=(
                'python /opt/airflow/scripts/brz_extract_gsheet_to_db.py "master_bank_code" "bank_code" "master_bank_codes" "truncate"'
            ),
        )

    bronze_branch = BashOperator(
            task_id="bronze_branch",
            bash_command=(
                'python /opt/airflow/scripts/brz_extract_gsheet_to_db.py "master_branch" "branch_code" "master_branchs" "truncate"'
            ),
        )

    silver_transaction = BashOperator(
            task_id="silver_transaction",
            bash_command=(
                'python /opt/airflow/scripts/slv_transaction.py "truncate"'
            ),
        )

    silver_account = BashOperator(
        task_id="silver_account",
        bash_command=(
            'python /opt/airflow/scripts/slv_master.py "master_accounts" ""account_number"" "master_accounts" "truncate"'
        ),
    )

    silver_customer = BashOperator(
        task_id="silver_customer",
        bash_command=(
            'python /opt/airflow/scripts/slv_master.py "master_customers" ""cif_number"" "master_customers" "truncate"'
        ),
    )

    silver_transaction_code = BashOperator(
        task_id="silver_transaction_code",
        bash_command=(
            'python /opt/airflow/scripts/slv_master.py "master_transaction_codes" ""transaction_code"" "master_transaction_codes" "truncate"'
        ),
    )

    silver_bank_code = BashOperator(
        task_id="silver_bank_code",
        bash_command=(
            'python /opt/airflow/scripts/slv_master.py "master_bank_codes" ""bank_code"" "master_bank_codes" "truncate"'
        ),
    )

    silver_branch = BashOperator(
        task_id="silver_branch",
        bash_command=(
            'python /opt/airflow/scripts/slv_master.py "master_branchs" ""branch_code"" "master_branchs" "truncate"'
        ),
    )


    dimesion_data_master = BashOperator(
        task_id="dimesion_data_master",
        bash_command=(
            'python /opt/airflow/scripts/gld_dimension_master.py "truncate"'
        ),
    )

    fact_data_estatement_transaction = BashOperator(
        task_id="fact_data_estatement_transaction",
        bash_command=(
            'python /opt/airflow/scripts/gld_f_transaction.py "truncate"'
        ),
    )




    

    bronze_transaction >> silver_transaction,
    bronze_account >> silver_account,
    bronze_customer >> silver_customer, 
    bronze_transaction_code >> silver_transaction_code, 
    bronze_bank_code >> silver_bank_code, 
    bronze_branch >> silver_branch

    [
    silver_transaction,
    silver_account,
    silver_customer,
    silver_transaction_code,
    silver_bank_code,
    silver_branch
    ] >> dimesion_data_master >> fact_data_estatement_transaction