CREATE TABLE public.master_accounts (
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

CREATE TABLE public.master_bank_codes (
	bank_code varchar(5) NULL,
	bank_swift_code varchar(25) NULL,
	bank_name varchar(100) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.master_branchs (
	branch_code varchar(10) NULL,
	branch_name varchar(50) NULL,
	branch_location varchar(100) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.master_customers (
	cif_number varchar(10) NULL,
	customer_name varchar(50) NULL,
	gender varchar(2) NULL,
	cif_open_date date NULL,
	branch_code varchar(10) NULL,
	customer_birth_place varchar(100) NULL,
	customer_birth_date date NULL,
	customer_address varchar(100) NULL,
	customer_city varchar(100) NULL,
	customer_phone varchar(30) NULL,
	occupation varchar(100) NULL,
	married_status varchar(30) NULL,
	customer_email varchar(100) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.master_transaction_codes (
	transaction_code varchar(10) NULL,
	transaction_desc varchar(50) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);

CREATE TABLE public.transactions (
	transaction_id varchar(50) NULL,
	transaction_reference varchar(50) NULL,
	account_number varchar(21) NULL,
	debit_or_credit varchar(1) NULL,
	transaction_code varchar(10) NULL,
	transaction_date int4 NULL,
	transaction_time int4 NULL,
	amount numeric(17, 2) NULL,
	transaction_remark varchar(150) NULL,
	channel varchar(50) NULL,
	created_date timestamp NULL,
	created_by varchar(25) NULL
);