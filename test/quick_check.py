import mysql.connector
conn = mysql.connector.connect(
    host='localhost', user='root', password='deva', database='warehousedb')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM factsales')
count = cursor.fetchone()[0]
print(f'factsales: {count:,} records')
conn.close()
