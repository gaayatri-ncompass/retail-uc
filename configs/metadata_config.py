def get_expected_columns():
    return {
        'customers': ['customer_id', 'customer_name', 'email', 'phone', 'address', 'signup_date'],
        'products': ['product_id', 'product_name', 'category', 'price'],
        'stores': ['store_id', 'store_name', 'location', 'manager'],
        'sales': ['sale_id', 'customer_id', 'product_id', 'store_id', 'sale_date', 'quantity', 'total_amount'],
        'inventory': ['product_id', 'store_id', 'stock_level', 'last_updated', 'supplier_id'],
        'suppliers': ['supplier_id', 'supplier_name', 'contact_name', 'contact_email']
    }


def get_extraction_config():
    return [
        ('customers.csv', 'customers', 'customer_id'),
        ('products.csv', 'products', 'product_id'),
        ('stores.csv', 'stores', 'store_id'),
        ('sales.csv', 'sales', 'sale_id'),
        ('inventory.csv', 'inventory', 'product_id'),
        ('suppliers.csv', 'suppliers', 'supplier_id')
    ]
