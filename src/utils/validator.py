from cerberus import Validator
from .exceptions import ExtractionError
import logging
from logger import get_logger


logger = get_logger("VALIDATOR")


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
        return True
    else:
        raise ExtractionError(
            f"Data validation failed: {validator.errors}", "VAL001")


def validate_dataframe(df, table_name):

    if table_name not in schema_map:
        logger.info(f"No schema defined for {table_name}, skipping validation")
        return True

    schema = schema_map[table_name]
    validation_issues = []

    # Column-wise validation
    for column_name, column_rules in schema.items():
        if column_name not in df.columns:
            if column_rules.get('required', False):
                validation_issues.append(
                    f"Required column '{column_name}' is missing")
            continue

        column_data = df[column_name]

        # Check for required field nulls
        if column_rules.get('required', False):
            null_count = column_data.isnull().sum()
            if null_count > 0:
                validation_issues.append(
                    f"Column '{column_name}': {null_count} null values found (required field)")

        # Check data type (for string type)
        if column_rules.get('type') == 'string':
            non_string_count = 0
            for value in column_data.dropna():
                if not isinstance(value, str):
                    non_string_count += 1
            if non_string_count > 0:
                validation_issues.append(
                    f"Column '{column_name}': {non_string_count} non-string values found")

        # Check regex patterns
        if 'regex' in column_rules:
            import re
            pattern = column_rules['regex']
            regex_fail_count = 0
            for value in column_data.dropna():
                if isinstance(value, str) and not re.match(pattern, value):
                    regex_fail_count += 1
            if regex_fail_count > 0:
                validation_issues.append(
                    f"Column '{column_name}': {regex_fail_count} values don't match expected pattern")

    # Log validation summary
    if validation_issues:
        logger.warning(f"Column validation issues for {table_name}:")
        for issue in validation_issues:
            logger.warning(f"  - {issue}")
        return False
    else:
        logger.info(
            f"Column validation passed for {table_name}: {len(df)} rows validated")
        return True
