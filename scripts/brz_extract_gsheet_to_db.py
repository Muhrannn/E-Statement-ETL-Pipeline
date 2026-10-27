import pandas as pd
import numpy as np
import sqlalchemy as sa
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timezone, timedelta
import sys

def extract_data_from_gsheet(
    sheet_id : str,
    sheet_name : str,
    dtype = None
):
  url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'
  data = pd.read_excel(url, sheet_name = sheet_name, dtype = dtype)
  return(data)

def add_metadata(data : pd.DataFrame):
    now = datetime.now(timezone(timedelta(hours=7)))
    data['created_date'] = now
    data['created_by'] = 'System'
    return(data)

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

def load_data(data : pd.DataFrame, connection, table_name : str, load_method : str):
    data.to_sql(
        table_name,
        connection,
        if_exists = load_method,
        index = False
    )


def action_on_method(connection, table_name: str, action_method: str):
    if action_method == "truncate":
        action = sa.text(f'TRUNCATE TABLE public."{table_name}"')
    elif action_method == "drop":
        action = sa.text(f'DROP TABLE IF EXISTS public."{table_name}"')
    elif action_method == "delete":
        action = sa.text(f'DELETE FROM public."{table_name}"')
    else:
        raise ValueError(f"Metode tidak dikenal: {action_method}")

    connection.execute(action)


if __name__ == "__main__":
    sheet_id = '1He4b-15DsAJG_dwYgBz5nDVNW_zQfXZ3VSYoASr4WVo'

    env_path = find_dotenv('/opt/airflow/scripts/db.env')
    load_dotenv(env_path, override=True)

    sheet_name = sys.argv[1]
    primary_key = sys.argv[2]
    table_name = sys.argv[3]
    if_exist = sys.argv[4]

    engine_pgsql = None
    conn_pgsql = None

    try:
        data_extracted = extract_data_from_gsheet(
            sheet_id=sheet_id,
            sheet_name=sheet_name,
            dtype={primary_key: pd.StringDtype()}
        )

        data_extracted = add_metadata(data_extracted)

        engine_pgsql, conn_pgsql = connect_to_database(
            hostname=os.getenv('DB_HOST'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_BRZ_NAME')
        )

        action_on_method(
            connection=conn_pgsql,
            table_name=table_name,
            action_method=if_exist
        )

        load_data(
            data=data_extracted,
            connection=conn_pgsql,
            table_name=table_name,
            load_method='append'
        )

    finally:
        if conn_pgsql is not None:
            conn_pgsql.close()

        if engine_pgsql is not None:
            engine_pgsql.dispose()