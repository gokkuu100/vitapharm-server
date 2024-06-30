import pymysql

try:
    connection = pymysql.connect(
        host='vitapharmdb-1.cj6ico0sizn7.eu-north-1.rds.amazonaws.com',
        user='',
        password='',
        database=''
    )
    print("Connection successful")
except Exception as e:
    print(f"Error: {e}")
finally:
    connection.close()
