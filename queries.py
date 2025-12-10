from models import Seller, Customer, Product, Invoice, InvoiceItem, Activity
from database import get_db_connection
from datetime import datetime, date
from decimal import Decimal

# --- Helper Functions ---

def get_row_as_dict(cursor):
    """Helper to fetch one row as dict"""
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None

def get_all_rows_as_dict(cursor):
    """Helper to fetch all rows as dicts"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def log_activity(user_id, user_role, action_type, description):
    """Log an activity for the current user"""
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO activities (user_id, user_role, action_type, description, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, user_role, action_type, description, datetime.utcnow()))
        conn.commit()
    finally:
        conn.close()

def get_recent_activities(user_id, limit=5):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM activities WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s"
        cursor.execute(query, (user_id, limit))
        rows = get_all_rows_as_dict(cursor)
        return [Activity(**row) for row in rows]
    finally:
        conn.close()

def generate_next_product_id():
    """Generate next product ID using dictionary-based approach"""
    conn = get_db_connection()
    if not conn: return "P001"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT p_id FROM products")
        existing_ids = {row[0] for row in cursor.fetchall()}
        
        max_num = 0
        for pid in existing_ids:
            if pid.startswith('P') and len(pid) == 4:
                try:
                    num = int(pid[1:])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    continue
        
        while True:
            max_num += 1
            candidate = f"P{max_num:03d}"
            if candidate not in existing_ids:
                return candidate
    finally:
        conn.close()

def update_overdue_invoices():
    """Update invoice status to overdue if current date > due_date"""
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        today = date.today()
        query = """
            UPDATE invoices 
            SET status = 'overdue' 
            WHERE status IN ('pending', 'overdue') 
            AND due_date IS NOT NULL 
            AND due_date < %s
            AND status != 'overdue'
        """
        cursor.execute(query, (today,))
        conn.commit()
    finally:
        conn.close()

def restore_stock_on_cancellation(invoice):
    """Restore product stock when invoice is cancelled"""
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Invoice items are already attached to invoice object in get_invoice_by_id
        for item in invoice.invoice_items:
            # Update stock directly in DB
            query = "UPDATE products SET p_stock = p_stock + %s WHERE p_id = %s"
            cursor.execute(query, (item.item_quantity, item.p_id))
        conn.commit()
    finally:
        conn.close()

# --- Auth Queries ---

def get_seller_by_email(email):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sellers WHERE s_email = %s", (email,))
        row = get_row_as_dict(cursor)
        if row:
            return Seller(**row)
        return None
    finally:
        conn.close()

def get_seller_count():
    conn = get_db_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sellers")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def create_seller(s_id, name, email, address, phone, password):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        seller = Seller(s_id, name, email, address, phone, password)
        seller.set_password(password) # Ensure password is set (though passed in init)
        
        query = """
            INSERT INTO sellers (s_id, s_name, s_email, s_address, s_phone, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (seller.s_id, seller.s_name, seller.s_email, seller.s_address, seller.s_phone, seller.password))
        conn.commit()
        return seller
    finally:
        conn.close()

# --- Dashboard Queries ---

