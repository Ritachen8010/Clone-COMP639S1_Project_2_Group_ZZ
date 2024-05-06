-- Create the database
CREATE DATABASE `bbbb`;
USE `bbbb`;

-- 1. account 
CREATE TABLE `account` (
    `account_id` INT,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `role` ENUM('manager', 'staff', 'customer') NOT NULL,
    PRIMARY KEY (`account_id`)
)AUTO_INCREMENT=1;



-- 2. coustomer
CREATE TABLE `customer` (
    `customer_id` INT,
    `account_id` INT,
    `first_name` VARCHAR(100),
    `last_name` VARCHAR(100),
    `phone_number` VARCHAR(20),
    `date_of_birth` DATE,
    `gender` ENUM('male', 'female', 'other'),
    `id_num` VARCHAR(20),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `profile_image` VARCHAR(500) DEFAULT '123.jpg',
    `status` ENUM ('active', 'inactive') NOT NULL DEFAULT 'active',
    PRIMARY KEY (`customer_id`),
    FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`)
)AUTO_INCREMENT=1000;

-- 3. staff
CREATE TABLE `staff` (
	`staff_id` INT,
    `account_id` INT,
    `first_name` VARCHAR(100),
    `last_name` VARCHAR(100),
    `phone_number` VARCHAR(20),
    `date_of_birth` DATE,
    `gender` ENUM('male', 'female', 'other'),
    `position` VARCHAR(255),
    `profile_image` VARCHAR(500) DEFAULT '123.jpg',
    `status` ENUM ('active', 'inactive') NOT NULL DEFAULT 'active',
	PRIMARY KEY (`staff_id`),
    FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`)
)AUTO_INCREMENT=1;

-- 5. manager
CREATE TABLE `manager` (
	`manager_id` INT,
    `account_id` INT,
    `first_name` VARCHAR(100),
    `last_name` VARCHAR(100),
    `phone_number` VARCHAR(20),
    `date_of_birth` DATE,
    `gender` ENUM('male', 'female', 'other'),
    `position` VARCHAR(255),
    `profile_image` VARCHAR(500) DEFAULT '123.jpg',
    `status` ENUM ('active', 'inactive') NOT NULL DEFAULT 'active',
	PRIMARY KEY (`manager_id`),
    FOREIGN KEY (`account_id`) REFERENCES `account` (`account_id`)
)AUTO_INCREMENT=1;

-- 6 . product_category
CREATE TABLE `product_category` (
    `category_id` INT,
    `type` VARCHAR (225) NOT NULL,
    PRIMARY KEY (`category_id`)
)AUTO_INCREMENT=1;

-- 7. product
CREATE TABLE `product` (
    `product_id` INT AUTO_INCREMENT,
    `category_id` INT,
    `name` VARCHAR(255),
    `description` TEXT,
    `unit_price` DECIMAL(10,2),
    `special_requests` TEXT,
    `is_available` BOOLEAN,
    `image` VARCHAR(500),
    PRIMARY KEY (`product_id`),
    FOREIGN KEY (`category_id`) REFERENCES `product_category` (`category_id`)
)AUTO_INCREMENT=1;

CREATE TABLE `product_option_type` (
	`option_type_id` INT,
    `description` VARCHAR(500),
	PRIMARY KEY (`option_type_id`) -- 描述产品选项的类型，如大小、糖浆类型、牛奶类型。
)AUTO_INCREMENT=1;

CREATE TABLE `product_option` (
	`option_id` INT,
    `option_type_id` INT,
    `name` VARCHAR(500),
	`additional_cost` DECIMAL(10, 2),
    PRIMARY KEY (`option_id`),
    FOREIGN KEY (`option_type_id`) REFERENCES `product_option_type` (`option_type_id`)
)AUTO_INCREMENT=1;

CREATE TABLE `product_option_mapping` (
	`product_id` INT,
    `option_id` INT,
    PRIMARY KEY (`product_id`, `option_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`),
    FOREIGN KEY (`option_id`) REFERENCES `product_option` (`option_id`)
)AUTO_INCREMENT=1;

-- 8. orders
CREATE TABLE `orders` (
    `order_id` INT,
    `customer_id` INT,
    `total_price` DECIMAL(10,2),
    `special_requests` TEXT,
    `scheduled_pickup_time` DATETIME,
    `status` ENUM('ordered', 'ready', 'collected', 'cancelled') NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`order_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
)AUTO_INCREMENT=1;

-- 9. order_item
CREATE TABLE `order_item` (
    `order_item_id` INT,
    `order_id` INT,
    `product_id` INT,
    `quantity` INT,
    PRIMARY KEY (`order_item_id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product`(`product_id`)
)AUTO_INCREMENT=1;

-- 10. inventory
CREATE TABLE `inventory` (
    `inventory_id` INT,
    `staff_id` INT,
    `product_id` INT,
    `quantity` INT,
    `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`inventory_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`),
    FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
)AUTO_INCREMENT=1;

-- 10. accommodation
CREATE TABLE `accommodation` (
    `accommodation_id` INT,
    `type` ENUM('dorm', 'twin', 'queen') NOT NULL,
    `description` TEXT,
    `capacity` INT,
    `price_per_night` DECIMAL(10,2),
    `is_available` BOOLEAN DEFAULT TRUE,
    `image` VARCHAR(500),
    PRIMARY KEY (`accommodation_id`)
)AUTO_INCREMENT=1;

CREATE TABLE `blocked_dates` (
    `block_id` INT,
    `accommodation_id` INT,
    `start_date` DATE,
    `end_date` DATE,
    `is_active` BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (`block_id`),
    FOREIGN KEY (`accommodation_id`) REFERENCES `accommodation` (`accommodation_id`)
)AUTO_INCREMENT=1;

