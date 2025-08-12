
schemas = {
    'customers': {
        'customer_id': {'type': 'string', 'min': 1},
        'customer_name': {'type': 'string'},
        'email': {'type': 'string'},
        'phone': {'type': 'string'},
        'address': {'type': 'string', 'min': 1},
        'signup_date': {'type': 'string', 'regex': r'^\d{4}-\d{2}-\d{2}$'}
    },
    'stores': {
        'store_id': {'type': 'string', 'min': 1},
        'store_name': {'type': 'string', 'min': 1},
        'location': {'type': 'string', 'min': 1},
        'manager': {'type': 'string', 'min': 1}
    },
    'sales': {
        'sale_id': {'type': 'string', 'min': 1},
        'customer_id': {'type': 'string', 'min': 1},
        'product_id': {'type': 'string', 'min': 1},
        'store_id': {'type': 'string', 'min': 1},
        'sale_date': {'type': 'string', 'regex': r'^\d{4}-\d{2}-\d{2}$'},
        'quantity': {'type': 'integer', 'min': 0},
        'total_amount': {'type': 'float', 'min': 0.0}
    },
    'products': {
        'product_id': {'type': 'string', 'min': 1},
        'product_name': {'type': 'string', 'min': 1},
        'category': {'type': 'string', 'min': 1},
        'price': {'type': 'float', 'min': 0.0}
    },
    'inventory': {
        'product_id': {'type': 'string', 'min': 1},
        'store_id': {'type': 'string', 'min': 1},
        'stock_level': {'type': 'integer', 'min': 0},
        'last_updated': {'type': 'string', 'regex': r'^\d{4}-\d{2}-\d{2}$'},
        'supplier_id': {'type': 'string', 'min': 1}
    },
    'suppliers': {
        'supplier_id': {'type': 'string', 'min': 1},
        'supplier_name': {'type': 'string', 'min': 1},
        'contact_name': {'type': 'string', 'min': 1},
        'contact_email': {'type': 'string', 'min': 1}
    },
    'dimdate':{
        'date': {
            'type': 'string',
            'regex': r'^\d{4}-\d{2}-\d{2}$' 
        },
        'day': {
            'type': 'integer',
            'min': 1,
            'max': 31
        },
        'month': {
            'type': 'integer',
            'min': 1,
            'max': 12
        },
        'quarter': {
            'type': 'integer',
            'min': 1,
            'max': 4
        },
        'year': {
            'type': 'integer',
        },
        'day_of_week': {
            'type': 'integer',
            'min':0,
            'max':6
        }
    }
}
