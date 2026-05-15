import sqlite3
import os

DB_PATH = "db.sqlite3"


def get_connection():
    if not os.path.exists(DB_PATH):
        print("❌ db.sqlite3 not found in current directory")
        exit(1)
    return sqlite3.connect(DB_PATH)


def list_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name;
    """)
    tables = cursor.fetchall()

    print("\n📦 Tables in database:\n")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table[0]}")
    print()
    return [t[0] for t in tables]


def print_table(conn, table_name):
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        # get column names
        column_names = [description[0] for description in cursor.description]

        print(f"\n📊 Table: {table_name}")
        print("-" * 50)

        print(" | ".join(column_names))
        print("-" * 50)

        for row in rows:
            print(" | ".join(str(x) for x in row))

        print(f"\nTotal rows: {len(rows)}\n")

    except sqlite3.OperationalError as e:
        print(f"❌ Error reading table: {e}")


def main():
    conn = get_connection()

    while True:
        print("=== SQLite Browser ===")
        print("1. List all tables")
        print("2. Print table contents")
        print("3. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            list_tables(conn)

        elif choice == "2":
            tables = list_tables(conn)
            if not tables:
                print("No tables found.")
                continue

            table_name = input("Enter table name: ").strip()
            if table_name not in tables:
                print("❌ Invalid table name")
                continue

            print_table(conn, table_name)

        elif choice == "3":
            print("Goodbye 👋")
            break

        else:
            print("❌ Invalid option\n")


if __name__ == "__main__":
    main()