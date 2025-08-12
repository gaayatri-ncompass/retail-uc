staging_to_dimension_map = {
    'customers': {
        'customer_id': 'customer_id',
        'customer_name': 'customer_name',
        'email': 'email',
        'phone': 'phone',
    },
    'products': {
        'product_id': 'product_id',
        'product_name': 'product_name',
        'category': 'product_category',
        'price': 'price'
    },
    'stores': {
        'store_id': 'store_id',
        'store_name': 'store_name',
        'location': 'location',
        'manager': 'manager'
    },
    'suppliers': {
        'supplier_id': 'supplier_id',
        'supplier_name': 'supplier_name',
        'contact_name': 'contact_name',
        'contact_email': 'contact_email'
    },
    'dimdate':{
        'date': 'date',
        'day': 'day',
        'month': 'month',
        'quarter': 'quarter',
        'year': 'year',
        'day_of_week': 'day_of_week'
    },
    'sales': {
        'sale_id': 'sale_id',
        'customer_key': 'customer_key',
        'product_key': 'product_key',
        'store_key': 'store_key',
        'date_key': 'date_key',
        'quantity': 'quantity',
        'total_amount': 'total_amount'
    }
}
