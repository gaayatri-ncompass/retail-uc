
import mysql.connector

try:

    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='deva'
    )
    cursor = conn.cursor()

    # Check if warehouse database exists
    cursor.execute("SHOW DATABASES LIKE 'warehousedb'")
    result = cursor.fetchone()

    if result:
        print("warehousedb exists")

        # Connect to warehouse database
        cursor.execute("USE warehousedb")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"Tables in warehousedb: {[t[0] for t in tables]}")

        # Check counts
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"{table_name}: {count:,} records")
            except Exception as e:
                print(f"{table_name}: Error - {e}")
    else:
        print("warehousedb does not exist")

    conn.close()

except Exception as e:
    print(f"Connection error: {e}")
    import traceback
    traceback.print_exc()
