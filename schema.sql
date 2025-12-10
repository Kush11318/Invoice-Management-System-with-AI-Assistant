CREATE TABLE IF NOT EXISTS sellers (
    s_id VARCHAR(10) PRIMARY KEY,
    s_name VARCHAR(100) NOT NULL,
    s_email VARCHAR(100) NOT NULL UNIQUE,
    s_address TEXT NOT NULL,
    s_phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    c_id VARCHAR(10) PRIMARY KEY,
    c_name VARCHAR(100) NOT NULL,
    c_email VARCHAR(100) NOT NULL UNIQUE,
    c_phone_no VARCHAR(20) NOT NULL,
    c_address TEXT NOT NULL,
    password VARCHAR(255),
    s_id VARCHAR(10),
    FOREIGN KEY (s_id) REFERENCES sellers(s_id)
);

CREATE TABLE IF NOT EXISTS products (
    p_id VARCHAR(10) PRIMARY KEY,
    p_name VARCHAR(100) NOT NULL,
    p_price DECIMAL(10, 2) NOT NULL,
    p_description TEXT,
    p_stock INT NOT NULL DEFAULT 0,
    s_id VARCHAR(10) NOT NULL,
    FOREIGN KEY (s_id) REFERENCES sellers(s_id)
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_no VARCHAR(20) PRIMARY KEY,
    invoice_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    tax DECIMAL(10, 2) NOT NULL DEFAULT 0,
    amount DECIMAL(10, 2) NOT NULL,
    s_id VARCHAR(10) NOT NULL,
    c_id VARCHAR(10) NOT NULL,
    FOREIGN KEY (s_id) REFERENCES sellers(s_id),
    FOREIGN KEY (c_id) REFERENCES customers(c_id)
);

CREATE TABLE IF NOT EXISTS invoice_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    p_id VARCHAR(10) NOT NULL,
    item_quantity INT NOT NULL,
    discount DECIMAL(10, 2) NOT NULL DEFAULT 0,
    FOREIGN KEY (invoice_no) REFERENCES invoices(invoice_no) ON DELETE CASCADE,
    FOREIGN KEY (p_id) REFERENCES products(p_id)
);

CREATE TABLE IF NOT EXISTS activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(10) NOT NULL,
    user_role VARCHAR(20) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
