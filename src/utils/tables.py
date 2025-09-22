def get_tables(db,schema):
    query = f"""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
      AND table_type = 'BASE TABLE';
    """
    df = db.query_df(query)
    return df.iloc[:, 0].tolist()


def get_primary_key(db, schema, table_name):
    query = f"""
    SELECT column_name
    FROM information_schema.key_column_usage
    WHERE table_schema = '{schema}'
    AND table_name = '{table_name}'
    AND constraint_name IN (
      SELECT constraint_name
      FROM information_schema.table_constraints
      WHERE constraint_type = 'PRIMARY KEY'
        AND table_schema = '{schema}'
        AND table_name = '{table_name}'
  );
    """
    df = db.query_df(query)
    if df is not None and not df.empty:
        return df.iloc[0, 0]
    
    raise ValueError(f"No primary key found for table '{table_name}' in schema '{schema}'")