def get_seller_dashboard_stats(seller_id):
    conn = get_db_connection()
    if not conn: return {}
    try:
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE s_id = %s", (seller_id,))
        stats['total_products'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customers WHERE s_id = %s", (seller_id,))
        stats['total_customers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE s_id = %s", (seller_id,))
        stats['total_invoices'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE s_id = %s AND status = 'paid'", (seller_id,))
        stats['paid_invoices'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE s_id = %s AND status = 'pending'", (seller_id,))
        stats['unpaid_invoices'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE s_id = %s AND status = 'overdue'", (seller_id,))
        stats['overdue_invoices'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(amount) FROM invoices WHERE s_id = %s AND status = 'paid'", (seller_id,))
        res = cursor.fetchone()[0]
        stats['revenue_collected'] = float(res) if res else 0.0
        
        cursor.execute("SELECT SUM(amount) FROM invoices WHERE s_id = %s AND status IN ('pending', 'overdue')", (seller_id,))
        res = cursor.fetchone()[0]
        stats['revenue_due'] = float(res) if res else 0.0
        
        return stats
    finally:
        conn.close()

def get_admin_dashboard_stats():
    conn = get_db_connection()
    if not conn: return {}
    try:
        cursor = conn.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM sellers")
        stats['total_sellers'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM customers")
        stats['total_customers'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products")
        stats['total_products'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM invoices")
        stats['total_invoices'] = cursor.fetchone()[0]
        return stats
    finally:
        conn.close()

def get_all_sellers():
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sellers ORDER BY s_name ASC")
        rows = get_all_rows_as_dict(cursor)
        return [Seller(**row) for row in rows]
    finally:
        conn.close()

def get_seller_by_id(seller_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sellers WHERE s_id = %s", (seller_id,))
        row = get_row_as_dict(cursor)
        if row:
            return Seller(**row)
        return None
    finally:
        conn.close()

def update_seller(seller, name=None, email=None, phone=None, address=None, password=None):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        
        if name:
            updates.append("s_name = %s")
            params.append(name)
            seller.s_name = name
        if email:
            updates.append("s_email = %s")
            params.append(email)
            seller.s_email = email
        if phone:
            updates.append("s_phone = %s")
            params.append(phone)
            seller.s_phone = phone
        if address:
            updates.append("s_address = %s")
            params.append(address)
            seller.s_address = address
        if password:
            updates.append("password = %s")
            params.append(password)
            seller.password = password
            
        if updates:
            params.append(seller.s_id)
            query = f"UPDATE sellers SET {', '.join(updates)} WHERE s_id = %s"
            cursor.execute(query, tuple(params))
            conn.commit()
    finally:
        conn.close()

def delete_seller(seller):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sellers WHERE s_id = %s", (seller.s_id,))
        conn.commit()
    finally:
        conn.close()

# --- Product Queries ---

def get_products_by_seller(seller_id, query=None):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM products WHERE s_id = %s"
        params = [seller_id]
        
        if query:
            sql += " AND p_name LIKE %s"
            params.append(f"%{query}%")
            
        cursor.execute(sql, tuple(params))
        rows = get_all_rows_as_dict(cursor)
        return [Product(**row) for row in rows]
    finally:
        conn.close()

def get_product_by_id(product_id, seller_id=None):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM products WHERE p_id = %s"
        params = [product_id]
        
        if seller_id:
            sql += " AND s_id = %s"
            params.append(seller_id)
            
        cursor.execute(sql, tuple(params))
        row = get_row_as_dict(cursor)
        if row:
            return Product(**row)
        return None
    finally:
        conn.close()

def add_product(name, price, description, stock, seller_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        product_id = generate_next_product_id()
        cursor = conn.cursor()
        query = """
            INSERT INTO products (p_id, p_name, p_price, p_description, p_stock, s_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (product_id, name, price, description, stock, seller_id))
        conn.commit()
        return Product(product_id, name, price, description, stock, seller_id)
    finally:
        conn.close()

def update_product(product, name, price, description, stock):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        query = """
            UPDATE products 
            SET p_name = %s, p_price = %s, p_description = %s, p_stock = %s 
            WHERE p_id = %s
        """
        cursor.execute(query, (name, price, description, stock, product.p_id))
        conn.commit()
        # Update object state
        product.p_name = name
        product.p_price = price
        product.p_description = description
        product.p_stock = stock
    finally:
        conn.close()

def update_product_stock(product_id, new_stock):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET p_stock = %s WHERE p_id = %s", (new_stock, product_id))
        conn.commit()
    finally:
        conn.close()

def delete_product(product):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE p_id = %s", (product.p_id,))
        conn.commit()
    finally:
        conn.close()

def check_product_in_invoices(product_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoice_items WHERE p_id = %s", (product_id,))
        rows = get_all_rows_as_dict(cursor)
        return [InvoiceItem(**row) for row in rows]
    finally:
        conn.close()

# --- Customer Queries ---

def get_customers_by_seller(seller_id, query=None):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM customers WHERE s_id = %s"
        params = [seller_id]
        
        if query:
            sql += " AND c_name LIKE %s"
            params.append(f"%{query}%")
            
        sql += " ORDER BY c_name ASC"
        cursor.execute(sql, tuple(params))
        rows = get_all_rows_as_dict(cursor)
        return [Customer(**row) for row in rows]
    finally:
        conn.close()

def get_customer_by_id(customer_id, seller_id=None):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM customers WHERE c_id = %s"
        params = [customer_id]
        
        if seller_id:
            sql += " AND s_id = %s"
            params.append(seller_id)
            
        cursor.execute(sql, tuple(params))
        row = get_row_as_dict(cursor)
        if row:
            return Customer(**row)
        return None
    finally:
        conn.close()

def get_customer_by_email(email):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE c_email = %s", (email,))
        row = get_row_as_dict(cursor)
        if row:
            return Customer(**row)
        return None
    finally:
        conn.close()

def get_customer_count():
    conn = get_db_connection()
    if not conn: return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        return cursor.fetchone()[0]
    finally:
        conn.close()

def create_customer(c_id, name, email, phone, address, seller_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO customers (c_id, c_name, c_email, c_phone_no, c_address, password, s_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (c_id, name, email, phone, address, '', seller_id))
        conn.commit()
        return Customer(c_id, name, email, phone, address, '', seller_id)
    finally:
        conn.close()

def update_customer(customer, name, email, phone, address):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        query = """
            UPDATE customers 
            SET c_name = %s, c_email = %s, c_phone_no = %s, c_address = %s 
            WHERE c_id = %s
        """
        cursor.execute(query, (name, email, phone, address, customer.c_id))
        conn.commit()
        # Update object
        customer.c_name = name
        customer.c_email = email
        customer.c_phone_no = phone
        customer.c_address = address
    finally:
        conn.close()

def delete_customer(customer):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE c_id = %s", (customer.c_id,))
        conn.commit()
    finally:
        conn.close()

def check_customer_in_invoices(customer_id, seller_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE c_id = %s AND s_id = %s", (customer_id, seller_id))
        rows = get_all_rows_as_dict(cursor)
        return [Invoice(**row) for row in rows]
    finally:
        conn.close()

def get_customer_analytics(seller_id, start_date_str=None, end_date_str=None):
    conn = get_db_connection()
    if not conn: return {
        'most_invoices': None, 'least_invoices': None,
        'most_purchased': None, 'least_purchased': None
    }
    try:
        cursor = conn.cursor()
        
        # Base WHERE clause
        where_clause = "WHERE i.s_id = %s AND i.status = 'paid'"
        params = [seller_id]
        
        if start_date_str:
            where_clause += " AND i.invoice_datetime >= %s"
            params.append(start_date_str)
        if end_date_str:
            where_clause += " AND i.invoice_datetime <= %s"
            params.append(end_date_str + " 23:59:59")
            
        # Common query part
        base_query = f"""
            SELECT c.*, COUNT(i.invoice_no) as invoice_count, SUM(i.amount) as total_purchased
            FROM customers c
            JOIN invoices i ON c.c_id = i.c_id
            {where_clause}
            GROUP BY c.c_id
        """
        
        # Most invoices
        cursor.execute(f"{base_query} ORDER BY invoice_count DESC LIMIT 1", tuple(params))
        row = get_row_as_dict(cursor)
        most_invoices = Customer(**{k: v for k, v in row.items() if k in vars(Customer())}) if row else None
        
        # Most purchased
        cursor.execute(f"{base_query} ORDER BY total_purchased DESC LIMIT 1", tuple(params))
        row = get_row_as_dict(cursor)
        most_purchased = Customer(**{k: v for k, v in row.items() if k in vars(Customer())}) if row else None
        
        # Least categories (need LEFT JOIN to include 0s)
        # This is complex in raw SQL to match exact logic of "least", simplifying to just those with invoices for now or doing a full left join
        # To match original logic:
        
        left_join_query = f"""
            SELECT c.*, 
                   COUNT(i.invoice_no) as invoice_count, 
                   SUM(CASE WHEN i.status = 'paid' THEN i.amount ELSE 0 END) as total_purchased
            FROM customers c
            LEFT JOIN invoices i ON c.c_id = i.c_id AND i.s_id = %s
            WHERE c.s_id = %s
        """
        lj_params = [seller_id, seller_id]
        
        if start_date_str:
            left_join_query += " AND (i.invoice_datetime >= %s OR i.invoice_no IS NULL)"
            lj_params.append(start_date_str)
        if end_date_str:
            left_join_query += " AND (i.invoice_datetime <= %s OR i.invoice_no IS NULL)"
            lj_params.append(end_date_str + " 23:59:59")
            
        left_join_query += " GROUP BY c.c_id"
        
        # Least invoices
        cursor.execute(f"{left_join_query} ORDER BY invoice_count ASC LIMIT 1", tuple(lj_params))
        row = get_row_as_dict(cursor)
        least_invoices = Customer(**{k: v for k, v in row.items() if k in vars(Customer())}) if row else None
        
        # Least purchased
        cursor.execute(f"{left_join_query} ORDER BY total_purchased ASC LIMIT 1", tuple(lj_params))
        row = get_row_as_dict(cursor)
        least_purchased = Customer(**{k: v for k, v in row.items() if k in vars(Customer())}) if row else None

        return {
            'most_invoices': most_invoices,
            'least_invoices': least_invoices,
            'most_purchased': most_purchased,
            'least_purchased': least_purchased
        }
    finally:
        conn.close()

# --- Invoice Queries ---

def _attach_customer_and_items(cursor, invoices):
    """Helper to attach customer and items to invoice objects"""
    for invoice in invoices:
        # Attach Customer
        cursor.execute("SELECT * FROM customers WHERE c_id = %s", (invoice.c_id,))
        c_row = get_row_as_dict(cursor)
        if c_row:
            invoice.customer = Customer(**c_row)
            
        # Attach Items
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_no = %s", (invoice.invoice_no,))
        i_rows = get_all_rows_as_dict(cursor)
        invoice.invoice_items = []
        for i_row in i_rows:
            item = InvoiceItem(**i_row)
            # Attach Product to Item
            cursor.execute("SELECT * FROM products WHERE p_id = %s", (item.p_id,))
            p_row = get_row_as_dict(cursor)
            if p_row:
                item.product = Product(**p_row)
            invoice.invoice_items.append(item)
    return invoices

def get_invoices_by_seller(seller_id, query=None, customer_query=None, status=None, start_date=None, end_date=None, min_amount=None, max_amount=None):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        sql = "SELECT i.* FROM invoices i"
        if customer_query:
            sql += " JOIN customers c ON i.c_id = c.c_id"
            
        sql += " WHERE i.s_id = %s"
        params = [seller_id]
        
        if query:
            sql += " AND i.invoice_no LIKE %s"
            params.append(f"%{query}%")
        
        if customer_query:
            sql += " AND (c.c_name LIKE %s OR c.c_email LIKE %s)"
            params.append(f"%{customer_query}%")
            params.append(f"%{customer_query}%")
            
        if status:
            sql += " AND i.status = %s"
            params.append(status)
            
        if start_date:
            sql += " AND i.invoice_datetime >= %s"
            params.append(start_date)
            
        if end_date:
            sql += " AND i.invoice_datetime <= %s"
            params.append(end_date + " 23:59:59")
            
        if min_amount:
            sql += " AND i.amount >= %s"
            params.append(min_amount)
            
        if max_amount:
            sql += " AND i.amount <= %s"
            params.append(max_amount)
            
        sql += " ORDER BY i.invoice_datetime DESC"
        
        cursor.execute(sql, tuple(params))
        rows = get_all_rows_as_dict(cursor)
        invoices = [Invoice(**row) for row in rows]
        
        # Attach related objects (N+1 problem here, but safe for small scale)
        return _attach_customer_and_items(cursor, invoices)
        
    finally:
        conn.close()

def get_invoice_by_id(invoice_id, seller_id=None):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM invoices WHERE invoice_no = %s"
        params = [invoice_id]
        
        if seller_id:
            sql += " AND s_id = %s"
            params.append(seller_id)
            
        cursor.execute(sql, tuple(params))
        row = get_row_as_dict(cursor)
        if row:
            invoice = Invoice(**row)
            return _attach_customer_and_items(cursor, [invoice])[0]
        return None
    finally:
        conn.close()

def get_invoices_by_customer(customer_id, seller_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE c_id = %s AND s_id = %s", (customer_id, seller_id))
        rows = get_all_rows_as_dict(cursor)
        invoices = [Invoice(**row) for row in rows]
        return _attach_customer_and_items(cursor, invoices)
    finally:
        conn.close()

def generate_invoice_id():
    conn = get_db_connection()
    if not conn: return "INV-001"
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT invoice_no FROM invoices")
        existing_ids = {row[0] for row in cursor.fetchall()}
        
        invoice_num = 1
        while True:
            invoice_id = f"INV-{invoice_num:03d}"
            if invoice_id not in existing_ids:
                return invoice_id
            invoice_num += 1
    finally:
        conn.close()

def create_invoice(invoice_id, due_date, status, tax, amount, seller_id, customer_id, items):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        
        # Create Invoice
        query = """
            INSERT INTO invoices (invoice_no, invoice_datetime, due_date, status, tax, amount, s_id, c_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (invoice_id, datetime.utcnow(), due_date, status, tax, amount, seller_id, customer_id))
        
        # Create Items and Update Stock
        for item in items:
            # Create Item
            item_query = """
                INSERT INTO invoice_items (invoice_no, p_id, item_quantity, discount)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(item_query, (invoice_id, item['product'].p_id, item['quantity'], item['discount']))
            
            # Update Stock
            stock_query = "UPDATE products SET p_stock = p_stock - %s WHERE p_id = %s"
            cursor.execute(stock_query, (item['quantity'], item['product'].p_id))
            
        conn.commit()
        
        # Return new invoice object (simplified, re-fetch if needed)
        return Invoice(invoice_id, datetime.utcnow(), due_date, status, tax, amount, seller_id, customer_id)
    finally:
        conn.close()

def update_invoice_status(invoice, status):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE invoices SET status = %s WHERE invoice_no = %s", (status, invoice.invoice_no))
        conn.commit()
        invoice.status = status
    finally:
        conn.close()

def update_invoice_details(invoice, tax=None, due_date=None, amount=None):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        
        if tax is not None:
            updates.append("tax = %s")
            params.append(tax)
            invoice.tax = tax
            
        if due_date is not None:
            updates.append("due_date = %s")
            params.append(due_date)
            invoice.due_date = due_date
            
        if amount is not None:
            updates.append("amount = %s")
            params.append(amount)
            invoice.amount = amount
            
        if updates:
            params.append(invoice.invoice_no)
            query = f"UPDATE invoices SET {', '.join(updates)} WHERE invoice_no = %s"
            cursor.execute(query, tuple(params))
            conn.commit()
    finally:
        conn.close()

def update_invoice_item(item):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        query = """
            UPDATE invoice_items 
            SET item_quantity = %s, discount = %s, p_id = %s
            WHERE item_id = %s
        """
        cursor.execute(query, (item.item_quantity, item.discount, item.p_id, item.item_id))
        conn.commit()
    finally:
        conn.close()

def delete_invoice_item(item):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoice_items WHERE item_id = %s", (item.item_id,))
        conn.commit()
    finally:
        conn.close()

def add_invoice_item(invoice_no, product_id, quantity, discount):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO invoice_items (invoice_no, p_id, item_quantity, discount)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (invoice_no, product_id, quantity, discount))
        conn.commit()
        # Return object
        return InvoiceItem(None, invoice_no, product_id, quantity, discount)
    finally:
        conn.close()

def delete_invoice(invoice):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        # Cascade delete should handle items, but let's be safe if schema doesn't support it (schema.sql has ON DELETE CASCADE)
        cursor.execute("DELETE FROM invoices WHERE invoice_no = %s", (invoice.invoice_no,))
        conn.commit()
    finally:
        conn.close()
