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
    master['created_date'] = now
    master['created_by'] = 'System'
    return(data)


def load_data(data : pd.DataFrame, connection , table_name : str, load_method : str):
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

    table_name_brz = sys.argv[1]
    primary_key = sys.argv[2]
    table_name_slv = sys.argv[3]
    if_exist = sys.argv[4]

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

        master = pd.read_sql(
            f"select * from {table_name_brz}",
            con=conn_pgsql_brz
        )

        master.dropna(subset=[primary_key], inplace=True)
        master.drop_duplicates(subset=[primary_key], inplace=True)

        master = master.apply(
            lambda col: col.map(
                lambda x: x.strip() if isinstance(x, str) else x
            ) if col.dtype == 'object' else col
        )

        master = add_metadata(master)

        engine_pgsql_slv, conn_pgsql_slv = connect_to_database(
            hostname=os.getenv('DB_HOST'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_SLV_NAME')
        )

        action_on_method(
            connection=conn_pgsql_slv,
            table_name=table_name_slv,
            action_method=if_exist
        )

        load_data(
            master,
            conn_pgsql_slv,
            table_name=table_name_slv,
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