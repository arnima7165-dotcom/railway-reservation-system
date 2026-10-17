
from db import get_connection

connection = None
cursor = None

try:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT DATABASE()")
    print("Connected to database:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM Trains")
    print("Number of trains:", cursor.fetchone()[0])

except Exception as error:
    print("Connection failed:", error)

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()
