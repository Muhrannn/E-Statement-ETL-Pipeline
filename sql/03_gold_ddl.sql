CREATE TABLE public.dim_transaction_code (
	transaction_code varchar(10) NULL,
	transaction_desc varchar(50) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.dim_transaction_master_account (
	account_number varchar(18) NULL,
	cif_number varchar(10) NULL,
	account_open_date date NULL,
	account_currency_type varchar(5) NULL,
	account_status varchar(20) NULL,
	product_code varchar(20) NULL,
	product_name varchar(50) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.dim_transaction_master_bank_code (
	bank_code varchar(5) NULL,
	bank_swift_code varchar(25) NULL,
	bank_name varchar(100) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.dim_transaction_master_branch (
	branch_code varchar(10) NULL,
	branch_name varchar(50) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.dim_transaction_master_customer (
	cif_number varchar(10) NULL,
	customer_name varchar(50) NULL,
	gender varchar(2) NULL,
	branch_code varchar(10) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.f_estatement_transaction (
	transaction_id varchar(17) NULL,
	transaction_reference varchar(23) NULL,
	account_number varchar(17) NULL,
	debit_or_credit varchar(2) NULL,
	transaction_code varchar(8) NULL,
	transaction_datetime timestamp NULL,
	transaction_remark varchar(100) NULL,
	channel varchar(30) NULL,
	credit_amount float8 NULL,
	debit_amount float8 NULL,
	transaction_desc varchar(30) NULL,
	additional_fee float8 NULL,
	balance float8 NULL,
	transmode_code varchar(20) NULL,
	acquirer_bank_code varchar(5) NULL,
	acquirer_account_number varchar(30) NULL,
	acquirer_account_name varchar(100) NULL,
	bank_code varchar(5) NULL,
	bank_swift_code varchar(20) NULL,
	bank_name varchar(100) NULL,
	cif_number varchar(12) NULL,
	account_open_date date NULL,
	account_currency_type varchar(10) NULL,
	account_status varchar(30) NULL,
	product_code varchar(50) NULL,
	product_name varchar(100) NULL,
	account_aging int8 NULL,
	customer_name varchar(100) NULL,
	gender varchar(10) NULL,
	branch_code varchar(20) NULL,
	branch_name varchar(50) NULL,
	created_date timestamptz NULL,
	created_by varchar(100) NULL
);