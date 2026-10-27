import pandas as pd
import numpy as np
import sqlalchemy as sa
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timezone, timedelta
import sys


def connect_to_database(**params):
    hostname = params.get('hostname')
    port = params.get('port')
    username = params.get('username')
    password = params.get('password')
    database = params.get('database')
    engine = sa.create_engine(
        f"postgresql+psycopg2://{username}:{password}@{hostname}:{port}/{database}"
    )
    conn = engine.connect()
    return (engine, conn)

def add_metadata(data : pd.DataFrame):
    now = datetime.now(timezone(timedelta(hours=7)))
    data['created_date'] = now
    data['created_by'] = 'System'
    return(data)

def extract_table(table_name, conn):
    return pd.read_sql(
        f"SELECT * FROM {table_name}",
        con=conn
    )

def load_data(data : pd.DataFrame, connection, table_name : str, load_method : str):
        data.to_sql(
        table_name,
        connection,
        if_exists = load_method,
        index = False,
        chunksize = 1000,
        method = 'multi'
    )

def action_on_method(connection, table_name : str, action_method : str):
    if action_method == 'truncate':
        action = sa.text(f'TRUNCATE TABLE public."{table_name}"')
    elif action_method == 'drop':
        action = sa.text(f'DROP TABLE IF EXISTS public."{table_name}"')     
    elif action_method == 'delete':
        action = sa.text(f'DELETE FROM public."{table_name}"')
    else:
        pass
    with connection.begin():
        connection.execute(action)
        
if __name__ == "__main__":
    env_path = find_dotenv('/opt/airflow/scripts/db.env')
    load_dotenv(env_path, override=True)

    if_exist = sys.argv[1]

    env_path = find_dotenv('db.env', usecwd=True)
    load_dotenv(env_path, override=True)

    conn_pgsql_slv = None
    engine_pgsql_slv = None
    engine_pgsql_gld = None
    conn_pgsql_gld = None

    try:
        engine_pgsql_slv, conn_pgsql_slv = connect_to_database(
        hostname = os.getenv('DB_HOST'),    
        username = os.getenv('DB_USER'),
        password = os.getenv('DB_PASSWORD'),
        port = int(os.getenv('DB_PORT')),
        database = os.getenv('DB_SLV_NAME')
    )
        
        transaction_code = extract_table("master_transaction_codes", conn_pgsql_slv)
        transaction_master_bank_code = extract_table("master_bank_codes", conn_pgsql_slv)
        transaction_master_account = extract_table("master_accounts", conn_pgsql_slv)
        transaction_master_customer = extract_table("master_customers", conn_pgsql_slv)
        transaction_master_branch = extract_table("master_branchs", conn_pgsql_slv)

        transaction_code = transaction_code.drop(columns=["created_by", "created_date"])
        transaction_master_bank_code = transaction_master_bank_code.drop(columns=["created_by", "created_date"])
        transaction_master_account = transaction_master_account.drop(columns=["created_by", "created_date"])
        transaction_master_customer = transaction_master_customer[["cif_number", "customer_name", "gender", "branch_code"]]
        transaction_master_branch = transaction_master_branch[["branch_code", "branch_name"]]

        engine_pgsql_gld, conn_pgsql_gld = connect_to_database(
        hostname=os.getenv('DB_HOST'),
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=int(os.getenv('DB_PORT')),
        database=os.getenv('DB_GLD_NAME')
            )
    
        tables = {
            "transaction_code": transaction_code,
            "transaction_master_bank_code": transaction_master_bank_code,
            "transaction_master_account": transaction_master_account,
            "transaction_master_customer": transaction_master_customer,
            "transaction_master_branch": transaction_master_branch
        }
        
        for test, data in tables.items():
            action_on_method(connection=conn_pgsql_gld,table_name=f'dim_{test}',action_method=if_exist)
            data = add_metadata(data)
            load_data(data,conn_pgsql_gld,table_name=f'dim_{test}',load_method='append')
    
    finally:
        if conn_pgsql_gld is not None:
            conn_pgsql_gld.close()

        if conn_pgsql_slv is not None:
            conn_pgsql_slv.close()

        if engine_pgsql_gld is not None:
            engine_pgsql_gld.dispose()

        if engine_pgsql_slv is not None:
            engine_pgsql_slv.dispose()