--Looking for duplicated rows by cst_id

SELECT cst_id, COUNT(*) 
FROM bronze.crm_cust_info
GROUP by cst_id
having COUNT(*) > 1 or cst_id IS NULL

/* This query effectively uses the ROW_NUMBER() window function to 
assign a sequential number to customer records based on their creation date 
within each customer group (partition by). By ordering these records in descending order 
of creation date (order by cst_create_date desc), the most recent entry 
for each customer will receive flag_last = 1. This is a clean and efficient way to identify 
the latest record for each customer without needing self-joins or subqueries. */
select *, ROW_NUMBER() OVER (partition by cst_id order by cst_create_date desc) as flag_last
from bronze.crm_cust_info
order by flag_last

/*
This query selects the most recent record for every unique customer ID (cst_id) 
from the 'bronze.crm_cust_info' table.
It achieves this by using a subquery (aliased as 't') to first calculate the 
ROW_NUMBER() within each customer partition, ordering by the most recent 
creation date (desc). The outer query then filters this result set 
to only keep the rows where 'flag_last' equals 1, effectively isolating 
only the latest entry for each customer. This is a standard and efficient 
pattern for deduplication or identifying current/active records.
*/
select * 
from (
	select *, ROW_NUMBER() OVER (partition by cst_id order by cst_create_date desc) as flag_last
	from bronze.crm_cust_info
) as t 
where t.flag_last = 1

--Checking for unwanted spaces
select cst_id,cst_firstname
from bronze.crm_cust_info
where cst_firstname != trim(cst_firstname) --likewise

insert into silver.crm_cust_info (
	cst_id, 
	cst_key, 
	cst_firstname, 
	cst_lastname, 
	cst_marital_status, 
	cst_gndr, 
	cst_create_date)

select 
	cst_id, 
	cst_key, 
	TRIM(cst_firstname) AS cst_firstname, 
	TRIM(cst_lastname) AS cst_lastname, 
	case 
		when UPPER(TRIM(cst_marital_status)) = 'S' then 'Single' 
		when UPPER(TRIM(cst_marital_status)) = 'M' then 'Married'
		else 'n/a'
	end as cst_marital_status,
	case 
		when UPPER(TRIM(cst_gndr)) = 'F' then 'Female' 
		when UPPER(TRIM(cst_gndr)) = 'M' then 'Male'
		else 'n/a'
	end as cst_gndr,
	cst_create_date
from (
	select *, ROW_NUMBER() OVER (partition by cst_id order by cst_create_date desc) as flag_last
	from bronze.crm_cust_info
	where cst_id is not null
) as t 
where t.flag_last = 1


--Looking for duplicated rows by cst_id
SELECT cst_id, COUNT(*) 
FROM silver.crm_cust_info
GROUP by cst_id
having COUNT(*) > 1 or cst_id IS NULL

--Checking for unwanted spaces
select cst_id,cst_firstname
from silver.crm_cust_info
where cst_firstname != trim(cst_firstname) --likewise

select cst_id,cst_lastname
from silver.crm_cust_info
where cst_lastname != trim(cst_lastname) --likewise

--Standardization & Data Consistency
select distinct cst_marital_status
from silver.crm_cust_info

select distinct cst_gndr
from silver.crm_cust_info.


select * from silver.crm_cust_info
