-- Create the database
drop database luxurystays;
CREATE DATABASE IF NOT EXISTS luxurystays;
USE luxurystays;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE
);

-- User addresses table
CREATE TABLE IF NOT EXISTS user_addresses (
    address_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    address_line1 VARCHAR(100) NOT NULL,
    address_line2 VARCHAR(100),
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50),
    country VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Hotels table
CREATE TABLE IF NOT EXISTS hotels (
    hotel_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50),
    country VARCHAR(50) NOT NULL,
    postal_code VARCHAR(20),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    star_rating DECIMAL(2, 1),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    check_in_time TIME,
    check_out_time TIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Hotel images table
CREATE TABLE IF NOT EXISTS hotel_images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    image_url VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    caption VARCHAR(100),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id) ON DELETE CASCADE
);

-- Room types table
CREATE TABLE IF NOT EXISTS room_types (
    room_type_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL,
    max_occupancy INT NOT NULL,
    size_sqft INT,
    has_breakfast BOOLEAN DEFAULT FALSE,
    is_refundable BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id) ON DELETE CASCADE
);

-- Room type amenities
CREATE TABLE IF NOT EXISTS room_amenities (
    amenity_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    icon_class VARCHAR(50),
    description VARCHAR(255)
);

-- Room type to amenities mapping
CREATE TABLE IF NOT EXISTS room_type_amenities (
    room_type_id INT NOT NULL,
    amenity_id INT NOT NULL,
    PRIMARY KEY (room_type_id, amenity_id),
    FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id) ON DELETE CASCADE,
    FOREIGN KEY (amenity_id) REFERENCES room_amenities(amenity_id) ON DELETE CASCADE
);

-- Hotel facilities
CREATE TABLE IF NOT EXISTS hotel_facilities (
    facility_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    icon_class VARCHAR(50),
    description VARCHAR(255)
);

-- Hotel to facilities mapping
CREATE TABLE IF NOT EXISTS hotel_facility_mapping (
    hotel_id INT NOT NULL,
    facility_id INT NOT NULL,
    PRIMARY KEY (hotel_id, facility_id),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES hotel_facilities(facility_id) ON DELETE CASCADE
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    hotel_id INT NOT NULL,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('pending', 'confirmed', 'cancelled', 'completed') DEFAULT 'confirmed',
    special_requests TEXT,
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

-- Booking rooms details
CREATE TABLE IF NOT EXISTS booking_rooms (
    booking_room_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    room_type_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    adults INT NOT NULL DEFAULT 1,
    children INT DEFAULT 0,
    price_per_night DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id)
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    hotel_id INT NOT NULL,
    booking_id INT,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(100),
    comment TEXT,
    review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_approved BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);

-- Promotions table
CREATE TABLE IF NOT EXISTS promotions (
    promotion_id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT,
    discount_type ENUM('percentage', 'fixed') NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    min_booking_amount DECIMAL(10, 2) DEFAULT 0,
    max_discount DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE
);

-- Newsletter subscriptions
CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    subscription_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert sample data
INSERT INTO users (first_name, last_name, email, password_hash, phone) VALUES
('John', 'Doe', 'john.doe@example.com', '$2y$10$HIXd9X5x1z6vJ5J5X5X5Xe5X5X5X5X5X5X5X5X5X5X5X5X5X5X5X5X', '+1234567890'),
('Jane', 'Smith', 'jane.smith@example.com', '$2y$10$HIXd9X5x1z6vJ5J5X5X5Xe5X5X5X5X5X5X5X5X5X5X5X5X5X5X5X5X', '+1987654321');

INSERT INTO hotels (name, description, address, city, country, star_rating, contact_phone, contact_email) VALUES
('Grand Plaza Hotel', 'Luxury hotel in the heart of New York with stunning city views.', '123 Broadway', 'New York', 'USA', 4.5, '+12125551234', 'info@grandplaza.com'),
('Royal Resort & Spa', 'Exclusive beachfront resort with world-class spa facilities.', '456 Beach Road', 'Bali', 'Indonesia', 5.0, '+623612345678', 'reservations@royalresort.com'),
('Metropolitan Suites', 'Modern suites with premium amenities in central London.', '789 Oxford Street', 'London', 'UK', 4.0, '+442071234567', 'bookings@metropolitansuites.com'),
('Seaside Villas', 'Private villas with breathtaking views of the Aegean Sea.', '101 Cliffside Avenue', 'Santorini', 'Greece', 4.5, '+302286012345', 'stay@seasidevillas.com');

