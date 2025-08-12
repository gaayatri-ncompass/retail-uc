import pandas as pd

def split_address(df, column="address"):
    address_parts = df[column].str.extract(r'(?P<street>.*?),\s*(?P<city>.*?),\s*(?P<state>[A-Za-z]{2})\s*(?P<zip>\d{5})')
    return pd.concat([df.drop(columns=[column]), address_parts], axis=1)
