-- =========================
-- DRESS RENTAL DATABASE SETUP
-- =========================

-- Optional: Create database
CREATE DATABASE IF NOT EXISTS dress_rental;
USE dress_rental;

-- =========================
-- DROP TABLES (to avoid conflicts)
-- =========================
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS penalty_fees;
DROP TABLE IF EXISTS return_assessments;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS rentals;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS customers;

SET FOREIGN_KEY_CHECKS = 1;

-- =========================
-- TABLE CREATION
-- =========================

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    role ENUM('customer', 'employee') DEFAULT 'customer'
);

CREATE TABLE inventory (
    dress_id INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    size VARCHAR(10) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    color VARCHAR (255) NOT NULL,
    img VARCHAR (255) NOT NULL,
    unavailable_dates JSON,
    is_available BOOLEAN DEFAULT TRUE
);

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    dress_id INT NOT NULL,
    calendar_event_id VARCHAR(255),
    slot_datetime DATETIME NOT NULL,
    status ENUM('CONFIRMED', 'CANCELLED') DEFAULT 'CONFIRMED',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (dress_id) REFERENCES inventory(dress_id)
);

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status ENUM('PENDING', 'SENT', 'FAILED') DEFAULT 'PENDING',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE rentals (
    rental_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    dress_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('ACTIVE', 'COMPLETED', 'CANCELLED') DEFAULT 'ACTIVE',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (dress_id) REFERENCES inventory(dress_id)
);

CREATE TABLE return_assessments (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    rental_id INT NOT NULL,
    dress_id INT NOT NULL,
    assessment_date DATETIME NOT NULL,
    is_late BOOLEAN DEFAULT FALSE,
    is_damaged BOOLEAN DEFAULT FALSE,
    damage_description TEXT,
    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id),
    FOREIGN KEY (dress_id) REFERENCES inventory(dress_id)
);

CREATE TABLE penalty_fees (
    penalty_id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    late_fee DECIMAL(10, 2) DEFAULT 0.00,
    damage_fee DECIMAL(10, 2) DEFAULT 0.00,
    total_penalty DECIMAL(10, 2) DEFAULT 0.00,
    FOREIGN KEY (assessment_id) REFERENCES return_assessments(assessment_id)
);

CREATE TABLE invoices (
  invoice_id INT AUTO_INCREMENT PRIMARY KEY,
  rental_id INT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  type ENUM('RENTAL', 'PENALTY') NOT NULL,
  stripe_id VARCHAR(100),
  status ENUM('PENDING', 'PAID', 'FAILED', 'REFUNDED') DEFAULT 'PENDING',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
);

-- =========================
-- INSERT DATA
-- =========================

INSERT INTO customers (name, email, password_hash, role) VALUES
('Alice Smith', 'alice@user.com', 'user123', 'customer'),
('Bob Jones', 'bob@user.com', 'user123', 'customer'),
('Chloe Davis', 'chloe@user.com', 'user123', 'customer'),
('Sarah Employee', 'sarah@staff.com', 'staff123', 'employee'),
('James Employee', 'james@staff.com', 'staff123', 'employee');

INSERT INTO inventory (dress_id, name, size, price, color, img, unavailable_dates, is_available) VALUES
(101, 'Blush Satin Gown', 'S',   80.00, 'Pink', '/images/dress_pink.jpeg', '["2026-04-16","2026-04-17","2026-04-18","2026-04-19"]', TRUE),
(102, 'Royal Blue Gown', 'M',   120.00, 'Blue', '/images/dress_turquiose.jpeg', '["2026-05-21","2026-05-22","2026-05-23"]',              TRUE),
(103, 'Emerald Chiffon', 'L',   95.00, 'Green', '/images/dress_green.jpeg', '[]',                                                    FALSE),
(201, 'Ivory Lace Maxi', 'S',   80.00,  'White', '/images/dress_white.jpeg', '["2026-06-01","2026-06-02"]',                           TRUE),
(202, 'Navy Velvet', 'M',   120.00, 'Navy', '/images/dress_blue.jpeg', '["2026-03-25","2026-03-26","2026-03-30","2026-03-31"]', TRUE),
(203, 'Lipstick Tulle', 'L', 90.00, 'Red', '/images/dress_red.jpeg', '["2026-04-01"]',                                        TRUE);

INSERT INTO bookings (customer_id, dress_id, calendar_event_id, slot_datetime, status) VALUES
(1, 101, 'evt_xyz123', '2026-04-15 10:00:00', 'CONFIRMED'),
(2, 102, 'evt_abc456', '2026-05-20 14:30:00', 'CONFIRMED'),
(3, 103, 'evt_def789', '2026-03-01 09:00:00', 'CANCELLED');

INSERT INTO notifications (customer_id, email, message, status) VALUES
(1, 'alice@example.com', 'Your fitting is confirmed for April 15.', 'SENT'),
(2, 'bob@example.com', 'Reminder: Upcoming appointment next month.', 'PENDING'),
(3, 'chloe@example.com', 'Your booking has been successfully cancelled.', 'SENT');

INSERT INTO rentals (customer_id, dress_id, start_date, end_date, status) VALUES
(1, 201, '2026-03-10', '2026-03-14', 'COMPLETED'),
(2, 202, '2026-03-18', '2026-03-22', 'ACTIVE'),
(3, 203, '2026-02-01', '2026-02-05', 'COMPLETED');

INSERT INTO return_assessments (rental_id, dress_id, assessment_date, is_late, is_damaged, damage_description) VALUES
(1, 201, '2026-03-14 15:00:00', FALSE, FALSE, NULL),
(3, 203, '2026-02-07 10:00:00', TRUE, TRUE, 'Wine stain on the hem and returned 2 days late.');

INSERT INTO penalty_fees (assessment_id, late_fee, damage_fee, total_penalty) VALUES
(2, 50.00, 150.00, 200.00);

INSERT INTO invoices (rental_id, amount, type, stripe_id, status) VALUES
(1, 80.00, 'RENTAL', 'pi_1AbCdEfGhIjKlMnOp111111', 'PAID'),
(2, 120.00, 'RENTAL', 'pi_2BcDeFgHiJkLmNoPq222222', 'PAID'),
(3, 90.00, 'RENTAL', 'pi_3CdEfGhIjKlMnOpQr333333', 'PAID'),
(3, 200.00, 'PENALTY', 'pi_4DeFgHiJkLmNoPqRs444444', 'PENDING');