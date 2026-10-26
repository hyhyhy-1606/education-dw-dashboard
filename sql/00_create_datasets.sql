-- BigQuery setup. Project ID: data-warehouse-512306, Region: asia-southeast1
CREATE SCHEMA IF NOT EXISTS `data-warehouse-512306.education_dw`;
CREATE SCHEMA IF NOT EXISTS `data-warehouse-512306.education_dw_gold`;
-- Upload raw/silver CSV files to data-warehouse-512306.education_dw tables using BigQuery UI.
-- Do not store credentials or service-account keys in this repository.
