staging_sql_commands = {
    "stg_supplier": """
    CREATE TABLE supplier (
    supplier_id VARCHAR(50) PRIMARY KEY,
    supplier_name VARCHAR(50),
    contact_name VARCHAR(50),
    contact_email VARCHAR(50));
""",
    "stg_customers":"""
    CREATE TABLE customers(
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(50),
    address VARCHAR(100),
    signup_date DATE );
""",
    "stg_stores":"""
    CREATE TABLE stores(
    store_id VARCHAR(50) PRIMARY KEY,
    store_name VARCHAR(100),
    location VARCHAR(100),
    manager VARCHAR(100));
""",
    "stg_products":"""
    CREATE TABLE products(
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10,2));
""",
    "stg_inventory":"""
    CREATE TABLE inventory(
    product_id VARCHAR(50),
    store_id VARCHAR(50),
    stock_level INT,
    last_updated DATE,
    supplier_id VARCHAR(50),
    PRIMARY KEY (product_id,store_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id));
""",
    "stg_sales":"""
    CREATE TABLE sales(
    sale_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    product_id VARCHAR(50),
    store_id VARCHAR(50),
    sale_date DATE,
    quantity INT,
    total_amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id));
""",
    "stg_metadata":"""
    CREATE TABLE metadata (
    table_name VARCHAR(50) PRIMARY KEY,
    last_loaded_key TEXT,
    last_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
    """,
    "stg_dimdate":"""
    CREATE TABLE dimdate (
        date DATE,
        day INT,
        month INT,
        quarter INT,
        year INT,
        day_of_week VARCHAR(20)
    );
"""
}

drop_staging_sql_commands = {
    "drop_sales": "DROP TABLE IF EXISTS sales;",
    "drop_inventory": "DROP TABLE IF EXISTS inventory;",
    "drop_products": "DROP TABLE IF EXISTS products;",
    "drop_stores": "DROP TABLE IF EXISTS stores;",
    "drop_customers": "DROP TABLE IF EXISTS customers;",
    "drop_supplier": "DROP TABLE IF EXISTS supplier;",
    "drop_metadata": "DROP TABLE IF EXISTS metadata;",
    "drop dimdate": "DROP TABLE IF EXISTS dimdate"
}

