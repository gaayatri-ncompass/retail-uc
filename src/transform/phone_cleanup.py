import re
import pandas as pd

def clean_phone_number(phone):
    if pd.isnull(phone):
        return None

    phone = re.sub(r'x\d+.*$', '', str(phone))

    digits = re.sub(r'\D', '', phone)

    digits = digits[-10:]

    if len(digits) == 10:
        return f"+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    else:
        return None

def clean_phone_numbers(df, column="phone"):
    df[column] = df[column].apply(clean_phone_number)
    return df