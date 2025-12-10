import mysql.connector
import os
from mysql.connector import Error

def get_db_connection():
    """Create a connection to the MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DB', 'inventory_db')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    """Initialize the database with schema"""
    # Connect without database to create it if it doesn't exist
    try:
        conn = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', '')
        )
        cursor = conn.cursor()
        db_name = os.environ.get('MYSQL_DB', 'inventory_db')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        conn.close()
        
        # Now connect to the database and run schema
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            with open('schema.sql', 'r') as f:
                schema = f.read()
                # Split by semicolon to execute individual statements
                statements = schema.split(';')
                for statement in statements:
                    if statement.strip():
                        cursor.execute(statement)
            conn.commit()
            conn.close()
            print("Database initialized successfully.")
    except Error as e:
        print(f"Error initializing database: {e}")
