-- 1. Create the customers table first (No dependencies)
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE
);

-- 2. Create the bookings table (Depends on customers)
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    dress_id INT NOT NULL,
    calendar_event_id VARCHAR(255),
    slot_datetime DATETIME NOT NULL,
    status ENUM('CONFIRMED', 'CANCELLED') DEFAULT 'CONFIRMED',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 3. Create the notifications table (Depends on customers)
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    email VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status ENUM('PENDING', 'SENT', 'FAILED') DEFAULT 'PENDING',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 4. Create the rentals table (Depends on customers)
CREATE TABLE rentals (
    rental_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    dress_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('ACTIVE', 'COMPLETED', 'CANCELLED') DEFAULT 'ACTIVE',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 5. Create the return_assessments table (Depends on rentals)
CREATE TABLE return_assessments (
    assessment_id INT AUTO_INCREMENT PRIMARY KEY,
    rental_id INT NOT NULL,
    dress_id INT NOT NULL,
    assessment_date DATETIME NOT NULL,
    is_late BOOLEAN DEFAULT FALSE,
    is_damaged BOOLEAN DEFAULT FALSE,
    damage_description TEXT,
    assessed_by INT NOT NULL, -- Assuming employee_id
    FOREIGN KEY (rental_id) REFERENCES rentals(rental_id)
);

-- 6. Create the penalty_fees table (Depends on return_assessments)
CREATE TABLE penalty_fees (
    penalty_id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL,
    late_fee DECIMAL(10, 2) DEFAULT 0.00,
    damage_fee DECIMAL(10, 2) DEFAULT 0.00,
    total_penalty DECIMAL(10, 2) DEFAULT 0.00,
    FOREIGN KEY (assessment_id) REFERENCES return_assessments(assessment_id)
);

-- 7. Create the invoices table
CREATE TABLE invoices (
  invoice_id   INT AUTO_INCREMENT PRIMARY KEY,
  rental_id    INT NOT NULL,
  amount       DECIMAL(10, 2) NOT NULL,            -- Changed to DECIMAL for currency precision
  type         ENUM('RENTAL', 'PENALTY') NOT NULL, -- Changed to ENUM to enforce valid types
  stripe_id    VARCHAR(100),
  status       ENUM('PENDING', 'PAID', 'FAILED', 'REFUNDED') DEFAULT 'PENDING',
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, -- Tracks payment time
  FOREIGN KEY (rental_id) REFERENCES rentals(rental_id) -- Enforces relational integrity
);

-- 8. Create the inventory table
CREATE TABLE inventory (
    dress_id INT PRIMARY KEY,               -- PK ensures each dress has only ONE record/size
    size VARCHAR(10) NOT NULL,              -- e.g., 'XS', 'S', 'M', 'L', 'XL'
    all_available_dates JSON,               -- Stores the list of dates as a JSON array
    is_available BOOLEAN DEFAULT TRUE       -- Quick toggle for overall availability
);



-- Logic Behind the Data:
-- The Happy Path (Alice): Alice booked an appointment, received her notification, rented dress 201, 
-- and returned it right on time on March 14th with no damages. Her assessment generated no penalty row.

-- The Active Path (Bob): Bob is currently in the middle of a rental spanning March 18th to March 22nd. 
-- He has no return assessment yet because his status is ACTIVE.

-- The Penalty Path (Chloe): Chloe rented dress 203 in February. 
-- She was supposed to return it by Feb 5th but brought it back on Feb 7th (triggering is_late). The employee also noted a wine stain (triggering is_damaged). Consequently, Assessment #2 directly triggered a $200 row in the penalty_fees table.


-- 1. Insert Customers
-- Creating three distinct users to attach our scenarios to.
INSERT INTO customers (name, email) VALUES
('Alice Smith', 'alice@example.com'),
('Bob Jones', 'bob@example.com'),
('Chloe Davis', 'chloe@example.com');
-- (Assume IDs generated are 1, 2, and 3)

-- 2. Insert Bookings
-- Mixing future confirmed fittings and a cancelled past appointment.
INSERT INTO bookings (customer_id, dress_id, calendar_event_id, slot_datetime, status) VALUES
(1, 101, 'evt_xyz123', '2026-04-15 10:00:00', 'CONFIRMED'), 
(2, 102, 'evt_abc456', '2026-05-20 14:30:00', 'CONFIRMED'), 
(3, 103, 'evt_def789', '2026-03-01 09:00:00', 'CANCELLED'); 

-- 3. Insert Notifications
-- Tying email alerts to the booking events above.
INSERT INTO notifications (customer_id, email, message, status) VALUES
(1, 'alice@example.com', 'Your fitting is confirmed for April 15.', 'SENT'),
(2, 'bob@example.com', 'Reminder: Upcoming appointment next month.', 'PENDING'),
(3, 'chloe@example.com', 'Your booking has been successfully cancelled.', 'SENT');

-- 4. Insert Rentals
-- Scenario 1 (Alice): Completed smoothly in the past.
-- Scenario 2 (Bob): Currently active rental.
-- Scenario 3 (Chloe): Completed in the past, but we'll use this one for a penalty scenario.
INSERT INTO rentals (customer_id, dress_id, start_date, end_date, status) VALUES
(1, 201, '2026-03-10', '2026-03-14', 'COMPLETED'), 
(2, 202, '2026-03-18', '2026-03-22', 'ACTIVE'),    
(3, 203, '2026-02-01', '2026-02-05', 'COMPLETED'); 
-- (Assume IDs generated are 1, 2, and 3)

-- 5. Insert Return Assessments
-- We only assess completed rentals (IDs 1 and 3). 
-- Employee 991 handles a perfect return. Employee 992 handles a problematic one.
INSERT INTO return_assessments (rental_id, dress_id, assessment_date, is_late, is_damaged, damage_description, assessed_by) VALUES
(1, 201, '2026-03-14 15:00:00', FALSE, FALSE, NULL, 991), 
(3, 203, '2026-02-07 10:00:00', TRUE, TRUE, 'Wine stain on the hem and returned 2 days late.', 992); 
-- (Assume IDs generated are 1 and 2)

-- 6. Insert Penalty Fees
-- Linking a fee ONLY to Assessment ID 2 (Chloe's problematic return).
INSERT INTO penalty_fees (assessment_id, late_fee, damage_fee, total_penalty) VALUES
(2, 50.00, 150.00, 200.00);


-- 7. Insert Invoices
-- Creating standard rental invoices for all three users, plus one penalty invoice for Chloe.
INSERT INTO invoices (rental_id, amount, type, stripe_id, status) VALUES

-- Scenario 1 (Alice): Paid for her dress rental smoothly.
(1, 80.00, 'RENTAL', 'pi_1AbCdEfGhIjKlMnOp111111', 'PAID'),

-- Scenario 2 (Bob): Paid for his currently active rental.
(2, 120.00, 'RENTAL', 'pi_2BcDeFgHiJkLmNoPq222222', 'PAID'),

-- Scenario 3a (Chloe): Paid for her original base rental back in February.
(3, 90.00, 'RENTAL', 'pi_3CdEfGhIjKlMnOpQr333333', 'PAID'),

-- Scenario 3b (Chloe): The $200 penalty invoice triggered by Assessment ID 2.
-- This represents an outstanding charge sent to the customer that hasn't been paid yet.
(3, 200.00, 'PENALTY', 'pi_4DeFgHiJkLmNoPqRs444444', 'PENDING');


-- 8. Insert Inventories
INSERT INTO inventory (dress_id, size, all_available_dates, is_available) VALUES
-- Scenario 1: A dress with multiple upcoming available dates
(101, 'S', '["2026-04-16", "2026-04-17", "2026-04-18", "2026-04-19"]', TRUE),

-- Scenario 2: Another available dress
(102, 'M', '["2026-05-21", "2026-05-22", "2026-05-23"]', TRUE),

-- Scenario 3: A dress that is completely booked or out of commission (empty list)
(103, 'L', '[]', FALSE),

-- Scenario 4: A dress available for just a couple of days
(201, 'S', '["2026-06-01", "2026-06-02"]', TRUE),

-- Scenario 5: A dress with a gap in availability (maybe it's booked in the middle)
(202, 'M', '["2026-03-25", "2026-03-26", "2026-03-30", "2026-03-31"]', TRUE),

-- Scenario 6: A plus-size option with limited availability
(203, 'XXL', '["2026-04-01"]', TRUE);