-- 11. booking
CREATE TABLE `booking` (
    `booking_id` INT,
    `customer_id` INT,
    `payment_id` INT,
    `accommodation_id` INT,
    `start_date` DATE, 
    `end_date` DATE,
    `adults` INT,               
    `children` INT,              
    `rooms` INT DEFAULT 1,
    `is_paid` BOOLEAN,
    `status` ENUM('confirmed', 'cancelled', 'checked in', 'checked out') NOT NULL,
    `booking_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`booking_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`),
    FOREIGN KEY (`accommodation_id`) REFERENCES `accommodation` (`accommodation_id`)
)AUTO_INCREMENT=1;


-- 12. message
CREATE TABLE `message` (
    `message_id` INT,
    `customer_id` INT,
    `manager_id` INT,
    `staff_id` INT,
    `content` TEXT,
    `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `time_responded` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`message_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`),
    FOREIGN KEY (`manager_id`) REFERENCES `manager` (`manager_id`),
    FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
)AUTO_INCREMENT=1;

-- 13. loyalty_point
CREATE TABLE `loyalty_point` (
	`loyalty_point_id`INT,
    `order_id` INT,
    `customer_id` INT,
    `points_earned` INT NOT NULL,
    `points_redeemed` INT NOT NULL,
    `points_balance` INT,
    `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`loyalty_point_id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
);

-- 14. payment_type
CREATE TABLE `payment_type` (
    `payment_type_id` INT,
    `payment_type` VARCHAR(50),
    PRIMARY KEY (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 15. bank_card
CREATE TABLE `bank_Card` (
    `bank_card_id` INT,
    `card_num` INT,
    `expire_Date` DATE,
	`payment_type_id` INT,
    PRIMARY KEY (`bank_card_id`),
    FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 16. gift_card
CREATE TABLE `gift_card` (
    `gift_card_id` INT,
    `code` VARCHAR(255),
    `balance` DECIMAL(10,2),
    `expiration_date` DATE,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `purchase_amount` DECIMAL(10,2) NOT NULL, 
    `payment_type_id` INT,
    PRIMARY KEY (`gift_card_id`),
	FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 17. promotion
CREATE TABLE `promotion` (
    `promotion_id` INT,
    `code` VARCHAR(255),
    `description` TEXT,
    `discount_value` DECIMAL(10,2),
    `valid_from` DATE,
    `valid_until` DATE,
    `usage_limit` INT,
    `payment_type_id` INT,
    PRIMARY KEY (`promotion_id`),
    FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 18. payment
CREATE TABLE `payment` (
    `payment_id` INT,
    `customer_id` INT,
    `payment_type_id` INT,
    `order_id` INT,
    `booking_id` INT,
    PRIMARY KEY (`payment_id`),
    FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
    FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
)AUTO_INCREMENT=1;

-- 19. news
CREATE TABLE `news` (
    `news_id` INT,
    `manager_id` INT,
    `description` TEXT,
    `published_date` DATE,
    `image` VARCHAR(500),
    `is_active` BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (`news_id`),
    FOREIGN KEY (`manager_id`) REFERENCES `manager` (`manager_id`)
)AUTO_INCREMENT=1;

-- 20. order_feedback
CREATE TABLE `order_feedback` (
    `order_item_id` INT,
    `customer_id` INT,
    `manager_id` INT,
    `rate` INT,
    `description` TEXT,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATE DEFAULT (CURRENT_DATE), 
    PRIMARY KEY (`order_item_id`, `customer_id`),
    FOREIGN KEY (`order_item_id`) REFERENCES `order_item`(`order_item_id`),
    FOREIGN KEY (`manager_id`) REFERENCES `manager`(`manager_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
);

-- 21. room_feedback
CREATE TABLE `room_feedback` (
    `booking_id` INT,
    `customer_id` INT,
    `manager_id` INT,
    `rate` INT,
    `description` TEXT,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATE DEFAULT (CURRENT_DATE),
    PRIMARY KEY (`booking_id`, `customer_id`),
    FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`),
    FOREIGN KEY (`manager_id`) REFERENCES `manager`(`manager_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
);

INSERT INTO `account` (`account_id`, `email`, `password`, `role`) VALUES 
(1, 'aa@gmail.com', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'manager'),
(2, 'bb@gmail.com', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'staff'),
(3, 'cc@gmail.com', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'customer');

INSERT INTO `manager` (`manager_id`, `account_id`, `first_name`, `last_name`, `phone_number`, `date_of_birth`, `gender`, `position`, `profile_image`, `status`) 
VALUES (1, 1, 'aa', 'AA', '555-123-4567', '1975-08-30', 'Female', 'General Manager', 'default.jpg', 'active');

INSERT INTO `staff` (`staff_id`, `account_id`, `first_name`, `last_name`, `phone_number`, `date_of_birth`, `gender`, `position`, `profile_image`, `status`) 
VALUES (1, 2, 'bb', 'BB', '987-654-3210', '1990-05-15', 'Female', 'Reception', 'bb.jpg', 'active');

INSERT INTO `customer` (`customer_id`, `account_id`, `first_name`, `last_name`, `phone_number`, `date_of_birth`, `gender`, `id_num`, `created_at`, `profile_image`, `status`) 
VALUES (1, 3, 'cc', 'CC', '123-456-7890', '1985-10-25', 'Male', 'AB1234567', CURRENT_TIMESTAMP, 'cc.jpg', 'active');
