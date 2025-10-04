import sqlite3

def create_test_database(db_name, table_name, columns, data):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create table
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})")

    # Insert data
    placeholders = ', '.join(['?'] * len(columns))
    cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Database 1
    columns1 = ["id INTEGER", "name TEXT", "email TEXT"]
    data1 = [
        (1, "Alice", "alice@example.com"),
        (2, "Bob", "bob@example.com"),
        (3, "Charlie", "charlie@example.com")
    ]
    create_test_database("test1.db", "users", columns1, data1)

    # Database 2
    columns2 = ["product_id INTEGER", "product_name TEXT", "price REAL"]
    data2 = [
        (101, "Laptop", 1200.50),
        (102, "Mouse", 25.00),
        (103, "Keyboard", 75.99)
    ]
    create_test_database("test2.db", "products", columns2, data2)

    print("Test databases created successfully.")