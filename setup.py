#!/usr/bin/env python3
"""
Database setup script for Invoice Management System
This script helps you set up MySQL database and initialize the application
"""

import os
import sys
import subprocess
import pymysql
from config import Config

def check_mysql_connection():
    """Check if MySQL is running and accessible"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USERNAME,
            password=Config.MYSQL_PASSWORD
        )
        connection.close()
        print("✅ MySQL connection successful!")
        return True
    except Exception as e:
        print(f"❌ MySQL connection failed: {str(e)}")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USERNAME,
            password=Config.MYSQL_PASSWORD
        )
        
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"✅ Database '{Config.MYSQL_DATABASE}' created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create database: {str(e)}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Invoice Management System with MySQL")
    print("=" * 60)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("📝 Please create a .env file based on env_example.txt")
        print("   Copy env_example.txt to .env and update with your MySQL credentials")
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check MySQL connection
    if not check_mysql_connection():
        print("\n🔧 MySQL Setup Instructions:")
        print("1. Install MySQL Server")
        print("2. Start MySQL service")
        print("3. Update .env file with correct MySQL credentials")
        print("4. Run this script again")
        return False
    
    # Create database
    if not create_database():
        return False
    
    # Initialize database with sample data
    print("\n📊 Initializing database with sample data...")
    try:
        from init_db import main as init_main
        init_main()
    except Exception as e:
        print(f"❌ Failed to initialize database: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Run the application: python app.py")
    print("2. Open browser: http://localhost:5000")
    print("\n🔐 Demo Credentials:")
    print("   Seller: seller@example.com / password")
    print("   Customer: customer@example.com / password")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
