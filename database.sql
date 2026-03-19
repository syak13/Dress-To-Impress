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