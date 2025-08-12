from cerberus import Validator
from .exceptions import ExtractionError
import logging


logger = logging.getLogger(__name__)


customer_schema = {
    "customer_id": {"type": "string", "required": True},
    "customer_name": {"type": "string"},
    "email": {"type": "string", "regex": r"^\S+@\S+\.\S+$"},
    "phone": {"type": "string"},
    "address": {"type": "string"},

    "signup_date": {"type": "string"}
}

inventory_schema = {
    "product_id": {"type": "string", "required": True},
    "store_id": {"type": "string", "required": True},
    "stock_level": {"type": "string", "regex": r"^\d+$"},
    "last_updated": {"type": "string"},
    "supplier_id": {"type": "string"}
}

product_schema = {
    "product_id": {"type": "string", "required": True},
    "product_name": {"type": "string"},
    "category": {"type": "string"},
    "price": {"type": "string", "regex": r"^\d+\.?\d*$"}
}

sales_schema = {
    "sale_id": {"type": "string", "required": True},
    "customer_id": {"type": "string", "required": True},
    "product_id": {"type": "string", "required": True},
    "store_id": {"type": "string", "required": True},
    "sale_date": {"type": "string"},

    "quantity": {"type": "string", "regex": r"^\d+$"},

    "total_amount": {"type": "string", "regex": r"^\d+\.?\d*$"}
}

store_schema = {
    "store_id": {"type": "string", "required": True},
    "store_name": {"type": "string"},
    "location": {"type": "string"},
    "manager": {"type": "string"}
}

supplier_schema = {
    "supplier_id": {"type": "string", "required": True},
    "supplier_name": {"type": "string"},
    "contact_name": {"type": "string"},
    "contact_email": {"type": "string", "regex": r"^\S+@\S+\.\S+$"}
}

schema_map = {
    "customers": customer_schema,
    "inventory": inventory_schema,
    "products": product_schema,
    "sales": sales_schema,
    "stores": store_schema,
    "suppliers": supplier_schema
}


def validate_data(data, schema):

    validator = Validator(schema)
    if validator.validate(data):
        logger.debug("Data validation passed.")
        return True
    else:
        raise ExtractionError(
            f"Data validation failed: {validator.errors}", "VAL001")


def validate_dataframe(df, table_name):

    if table_name not in schema_map:
        logger.info(f"No schema defined for {table_name}, skipping validation")
        return True

    schema = schema_map[table_name]
    error_count = 0

    for index, row in df.iterrows():
        try:
            validate_data(row.to_dict(), schema)
        except ExtractionError as e:
            error_count += 1
            if error_count <= 3:  # Only log first 3 errors
                logger.warning(
                    f"Row {index + 1} validation failed: {e.message}")

    if error_count > 0:
        logger.warning(
            f"Validation failed for {table_name}: {error_count} errors out of {len(df)} rows")
        if error_count > 3:
            logger.warning(f"... and {error_count - 3} more errors")
        return False
    else:
        logger.info(
            f" Validation passed for {table_name}: {len(df)} rows valid")
        return True
