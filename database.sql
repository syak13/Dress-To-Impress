-- 1. Create the customers table first (No dependencies)
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- 2. Create the inventory table (Moved up: Bookings and Rentals depend on this)
CREATE TABLE inventory (
    dress_id INT PRIMARY KEY,
    size VARCHAR(10) NOT NULL,
    all_available_dates JSON,
    is_available BOOLEAN DEFAULT TRUE
);

-- 3. Create the bookings table (Depends on customers, inventory)
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    dress_id INT NOT NULL,
    calendar_event_id VARCHAR(255),
    slot_datetime DATETIME NOT NULL,
    status ENUM('CONFIRMED', 'CANCELLED') DEFAULT 'CONFIRMED',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (dress_id) REFERENCES inventory(dress_id) -- ADDED FK
);

-- 4. Create the notifications table (Depends on customers)
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status ENUM('PENDING', 'SENT', 'FAILED') DEFAULT 'PENDING',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 5. Create the rentals table (Depends on customers, inventory)
CREATE TABLE rentals (
    rental_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    dress_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('ACTIVE', 'COMPLETED', 'CANCELLED') DEFAULT 'ACTIVE',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (dress_id) REFERENCES inventory(dress_id) -- ADDED FK
);

-- 6. Create the return_assessments table (Depends on rentals)
CREATE TABLE return_assessments (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    rental_id INT NOT NULL,
    -- dress_id INT NOT NULL, <-- REMOVED to satisfy 3rd Normal Form
    assessment_date DATETIME NOT NULL,
    is_late BOOLEAN DEFAULT FALSE,
    is_damaged BOOLEAN DEFAULT FALSE,
    damage_description TEXT,
    assessed_by INT NOT NULL, 
    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
);

-- 7. Create the penalty_fees table (Depends on return_assessments)
CREATE TABLE penalty_fees (
    penalty_id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    late_fee DECIMAL(10, 2) DEFAULT 0.00,
    damage_fee DECIMAL(10, 2) DEFAULT 0.00,
    total_penalty DECIMAL(10, 2) DEFAULT 0.00,
    FOREIGN KEY (assessment_id) REFERENCES return_assessments(assessment_id)
);

-- 8. Create the invoices table (Depends on rentals, penalty_fees)
CREATE TABLE invoices (
  invoice_id   INT AUTO_INCREMENT PRIMARY KEY,
  rental_id    INT NOT NULL,
  penalty_id   INT DEFAULT NULL,                   -- ADDED to trace penalties
  amount       DECIMAL(10, 2) NOT NULL,            
  type         ENUM('RENTAL', 'PENALTY') NOT NULL, 
  stripe_id    VARCHAR(100),
  status       ENUM('PENDING', 'PAID', 'FAILED', 'REFUNDED') DEFAULT 'PENDING',
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
  FOREIGN KEY (rental_id) REFERENCES rentals(rental_id),
  FOREIGN KEY (penalty_id) REFERENCES penalty_fees(penalty_id) -- ADDED FK
);


-- 1. Insert Customers
INSERT INTO customers (name, email) VALUES
('Alice Smith', 'alice@example.com'),
('Bob Jones', 'bob@example.com'),
('Chloe Davis', 'chloe@example.com');

-- 2. Insert Inventories (Moved up so foreign keys don't fail)
INSERT INTO inventory (dress_id, size, all_available_dates, is_available) VALUES
(101, 'S', '["2026-04-16", "2026-04-17", "2026-04-18", "2026-04-19"]', TRUE),
(102, 'M', '["2026-05-21", "2026-05-22", "2026-05-23"]', TRUE),
(103, 'L', '[]', FALSE),
(201, 'S', '["2026-06-01", "2026-06-02"]', TRUE),
(202, 'M', '["2026-03-25", "2026-03-26", "2026-03-30", "2026-03-31"]', TRUE),
(203, 'XXL', '["2026-04-01"]', TRUE);

-- 3. Insert Bookings
INSERT INTO bookings (customer_id, dress_id, calendar_event_id, slot_datetime, status) VALUES
(1, 101, 'evt_xyz123', '2026-04-15 10:00:00', 'CONFIRMED'), 
(2, 102, 'evt_abc456', '2026-05-20 14:30:00', 'CONFIRMED'), 
(3, 103, 'evt_def789', '2026-03-01 09:00:00', 'CANCELLED'); 

-- 4. Insert Notifications
INSERT INTO notifications (customer_id, email, message, status) VALUES
(1, 'alice@example.com', 'Your fitting is confirmed for April 15.', 'SENT'),
(2, 'bob@example.com', 'Reminder: Upcoming appointment next month.', 'PENDING'),
(3, 'chloe@example.com', 'Your booking has been successfully cancelled.', 'SENT');

-- 5. Insert Rentals
INSERT INTO rentals (customer_id, dress_id, start_date, end_date, status) VALUES
(1, 201, '2026-03-10', '2026-03-14', 'COMPLETED'), 
(2, 202, '2026-03-18', '2026-03-22', 'ACTIVE'),    
(3, 203, '2026-02-01', '2026-02-05', 'COMPLETED'); 

-- 6. Insert Return Assessments (Removed the dress_id column values)
INSERT INTO return_assessments (rental_id, assessment_date, is_late, is_damaged, damage_description, assessed_by) VALUES
(1, '2026-03-14 15:00:00', FALSE, FALSE, NULL, 991), 
(3, '2026-02-07 10:00:00', TRUE, TRUE, 'Wine stain on the hem and returned 2 days late.', 992); 

-- 7. Insert Penalty Fees (This generates penalty_id = 1)
INSERT INTO penalty_fees (assessment_id, late_fee, damage_fee, total_penalty) VALUES
(2, 50.00, 150.00, 200.00);

-- 8. Insert Invoices (Updated to include penalty_id mapping)
-- Syntax: (rental_id, penalty_id, amount, type, stripe_id, status)
INSERT INTO invoices (rental_id, penalty_id, amount, type, stripe_id, status) VALUES
(1, NULL, 80.00, 'RENTAL', 'pi_1AbCdEfGhIjKlMnOp111111', 'PAID'),       -- Alice's standard rental
(2, NULL, 120.00, 'RENTAL', 'pi_2BcDeFgHiJkLmNoPq222222', 'PAID'),      -- Bob's standard rental
(3, NULL, 90.00, 'RENTAL', 'pi_3CdEfGhIjKlMnOpQr333333', 'PAID'),       -- Chloe's standard rental
(3, 1, 200.00, 'PENALTY', 'pi_4DeFgHiJkLmNoPqRs444444', 'PENDING');     -- Chloe's penalty mapping directly to penalty_id 1