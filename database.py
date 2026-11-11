import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def create_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer'
        );

        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
            stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            total_price NUMERIC(10, 2) NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price NUMERIC(10, 2) NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def add_user(username, hashed_password, role="customer"):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, hashed_password, role) VALUES (%s, %s, %s)",
        (username, hashed_password, role),
    )
    conn.commit()
    conn.close()


def get_user(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, hashed_password, role FROM users WHERE username = %s",
        (username,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


def set_user_role(username, role):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET role = %s WHERE username = %s",
        (role, username),
    )
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    return updated

def add_product(name, description, price, stock):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price, stock) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (name, description, price, stock),
    )
    product_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return product_id


def get_all_products():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, price, stock FROM products ORDER BY id"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_product(product_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, description, price, stock FROM products WHERE id = %s",
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return row


if __name__ == "__main__":
    create_tables()
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public'"
    )
    print(cursor.fetchall())
    conn.close()

if __name__ == "__main__":
    create_tables()
    add_user("testuster", "fakehash")
    print(get_user("testuster"))
