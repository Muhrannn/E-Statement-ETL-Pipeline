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

    engine_pgsql_brz = None
    conn_pgsql_brz = None
    engine_pgsql_slv = None
    conn_pgsql_slv = None

    try:
        engine_pgsql_brz, conn_pgsql_brz = connect_to_database(
            hostname=os.getenv('DB_HOST'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_BRZ_NAME')
        )

        transaction = pd.read_sql(
            "SELECT * FROM transactions t",
            con=conn_pgsql_brz
        )

        transaction = transaction.drop_duplicates(
            subset=["transaction_id"]
        )
        transaction = transaction.dropna(
            subset=["transaction_id"]
        )

        transaction["transaction_date"] = pd.to_datetime(
            transaction["transaction_date"].astype(str),
            format="%Y%j"
        ).dt.strftime("%Y-%m-%d")

        transaction["transaction_time"] = pd.to_datetime(
            transaction["transaction_time"]
            .astype(str)
            .str.replace(":", "")
            .str.zfill(6),
            format="%H%M%S"
        ).dt.strftime("%H:%M:%S")

        transaction["transaction_date"] = (
            transaction["transaction_date"].astype(str) + " " +
            transaction["transaction_time"].astype(str)
        )

        transaction = transaction.rename(
            columns={"transaction_date": "transaction_datetime"}
        )

        transaction["transaction_datetime"] = pd.to_datetime(
            transaction["transaction_datetime"]
        )

        transaction = transaction.drop(columns=["transaction_time"])
        transaction = add_metadata(transaction)

        engine_pgsql_slv, conn_pgsql_slv = connect_to_database(
            hostname=os.getenv('DB_HOST'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_SLV_NAME')
        )

        action_on_method(
            connection=conn_pgsql_slv,
            table_name='transactions',
            action_method=if_exist
        )

        load_data(
            transaction,
            conn_pgsql_slv,
            table_name='transactions',
            load_method='append'
        )

    finally:
        if conn_pgsql_brz is not None:
            conn_pgsql_brz.close()

        if conn_pgsql_slv is not None:
            conn_pgsql_slv.close()

        if engine_pgsql_brz is not None:
            engine_pgsql_brz.dispose()

        if engine_pgsql_slv is not None:
            engine_pgsql_slv.dispose()