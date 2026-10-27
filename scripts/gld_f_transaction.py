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

def add_metadata(data : pd.DataFrame):
    now = datetime.now(timezone(timedelta(hours=7)))
    transaction['created_date'] = now
    transaction['created_by'] = 'System'
    return(data)

def extract_table(table_name, conn):
    return pd.read_sql(
        f"SELECT * FROM {table_name}",
        con=conn
    )

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
            hostname=os.getenv('DB_HOST'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port= (os.getenv('DB_PORT')),
            database=os.getenv('DB_SLV_NAME')
        )

        engine_pgsql_gld, conn_pgsql_gld = connect_to_database(
            hostname=os.getenv('DB_HOST'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port= (os.getenv('DB_PORT')),
            database=os.getenv('DB_GLD_NAME')
        )

        transaction = extract_table("transactions", conn_pgsql_slv)
        transaction_code = extract_table("dim_transaction_code", conn_pgsql_gld)
        transaction_master_bank_code = extract_table("dim_transaction_master_bank_code", conn_pgsql_gld)
        transaction_master_account = extract_table("dim_transaction_master_account", conn_pgsql_gld)
        transaction_master_customer = extract_table("dim_transaction_master_customer", conn_pgsql_gld)
        transaction_master_branch = extract_table("dim_transaction_master_branch", conn_pgsql_gld)

        transaction = transaction.sort_values(
            by=["account_number", "transaction_datetime"],
            ascending=[True, True]
        )

        transaction["credit_amount"] = np.where(
            transaction["debit_or_credit"] == "C",
            transaction["amount"],
            0
        )

        transaction["debit_amount"] = np.where(
            transaction["debit_or_credit"] == "D",
            transaction["amount"],
            0
        )

        transaction = pd.merge(
            transaction.drop(columns=["created_by", "created_date"]),
            transaction_code.drop(columns=["created_by", "created_date"]),
            on="transaction_code",
            how="left"
        )

        transaction = transaction.drop(columns=["amount"])

        transaction_fee = transaction.loc[
            transaction["transaction_code"] == "TRX092",
            ["transaction_reference", "debit_amount"]
        ].copy()

        transaction_fee = transaction_fee.rename(
            columns={"debit_amount": "additional_fee"}
        )

        transaction = transaction[
            transaction["transaction_code"] != "TRX092"
        ].copy()

        transaction = transaction.merge(
            transaction_fee,
            on="transaction_reference",
            how="left"
        )

        transaction["additional_fee"] = transaction["additional_fee"].fillna(0)

        transaction = transaction.sort_values(
            by=["account_number", "transaction_datetime"],
            ascending=[True, True]
        ).copy()

        transaction["balance"] = (
            transaction["credit_amount"]
            - transaction["debit_amount"]
            - transaction["additional_fee"]
        ).groupby(transaction["account_number"]).cumsum()

        conditions = [
            transaction["transaction_desc"] == "Cash Deposit",
            transaction["transaction_desc"] == "Cash Withdrawal",
            transaction["transaction_desc"] == "Transfer",
            transaction["transaction_desc"].isin([
                "Administration Fee",
                "Monthly Fee"
            ])
        ]

        choices = [
            "SETOR",
            "TARIK",
            "TRANSFER",
            "INTER"
        ]

        transaction["transmode_code"] = np.select(
            conditions,
            choices,
            default="INTER"
        )

        transfer_transaction = transaction[
            transaction["transaction_code"] == "TRX002"
        ]

        transfer_transaction = (
            transfer_transaction
            .groupby(["transaction_code", "transaction_reference"])
            .size()
            .reset_index(name="total_transaction")
        )

        transaction["acquirer_bank_code"] = np.select(
            [
                transaction["transaction_desc"].eq("Cash Withdrawal")
                & transaction["transaction_remark"].str.contains(
                    r"TARIK VIA ATM", case=False, na=False
                ),

                transaction["transmode_code"].eq("OUTGOING")
                & transaction["transaction_remark"].str.startswith(
                    "QRIS_", na=False
                ),

                transaction["transmode_code"].isin(
                    ["INCOMING", "OUTGOING", "OVERBOOKING"]
                )
                & transaction["transaction_remark"].str.startswith(
                    ("TRF_", "BIFAST_"), na=False
                )
            ],
            [
                transaction["transaction_remark"].str.extract(
                    r"TARIK VIA ATM\s+(\d+)", expand=False
                ),
                transaction["transaction_remark"].str.extract(
                    r"QRIS_(\d+)_", expand=False
                ),
                transaction["transaction_remark"].str.extract(
                    r"(?:TRF|BIFAST)_(\d+)_", expand=False
                )
            ],
            default=None
        )

        transaction["acquirer_account_number"] = transaction[
            "transaction_remark"
        ].str.extract(
            r"(?:TRF|BIFAST)_\d+_(\d+)_",
            expand=False
        )

        transaction["acquirer_account_name"] = transaction[
            "transaction_remark"
        ].str.extract(
            r"(?:TRF|BIFAST)_\d+_\d+_(.+)",
            expand=False
        )

        transaction = transaction.merge(
            transaction_master_bank_code.drop(
                columns=["created_by", "created_date"]
            ),
            left_on="acquirer_bank_code",
            right_on="bank_code",
            how="left"
        )

        transaction = transaction.merge(
            transaction_master_account.drop(
                columns=["created_by", "created_date"]
            ),
            on="account_number",
            how="left"
        )

        transaction["account_aging"] = (
            pd.to_datetime(transaction["transaction_datetime"])
            - pd.to_datetime(transaction["account_open_date"])
        ).dt.days

        transaction = transaction.merge(
            transaction_master_customer.drop(
                columns=["created_by", "created_date"]),
            on="cif_number",
            how="left"
        )

        transaction = transaction.merge(
            transaction_master_branch.drop(
                columns=["created_by", "created_date"]),
            on="branch_code",
            how="left"
        )

        transaction = add_metadata(transaction)

        action_on_method(
            connection=conn_pgsql_gld,
            table_name='f_estatement_transaction',
            action_method=if_exist
        )

        load_data(
            transaction,
            conn_pgsql_gld,
            table_name='f_estatement_transaction',
            load_method='append'
        )

    finally:
        if conn_pgsql_gld is not None:
            conn_pgsql_gld.close()

        if conn_pgsql_slv is not None:
            conn_pgsql_slv.close()

        if engine_pgsql_gld is not None:
            engine_pgsql_gld.dispose()

        if engine_pgsql_slv is not None:
            engine_pgsql_slv.dispose()