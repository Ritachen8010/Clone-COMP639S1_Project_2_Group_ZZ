-- Create the database
CREATE DATABASE BBBB;
USE BBBB;

-- account table 
CREATE TABLE account(
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('manager', 'staff', 'customer') NOT NULL
);

CREATE TABLE manager(
    account_id INT UNIQUE NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    position varchar(100) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(255) NOT NULL UNIQUE,
    `status` Enum ('active', 'inactive') NOT NULL default 'active',
    FOREIGN KEY (account_id) REFERENCES account(account_id)
);
CREATE TABLE staff(
    account_id INT UNIQUE NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
	phone VARCHAR(15),
    email VARCHAR(255) NOT NULL UNIQUE,
    `status` Enum ('active', 'inactive') NOT NULL default 'active',
    FOREIGN KEY (account_id) REFERENCES account(account_id)
);

CREATE TABLE customer(
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT UNIQUE NOT NULL,
    first_name varchar(100) NOT NULL,
    family_name varchar(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `status` Enum ('active', 'inactive') NOT NULL default 'active',
    FOREIGN KEY (account_id) REFERENCES account(account_id)
);




CREATE TABLE product(
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category ENUM('food', 'drinks', 'merchandise', 'accommodation') NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    is_available BOOLEAN NOT NULL
);

CREATE TABLE orders(
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATETIME NOT NULL,
    status ENUM('pending', 'completed', 'cancelled') NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES account(account_id)
);

CREATE TABLE order_items(
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    special_requests TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);
CREATE TABLE inventory(
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    quantity_available INT NOT NULL,
    last_updated DATETIME NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);
CREATE TABLE accommodation(
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_type ENUM('dorm', 'twin', 'queen') NOT NULL,
    capacity INT NOT NULL,
    is_available BOOLEAN NOT NULL
);
CREATE TABLE bookings(
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    room_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('booked', 'cancelled', 'completed') NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES account(account_id),
    FOREIGN KEY (room_id) REFERENCES accommodation(room_id)
);
CREATE TABLE promotions(
    promotion_id INT AUTO_INCREMENT PRIMARY KEY,
    description TEXT,
    discount_rate DECIMAL(5, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);
CREATE TABLE customer_messages(
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    content TEXT NOT NULL,
    date_sent DATETIME NOT NULL,
    staff_response TEXT,
    date_responded DATETIME,
    FOREIGN KEY (customer_id) REFERENCES account(account_id)
);

INSERT INTO account (username, `password`, `role`) VALUES 
('aa', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'manager'),
('bb', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'staff'),
('cc', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'customer');


INSERT INTO manager (account_id, first_name, last_name, position, phone, email) 
VALUES (1, 'aa', 'AA', 'Manager', '0210123456', 'aa@gmail.com');
INSERT INTO staff (account_id, first_name, last_name, phone, email) 
VALUES (2, 'bb', 'BB', '0210234567', 'bb@gmail.com');
INSERT INTO customer (account_id, first_name, family_name, email, phone, created_at, status) 
VALUES (3, 'cc', 'CC', 'cc@gmail.com', '0210345678', CURRENT_TIMESTAMP, 'active');
