warehouse_sql_commands = {
    "dim_customer": """
    CREATE TABLE dim_customer (
        customer_key INT AUTO_INCREMENT PRIMARY KEY,
        customer_id VARCHAR(50),
        customer_name VARCHAR(100),
        email VARCHAR(100),
        phone VARCHAR(50),
        street TEXT,
        city VARCHAR(50),
        state VARCHAR(15),
        zip INT
    );
    """,
    "dim_product": """
    CREATE TABLE dim_product (
        product_key INT AUTO_INCREMENT PRIMARY KEY,
        product_id VARCHAR(50),
        product_name VARCHAR(100),
        product_category VARCHAR(100),
        price DECIMAL(10,2)
    );
    """,
    "dim_store": """
    CREATE TABLE dim_store (
        store_key INT AUTO_INCREMENT PRIMARY KEY,
        store_id VARCHAR(50),
        store_name VARCHAR(100),
        location VARCHAR(100),
        region VARCHAR(100),
        manager VARCHAR(100)
    );
    """,
    "dim_supplier": """
    CREATE TABLE dim_supplier (
        supplier_key INT AUTO_INCREMENT PRIMARY KEY,
        supplier_id VARCHAR(50),
        supplier_name VARCHAR(100),
        contact_name VARCHAR(100),
        contact_email VARCHAR(100)
    );
    """,
    "dim_date": """
    CREATE TABLE dim_date (
        date_key INT AUTO_INCREMENT PRIMARY KEY,
        date DATE,
        day INT,
        month INT,
        quarter INT,
        year INT,
        day_of_week VARCHAR(20)
    );
    """,
    "fact_sales": """
    CREATE TABLE fact_sales (
        sale_key INT AUTO_INCREMENT PRIMARY KEY,
        sale_id VARCHAR(50),
        customer_key INT,
        product_key INT,
        store_key INT,
        date_key INT,
        quantity INT,
        total_amount DECIMAL(10,2),
        FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
        FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
        FOREIGN KEY (store_key) REFERENCES dim_store(store_key),
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
    );
    """
}

drop_warehouse_sql_commands = {
    "drop_fact_sales": "DROP TABLE IF EXISTS fact_sales;",
    "drop_dim_date": "DROP TABLE IF EXISTS dim_date;",
    "drop_dim_supplier": "DROP TABLE IF EXISTS dim_supplier;",
    "drop_dim_store": "DROP TABLE IF EXISTS dim_store;",
    "drop_dim_product": "DROP TABLE IF EXISTS dim_product;",
    "drop_dim_customer": "DROP TABLE IF EXISTS dim_customer;"
}