-- Fix the typo in bookings table
ALTER TABLE bookings DROP FOREIGN KEY bookings_ibfk_2;
ALTER TABLE bookings CHANGE hotel_id hotel_id INT NOT NULL;
ALTER TABLE bookings ADD FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id);

-- Create the missing rooms table
CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_type_id INT NOT NULL,
    hotel_id INT NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    floor_number INT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (room_type_id) REFERENCES room_types(room_type_id),
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

-- Insert room types
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy) VALUES
(1, 'Deluxe Room', 'Spacious room with city view', 20000.00, 2),
(1, 'Executive Suite', 'Luxury suite with separate living area', 35000.00, 4),
(2, 'Beach Villa', 'Private villa with ocean view', 450.00, 4),
(3, 'Standard Room', 'Comfortable room with modern amenities', 15000.00, 2);

-- Insert actual rooms
INSERT INTO rooms (room_type_id, hotel_id, room_number) VALUES
(1, 1, '101'), (1, 1, '102'), (1, 1, '103'),
(2, 1, '201'), (2, 1, '202'),
(3, 2, '301'), (3, 2, '302'), (3, 2, '303'),
(4, 3, '401'), (4, 3, '402'), (4, 3, '403');

-- Insert hotel images
INSERT INTO hotel_images (hotel_id, image_url, is_primary) VALUES
(1, 'https://example.com/hotel1.jpg', TRUE),
(2, 'https://example.com/hotel2.jpg', TRUE),
(3, 'https://example.com/hotel3.jpg', TRUE);
-- Remove latitude and longitude columns
ALTER TABLE hotels DROP COLUMN latitude;
ALTER TABLE hotels DROP COLUMN longitude;
-- Add Parisian luxury hotel
INSERT INTO hotels (name, description, address, city, country, star_rating, contact_phone, contact_email) VALUES
('Château Élégance', 'Historic palace turned luxury hotel with Eiffel Tower views', '8 Avenue Montaigne', 'Paris', 'France', 5.0, '+33140732000', 'reservations@chateau-elegance.com');

-- Add Tokyo high-rise hotel
INSERT INTO hotels (name, description, address, city, country, star_rating, contact_phone, contact_email) VALUES
('Tokyo Sky Sanctuary', 'Ultra-modern luxury hotel with panoramic city views', '1-2-3 Shibuya', 'Tokyo', 'Japan', 4.8, '+81354678900', 'info@tokyosky.com');

-- Add Dubai desert resort
INSERT INTO hotels (name, description, address, city, country, star_rating, contact_phone, contact_email) VALUES
('Oasis Mirage Resort', 'Luxury desert resort with private pools and spa', 'Al Barari Road', 'Dubai', 'UAE', 5.0, '+97144200000', 'bookings@oasismirage.ae');

-- Add Sydney harbor hotel
INSERT INTO hotels (name, description, address, city, country, star_rating, contact_phone, contact_email) VALUES
('Harbour Grand Sydney', 'Iconic luxury hotel with Opera House views', '7 Hickson Road', 'Sydney', 'Australia', 4.7, '+61292595000', 'reservations@harbourgrandsydney.com');
-- Add more room types to Grand Plaza Hotel (NY)
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy, size_sqft, has_breakfast) VALUES
(1, 'Presidential Suite', 'Ultra-luxurious suite with butler service', 80000.00, 4, 1800, TRUE),
(1, 'Honeymoon Suite', 'Romantic suite with champagne on arrival', 45000.00, 2, 1200, TRUE);

-- Add room types to Château Élégance (Paris)
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy, size_sqft, has_breakfast) VALUES
(5, 'Eiffel View Room', 'Elegant room with direct Eiffel Tower views', 35000.00, 2, 450, TRUE),
(5, 'Royal Suite', 'Opulent suite with Louis XIV furnishings', 120000.00, 4, 2200, TRUE),
(5, 'Garden Terrace Room', 'Charming room opening to private gardens', 28000.00, 2, 400, TRUE);

-- Add room types to Tokyo Sky Sanctuary
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy, size_sqft, has_breakfast) VALUES
(6, 'Sky View Room', 'High-floor room with panoramic Tokyo views', 40000.00, 2, 500, TRUE),
(6, 'Zen Suite', 'Minimalist luxury with private tatami area', 75000.00, 3, 900, TRUE),
(6, 'Executive Lounge Room', 'Premium room with lounge access', 55000.00, 2, 600, TRUE);
-- Images for Château Élégance (Paris)
INSERT INTO hotel_images (hotel_id, image_url, is_primary, caption) VALUES
(5, 'https://example.com/images/chateau/exterior.jpg', TRUE, 'Grand facade of Château Élégance'),
(5, 'https://example.com/images/chateau/lobby.jpg', FALSE, 'Luxurious lobby'),
(5, 'https://example.com/images/chateau/eiffel-view.jpg', FALSE, 'Eiffel Tower view from room'),
(5, 'https://example.com/images/chateau/restaurant.jpg', FALSE, 'Michelin-star restaurant');

-- Images for Tokyo Sky Sanctuary
INSERT INTO hotel_images (hotel_id, image_url, is_primary, caption) VALUES
(6, 'https://example.com/images/tokyo/exterior-night.jpg', TRUE, 'Tokyo Sky Sanctuary at night'),
(6, 'https://example.com/images/tokyo/pool.jpg', FALSE, 'Infinity pool with city views'),
(6, 'https://example.com/images/tokyo/room.jpg', FALSE, 'Modern guest room'),
(6, 'https://example.com/images/tokyo/spa.jpg', FALSE, 'Spa relaxation area');
-- Rooms for Château Élégance
INSERT INTO rooms (room_type_id, hotel_id, room_number, floor_number) VALUES
(5, 5, '301', 3), (5, 5, '302', 3), (5, 5, '303', 3), -- Eiffel View Rooms
(6, 5, '501', 5), (6, 5, '502', 5), -- Royal Suites
(7, 5, '201', 2), (7, 5, '202', 2), (7, 5, '203', 2); -- Garden Terrace Rooms

-- Rooms for Tokyo Sky Sanctuary
INSERT INTO rooms (room_type_id, hotel_id, room_number, floor_number) VALUES
(8, 6, '4501', 45), (8, 6, '4502', 45), (8, 6, '4503', 45), -- Sky View Rooms
(9, 6, '4801', 48), (9, 6, '4802', 48); -- Zen Suites
-- Add single rooms to Grand Plaza Hotel (NY)
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy, size_sqft, has_breakfast) VALUES
(1, 'Luxury Single', 'Elegant single occupancy room with premium amenities', 15000.00, 1, 300, TRUE);

-- Add single rooms to Royal Resort & Spa (Bali)
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy, size_sqft, has_breakfast) VALUES
(2, 'Tropical Single', 'Cozy single room with garden view', 250.00, 1, 250, TRUE);

-- Add single rooms to Château Élégance (Paris)
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy, size_sqft, has_breakfast) VALUES
(5, 'Petite Chambre', 'Charming single room with Parisian elegance', 22000.00, 1, 280, TRUE);

-- Add single rooms to Tokyo Sky Sanctuary
INSERT INTO room_types (hotel_id, name, description, base_price, max_occupancy, size_sqft, has_breakfast) VALUES
(6, 'Zen Single', 'Compact luxury room with minimalist design', 30000.00, 1, 220, TRUE);
-- Single rooms for Grand Plaza Hotel
INSERT INTO rooms (room_type_id, hotel_id, room_number, floor_number) VALUES
(14, 1, 'S101', 1), (14, 1, 'S102', 1), (14, 1, 'S103', 1);

-- Single rooms for Royal Resort & Spa
INSERT INTO rooms (room_type_id, hotel_id, room_number) VALUES
(15, 2, 'TS01'), (15, 2, 'TS02'), (15, 2, 'TS03');

-- Single rooms for Château Élégance
INSERT INTO rooms (room_type_id, hotel_id, room_number, floor_number) VALUES
(16, 5, 'PC01', 1), (16, 5, 'PC02', 1), (16, 5, 'PC03', 1);

-- Single rooms for Tokyo Sky Sanctuary

