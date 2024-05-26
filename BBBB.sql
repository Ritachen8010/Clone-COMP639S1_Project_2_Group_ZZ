-- Create the database
CREATE DATABASE `bbbb`;
USE `bbbb`;

-- 1. account 
CREATE TABLE `account` (
    `account_id` INT AUTO_INCREMENT,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password` VARCHAR(255) NOT NULL,
    `role` ENUM('manager', 'staff', 'customer') NOT NULL,
    PRIMARY KEY (`account_id`)
)AUTO_INCREMENT=1;

-- 2. coustomer
CREATE TABLE `customer` (
    `customer_id` INT AUTO_INCREMENT,
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
	`staff_id` INT AUTO_INCREMENT,
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

-- 4. manager
CREATE TABLE `manager` (
	`manager_id` INT AUTO_INCREMENT,
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

-- 5 . product_category
CREATE TABLE `product_category` (
    `category_id` INT AUTO_INCREMENT,
    `name` VARCHAR(225) NOT NULL,
    `description` VARCHAR(500),
    PRIMARY KEY (`category_id`)
)AUTO_INCREMENT=1;

-- 6. product
CREATE TABLE `product` (
    `product_id` INT AUTO_INCREMENT,
    `category_id` INT,
    `name` VARCHAR(255),
    `description` TEXT,
    `unit_price` DECIMAL(10,2),
    `is_available` BOOLEAN,
    `image` VARCHAR(500),
    PRIMARY KEY (`product_id`),
    FOREIGN KEY (`category_id`) REFERENCES `product_category` (`category_id`)
)AUTO_INCREMENT=1;

-- 7. product option type
CREATE TABLE `product_option` (
    `option_id` INT AUTO_INCREMENT,
    `product_id` INT,
    `option_type` VARCHAR(255),
    `option_name` VARCHAR(255),
    `additional_cost` DECIMAL(10,2),
    PRIMARY KEY (`option_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`)
) AUTO_INCREMENT=1;


CREATE TABLE `inventory` (
    `staff_id` INT,
    `manager_id` INT,
    `product_id` INT,
    `option_id` INT DEFAULT NULL,
    `quantity` INT,
    `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`),
    FOREIGN KEY (`option_id`) REFERENCES `product_option` (`option_id`)
);

-- 10. orders
CREATE TABLE `orders` (
    `order_id` INT AUTO_INCREMENT,
    `customer_id` INT,
    `total_price` DECIMAL(10,2),
    `special_requests` TEXT,
    `scheduled_pickup_time` DATETIME,
    `status` ENUM('ordered', 'ready', 'collected', 'cancelled') NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`order_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
)AUTO_INCREMENT=1;

-- 11. order_item
CREATE TABLE `order_item` (
    `order_item_id` INT AUTO_INCREMENT,
    `order_id` INT,
    `product_id` INT,
    `quantity` INT,
    `options` VARCHAR(255),
    PRIMARY KEY (`order_item_id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product`(`product_id`)
)AUTO_INCREMENT=1;

-- 13. accommodation
CREATE TABLE `accommodation` (
    `accommodation_id` INT AUTO_INCREMENT,
    `type` ENUM('Dorm', 'Twin', 'Queen') NOT NULL,
    `description` TEXT,
    `capacity` INT,
    `space` INT,
    `price_per_night` DECIMAL(10,2),
    `is_available` BOOLEAN DEFAULT TRUE,
    `image` VARCHAR(500),
    `room_status` ENUM('Open', 'Closed') DEFAULT 'Open',	
    PRIMARY KEY (`accommodation_id`)
)AUTO_INCREMENT=1;

-- 14. blocked dates
CREATE TABLE `blocked_dates` (
    `block_id` INT AUTO_INCREMENT,
    `accommodation_id` INT,
    `start_date` DATE,
    `end_date` DATE,
    `is_active` BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (`block_id`),
    FOREIGN KEY (`accommodation_id`) REFERENCES `accommodation` (`accommodation_id`)
)AUTO_INCREMENT=1;

-- 15. booking
CREATE TABLE `booking` (
    `booking_id` INT AUTO_INCREMENT,
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


-- 16. message
CREATE TABLE `message` (
    `message_id` INT AUTO_INCREMENT,
    `customer_id` INT,
    `manager_id` INT,
    `staff_id` INT,
    `content` TEXT,
    `sent_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `time_responded` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `is_read` BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (`message_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`),
    FOREIGN KEY (`manager_id`) REFERENCES `manager` (`manager_id`),
    FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`)
)AUTO_INCREMENT=1;

-- 17. loyalty_point
CREATE TABLE `loyalty_point` (
	`loyalty_point_id`INT AUTO_INCREMENT,
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

-- 18. payment_type
CREATE TABLE `payment_type` (
    `payment_type_id` INT AUTO_INCREMENT,
    `payment_type` VARCHAR(50),
    PRIMARY KEY (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 19. bank_card
CREATE TABLE `bank_card` (
    `bank_card_id` INT AUTO_INCREMENT,
    `card_num` VARCHAR(20),
    `expire_Date` DATE,
	`payment_type_id` INT,
    PRIMARY KEY (`bank_card_id`),
    FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 20. gift_card
CREATE TABLE `gift_card` (
    `gift_card_id` INT AUTO_INCREMENT,
    `code` VARCHAR(255),
    `balance` DECIMAL(10,2),
    `expiration_date` DATE,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `purchase_amount` DECIMAL(10,2) NOT NULL, 
    `payment_type_id` INT,
    PRIMARY KEY (`gift_card_id`),
	FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 21. promotion
CREATE TABLE `promotion` (
    `promotion_id` INT AUTO_INCREMENT,
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

-- 22. payment
CREATE TABLE `payment` (
    `payment_id` INT AUTO_INCREMENT,
    `customer_id` INT,
    `payment_type_id` INT,
    `order_id` INT,
    `booking_id` INT,
    `paid_amount` DECIMAL(10,2),
    PRIMARY KEY (`payment_id`),
    FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
    FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`)
)AUTO_INCREMENT=1;

-- 23. news
CREATE TABLE `news` (
    `news_id` INT AUTO_INCREMENT,
    `manager_id` INT,
    `description` TEXT,
    `published_date` DATE,
    `image` VARCHAR(500),
    `is_active` BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (`news_id`),
    FOREIGN KEY (`manager_id`) REFERENCES `manager` (`manager_id`)
)AUTO_INCREMENT=1;

-- 24. order_feedback
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

-- 25. room_feedback
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


-- 26. cart_item
CREATE TABLE `cart_item` (
    `cart_item_id` INT AUTO_INCREMENT,
    `customer_id` INT,
    `product_id` INT,
    `quantity` INT,
    PRIMARY KEY (`cart_item_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`)
) AUTO_INCREMENT=1;


-- 27. cart_item_option
CREATE TABLE `cart_item_option` (
    `cart_item_id` INT,
    `option_id` INT,
    PRIMARY KEY (`cart_item_id`, `option_id`),
    FOREIGN KEY (`cart_item_id`) REFERENCES `cart_item` (`cart_item_id`),
    FOREIGN KEY (`option_id`) REFERENCES `product_option` (`option_id`)
)AUTO_INCREMENT=1;

-- 28. paid_item
CREATE TABLE `paid_item` (
    `paid_item_id` INT AUTO_INCREMENT,
    `customer_id` INT,
    `product_id` INT,
    `quantity` INT,
    `price` DECIMAL(10,2),
    `order_id` INT,
    PRIMARY KEY (`paid_item_id`),
    FOREIGN KEY (`customer_id`) REFERENCES `customer` (`customer_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`)
) AUTO_INCREMENT=1;


-- 1. Insert into account
INSERT INTO `account` (`account_id`, `email`, `password`, `role`) VALUES 
(1, 'aa@gmail.com', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'manager'),
(2, 'bb@gmail.com', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'staff'),
(3, 'cc@gmail.com', '0b92ecb984a4976d442762ef7831aacaa205f1ebacc2a617fe8225fff71d7fb6', 'customer');

-- 2. Insert into customer
INSERT INTO `customer` (`customer_id`, `account_id`, `first_name`, `last_name`, `phone_number`, `date_of_birth`, `gender`, `id_num`, `created_at`, `profile_image`, `status`) 
VALUES (1000, 3, 'cc', 'CC', '1234567890', '1985-10-25', 'Male', 'AB1234567', CURRENT_TIMESTAMP, 'cc.jpg', 'active');

-- 3. Insert into staff
INSERT INTO `manager` (`manager_id`, `account_id`, `first_name`, `last_name`, `phone_number`, `date_of_birth`, `gender`, `position`, `profile_image`, `status`) 
VALUES (1, 1, 'aa', 'AA', '5551234567', '1975-08-30', 'Female', 'General Manager', 'default.jpg', 'active');

-- 4. Insert into manager
INSERT INTO `staff` (`staff_id`, `account_id`, `first_name`, `last_name`, `phone_number`, `date_of_birth`, `gender`, `position`, `profile_image`, `status`) 
VALUES (1, 2, 'bb', 'BB', '9876543210', '1990-05-15', 'Female', 'Reception', 'bb.jpg', 'active');

-- 5. Insert into product_category
INSERT INTO `product_category` (`name`, `description`)
VALUES
('Coffee', 'A variety of coffee drinks including espresso, latte, cappuccino, and more'),
('Hot Drinks', 'A variety of warm beverages including hot chocolate, tea, and more'),
('Soft Drinks', 'A variety of refreshing carbonated beverages.'),
('Milkshakes', 'Creamy and thick milkshakes with a variety of flavors.'),
('Iced Teas', 'Refreshing and chilled teas available in several flavors.'),
('Fast Food', 'A variety of quick and delicious meals including hotdogs, crepes, and more'),
('Frozen Treats', 'Delicious and refreshing frozen desserts, perfect for cooling down on a hot day'),
('Travel Essentials & Souvenirs', 'A curated collection of essential items and unique souvenirs, perfect for travelers seeking convenience and memorable keepsakes.');
-- 6. Insert into product
INSERT INTO `product` (`category_id`, `name`, `description`, `unit_price`, `is_available`, `image`)
VALUES 
-- Coffee
(1, 'Espresso', 'Strong black coffee made by forcing steam through ground coffee beans.', 4.50, TRUE, 'espresso.jpg'), -- 1
(1, 'Latte', 'Coffee drink made with espresso and steamed milk.', 6.00, TRUE, 'latte.jpg'), -- 2
(1, 'Cappuccino', 'Coffee-based drink made with equal parts of espresso, steamed milk, and frothed milk.', 6.00, TRUE, 'cappuccino.jpg'), -- 3
(1, 'Flat White', 'Smooth and velvety coffee made with espresso and steamed milk.', 6.00, TRUE, 'flatwhite.jpg'), -- 4
(1, 'Mocha', 'Espresso with steamed milk and chocolate syrup, topped with whipped cream.', 6.50, TRUE, 'mocha.jpg'), -- 5

-- Hot Drinks
(2, 'Hot Chocolate', 'Rich and creamy hot chocolate made with real cocoa.', 5.00, TRUE, 'hotchocolate.jpg'), -- 6
(2, 'Herbal Tea', 'A soothing blend of herbal ingredients steeped to perfection.', 6.50, TRUE, 'herbaltea.jpg'), -- 7
(2, 'Chai Latte', 'Spiced tea beverage made with aromatic spices and steamed milk.', 5.00, TRUE, 'chai.jpg'), -- 8

-- Soft Drinks
(3, 'Coca-Cola', 'Classic cola-flavored soft drink.', 3.00, TRUE, 'cola.jpg'), -- 9
(3, 'Sprite', 'Crisp, refreshing lemon-lime flavored soda.', 3.00, TRUE, 'sprite.jpg'), -- 10
(3, 'Fanta', 'Bright, bubbly and instantly refreshing orange soda.', 3.00, TRUE, 'fanta.jpg'), -- 11
(3, 'Pepsi', 'Bold, refreshing cola drink with a rich flavor.', 3.00, TRUE, 'pepsi.jpg'), -- 12
(3, 'Ginger Ale', 'Gently carbonated, soothing ginger-flavored soda.', 5.00, TRUE, 'ginger.jpg'), -- 13

-- Milkshakes
(4, 'Classic Vanilla', 'Smooth and creamy vanilla milkshake.', 7.00, TRUE, 'vanilla.jpg'), -- 14
(4, 'Rich Chocolate', 'Decadent chocolate milkshake made from real cocoa.', 7.00, TRUE, 'chocolate.jpg'), -- 15
(4, 'Strawberry Delight', 'Fresh and fruity strawberry milkshake.', 7.00, TRUE, 'strawberry.jpg'), -- 16
(4, 'Caramel Swirl', 'Creamy milkshake with rich caramel swirls.', 7.00, TRUE, 'caramel.jpg'), -- 17
(4, 'Banana Bliss', 'Creamy milkshake blended with ripe bananas.', 7.00, TRUE, 'banana.jpg'), -- 18
(4, 'Cookies and Cream', 'Crushed cookies mixed into a creamy milkshake.', 7.00, TRUE, 'cookie.jpg'), -- 19
(4, 'Seasonal Berry', 'Blend of seasonal berries in a refreshing milkshake.', 7.00, TRUE, 'berry.jpg'), -- 20

-- Iced Teas
(5, 'Classic Lemon Iced Tea', 'Iced tea flavored with a twist of lemon.', 4.50, TRUE, 'lemontea.jpg'), -- 21
(5, 'Peach Iced Tea', 'Refreshing iced tea infused with peach flavors.', 4.50, TRUE, 'peachtea.jpg'), -- 22
(5, 'Raspberry Iced Tea', 'Iced tea infused with the essence of raspberries.', 4.50, TRUE, 'rasberrytea.jpg'), -- 23
(5, 'Green Iced Tea', 'Smooth and mellow green tea served chilled.', 4.50, TRUE, 'greentea.jpg'), -- 24
(5, 'Hibiscus Iced Tea', 'Tangy and refreshing hibiscus-flavored iced tea.', 4.50, TRUE, 'hibiscuctea.jpg'), -- 25
(5, 'Mint Iced Tea', 'Cooling mint-flavored iced tea.', 4.50, TRUE, 'minttea.jpg'), -- 26

-- Fast Food
(6, 'American Hotdogs', 'Classic grilled hotdogs with a selection of toppings.', 8.00, TRUE, 'hotdog.jpg'), -- 27
(6, 'Sweetcorn & Kumara Patties', 'Delicious patties made from sweetcorn and kumara.', 8.50, TRUE, 'pattie.jpg'), -- 28
(6, 'Crepes', 'Thin pancakes served with various toppings.', 8.00, TRUE, 'crepes.jpg'), -- 29
(6, 'Smokey BBQ Pulled Pork in a Bun', 'Slow-cooked pulled pork smothered in Smokey BBQ sauce, served in a soft bun.', 10.00, TRUE, 'bun.jpg'), -- 30
(6, 'Muffins', 'Freshly baked muffins available in several flavors.', 4.50, TRUE, 'muffins.jpg'), -- 31
(6, 'Slices', 'Assorted homemade slices.', 3.00, TRUE, 'slice.jpg'), -- 32
(6, 'Chicken Tenders', 'Crispy on the outside, juicy on the inside, our chicken tenders are served with your choice of dipping sauces.', 7.50, TRUE, 'chicken_tenders.jpg'), -- 33
(6, 'Veggie Burger', 'A hearty, meat-free patty served on a toasted bun with lettuce, tomato, and your choice of sauce.', 9.00, TRUE, 'veggie_burger.jpg'), -- 34
(6, 'Fish Tacos', 'Soft tacos filled with lightly seasoned grilled fish, fresh slaw, and a creamy cilantro sauce.', 9.50, TRUE, 'fish_tacos.jpg'), -- 35
(6, 'Loaded Fries', 'Crispy fries topped with melted cheese, bacon bits, and green onions, served with a side of sour cream.', 4.50, TRUE, 'loaded_fries.jpg'), -- 36
(6, 'Falafel Wrap', 'Crunchy falafel balls wrapped in a soft tortilla with lettuce, tomato, and a drizzle of tahini.', 9.00, TRUE, 'falafel_wrap.jpg'), -- 37
(6, 'Cheese Nachos', 'Corn tortilla chips covered with a generous layer of melted cheese, jalapeños, and a side of salsa.', 7.00, TRUE, 'nachos.jpg'), -- 38
(6, 'Spicy Ramen', 'Authentic Spicy Ramen noodles served in a rich, fiery broth, topped with sliced pork, boiled eggs, and fresh green onions.', 8.50, TRUE, 'spicy_ramen.jpg'), -- 39
(6, 'Stinky Tofu', 'Deep-fried Stinky Tofu, renowned for its pungent aroma and crisp exterior, served with pickled cabbage and chili sauce.', 6.50, TRUE, 'stinky_tofu.jpg'), -- 40
(6, 'Grilled Cold Noodles', 'Chilled noodles with a sesame and soy sauce dressing, grilled to perfection and topped with cucumber, peanuts, and coriander.', 7.00, TRUE, 'grilled_cold_noodles.jpg'), -- 41

-- Frozen Treats
(7, 'Ice Blocks', 'Refreshing flavored ice blocks.', 3.50, TRUE, 'iceblock.jpg'), -- 42
(7, 'Real Fruit Ice Creams', 'Ice cream made with real fruit blended on the spot.', 7.50, TRUE, 'icecream.jpg'), -- 43
(7, 'Sorbet', 'Light and refreshing, our sorbet comes in a variety of fruity flavors, perfect for a dairy-free refreshment.', 3.00, TRUE, 'sorbet.jpg'), -- 44
(7, 'Frozen Yogurt', 'Enjoy our creamy frozen yogurt, available in classic and exotic flavors, topped with your choice of fruits or nuts.', 3.50, TRUE, 'froyo.jpg'), -- 45
(7, 'Gelato', 'Indulge in our rich and creamy gelato, crafted with the finest ingredients for a smooth and flavorful experience.', 8.00, TRUE, 'gelato.jpg'), -- 46

-- Travel Essentials & Souvenirs
(8, 'Sandfly Spray', 'Effective protection against sandflies and other biting insects, essential for enjoying the outdoors in comfort.', 12.00, TRUE, 'sandflyspray.jpg'), -- 47
(8, 'Sunscreen', 'The UV levels can be quite high, so sunscreen is a must to protect your skin.', 15.00, TRUE, 'sunscreen.jpg'), -- 48
(8, 'Rain Gear', 'The region is known for its rainfall, so a waterproof jacket or umbrella is advisable.', 50.00, TRUE, 'raingear.jpg'), -- 49
(8, 'Greenstone Jewelry', 'A significant cultural icon in New Zealand, sourced mainly from the West Coast.', 120.00, TRUE, 'greenstone.jpg'); -- 50


INSERT INTO `product_option` (`product_id`, `option_type`, `option_name`, `additional_cost`)
VALUES
-- Coffee Options (Milk Type, Size)
(1, 'Milk Type', 'Soy Milk', 0.50), (1, 'Milk Type', 'Almond Milk', 0.50), (1, 'Milk Type', 'Oat Milk', 0.50), 
(1, 'Size', 'Small', 0.00), (1, 'Size', 'Medium', 0.50), (1, 'Size', 'Large', 1.00),
(2, 'Milk Type', 'Soy Milk', 0.50), (2, 'Milk Type', 'Almond Milk', 0.50), (2, 'Milk Type', 'Oat Milk', 0.50), 
(2, 'Size', 'Small', 0.00), (2, 'Size', 'Medium', 0.50), (2, 'Size', 'Large', 1.00),
(3, 'Milk Type', 'Soy Milk', 0.50), (3, 'Milk Type', 'Almond Milk', 0.50), (3, 'Milk Type', 'Oat Milk', 0.50), 
(3, 'Size', 'Small', 0.00), (3, 'Size', 'Medium', 0.50), (3, 'Size', 'Large', 1.00),
(4, 'Milk Type', 'Soy Milk', 0.50), (4, 'Milk Type', 'Almond Milk', 0.50), (4, 'Milk Type', 'Oat Milk', 0.50), 
(4, 'Size', 'Small', 0.00), (4, 'Size', 'Medium', 0.50), (4, 'Size', 'Large', 1.00),
(5, 'Milk Type', 'Soy Milk', 0.50), (5, 'Milk Type', 'Almond Milk', 0.50), (5, 'Milk Type', 'Oat Milk', 0.50), 
(5, 'Size', 'Small', 0.00), (5, 'Size', 'Medium', 0.50), (5, 'Size', 'Large', 1.00),

-- Hot Drinks Options (Syrup Type)
(6, 'Syrup Type', 'Vanilla Syrup', 0.50), (6, 'Syrup Type', 'Caramel Syrup', 0.50), (6, 'Syrup Type', 'Hazelnut Syrup', 0.50),
(7, 'Syrup Type', 'Vanilla Syrup', 0.50), (7, 'Syrup Type', 'Caramel Syrup', 0.50), (7, 'Syrup Type', 'Hazelnut Syrup', 0.50),
(8, 'Syrup Type', 'Vanilla Syrup', 0.50), (8, 'Syrup Type', 'Caramel Syrup', 0.50), (8, 'Syrup Type', 'Hazelnut Syrup', 0.50),

-- Soft Drinks Options (No Options)
(9, 'No Option', 'No option', 0.00), (10, 'No Option', 'No option', 0.00), (11, 'No Option', 'No option', 0.00), 
(12, 'No Option', 'No option', 0.00), (13, 'No Option', 'No option', 0.00),

-- Milkshakes Options (Ice Level)
(14, 'Ice Level', 'Light Ice', 0.00), (14, 'Ice Level', 'No Ice', 0.00),
(15, 'Ice Level', 'Light Ice', 0.00), (15, 'Ice Level', 'No Ice', 0.00),
(16, 'Ice Level', 'Light Ice', 0.00), (16, 'Ice Level', 'No Ice', 0.00),
(17, 'Ice Level', 'Light Ice', 0.00), (17, 'Ice Level', 'No Ice', 0.00),
(18, 'Ice Level', 'Light Ice', 0.00), (18, 'Ice Level', 'No Ice', 0.00),
(19, 'Ice Level', 'Light Ice', 0.00), (19, 'Ice Level', 'No Ice', 0.00),
(20, 'Ice Level', 'Light Ice', 0.00), (20, 'Ice Level', 'No Ice', 0.00),

-- Iced Teas Options (Ice Level)
(21, 'Ice Level', 'Light Ice', 0.00), (21, 'Ice Level', 'No Ice', 0.00),
(22, 'Ice Level', 'Light Ice', 0.00), (22, 'Ice Level', 'No Ice', 0.00),
(23, 'Ice Level', 'Light Ice', 0.00), (23, 'Ice Level', 'No Ice', 0.00),
(24, 'Ice Level', 'Light Ice', 0.00), (24, 'Ice Level', 'No Ice', 0.00),
(25, 'Ice Level', 'Light Ice', 0.00), (25, 'Ice Level', 'No Ice', 0.00),
(26, 'Ice Level', 'Light Ice', 0.00), (26, 'Ice Level', 'No Ice', 0.00),

-- Fast Food Options (Bun Type, Toppings, Sauce Type)
-- American Hotdogs (27)
(27, 'Add on', 'Gluten-Free Bun', 0.50),
(27, 'Add on', 'Sesame Bun', 0.20),
(27, 'Add on', 'Extra Cheese', 0.50),
(27, 'Add on', 'Bacon', 0.75),
(27, 'Add on', 'Grilled Onions', 0.25),
(27, 'Add on', 'BBQ Sauce', 0.00),
(27, 'Add on', 'Mustard', 0.00),
(27, 'Add on', 'Mayo', 0.00),

-- Sweetcorn & Kumara Patties (28)
(28, 'Add on', 'Gluten-Free Bun', 0.50),
(28, 'Add on', 'Sesame Bun', 0.20),
(28, 'Add on', 'Extra Cheese', 0.50),
(28, 'Add on', 'Bacon', 0.75),
(28, 'Add on', 'Grilled Onions', 0.25),
(28, 'Add on', 'BBQ Sauce', 0.00),
(28, 'Add on', 'Mustard', 0.00),
(28, 'Add on', 'Mayo', 0.00),

-- Crepes (29)
(29, 'Add on', 'Gluten-Free Bun', 0.50),
(29, 'Add on', 'Sesame Bun', 0.20),
(29, 'Add on', 'Extra Cheese', 0.50),
(29, 'Add on', 'Bacon', 0.75),
(29, 'Add on', 'Grilled Onions', 0.25),
(29, 'Add on', 'BBQ Sauce', 0.00),
(29, 'Add on', 'Mustard', 0.00),
(29, 'Add on', 'Mayo', 0.00),

-- Smokey BBQ Pulled Pork in a Bun (30)
(30, 'Add on', 'Gluten-Free Bun', 0.50),
(30, 'Add on', 'Sesame Bun', 0.20),
(30, 'Add on', 'Extra Cheese', 0.50),
(30, 'Add on', 'Bacon', 0.75),
(30, 'Add on', 'Grilled Onions', 0.25),
(30, 'Add on', 'BBQ Sauce', 0.00),
(30, 'Add on', 'Mustard', 0.00),
(30, 'Add on', 'Mayo', 0.00),

-- Muffins (31)
(31, 'Add on', 'Gluten-Free Bun', 0.50),
(31, 'Add on', 'Sesame Bun', 0.20),
(31, 'Add on', 'Extra Cheese', 0.50),
(31, 'Add on', 'Bacon', 0.75),
(31, 'Add on', 'Grilled Onions', 0.25),
(31, 'Add on', 'BBQ Sauce', 0.00),
(31, 'Add on', 'Mustard', 0.00),
(31, 'Add on', 'Mayo', 0.00),

-- Slices (32)
(32, 'Add on', 'Gluten-Free Bun', 0.50),
(32, 'Add on', 'Sesame Bun', 0.20),
(32, 'Add on', 'Extra Cheese', 0.50),
(32, 'Add on', 'Bacon', 0.75),
(32, 'Add on', 'Grilled Onions', 0.25),
(32, 'Add on', 'BBQ Sauce', 0.00),
(32, 'Add on', 'Mustard', 0.00),
(32, 'Add on', 'Mayo', 0.00),

-- Chicken Tenders (33)
(33, 'Add on', 'Gluten-Free Bun', 0.50),
(33, 'Add on', 'Sesame Bun', 0.20),
(33, 'Add on', 'Extra Cheese', 0.50),
(33, 'Add on', 'Bacon', 0.75),
(33, 'Add on', 'Grilled Onions', 0.25),
(33, 'Add on', 'BBQ Sauce', 0.00),
(33, 'Add on', 'Mustard', 0.00),
(33, 'Add on', 'Mayo', 0.00),

-- Veggie Burger (34)
(34, 'Add on', 'Gluten-Free Bun', 0.50),
(34, 'Add on', 'Sesame Bun', 0.20),
(34, 'Add on', 'Extra Cheese', 0.50),
(34, 'Add on', 'Bacon', 0.75),
(34, 'Add on', 'Grilled Onions', 0.25),
(34, 'Add on', 'BBQ Sauce', 0.00),
(34, 'Add on', 'Mustard', 0.00),
(34, 'Add on', 'Mayo', 0.00),

-- Fish Tacos (35)
(35, 'Add on', 'Gluten-Free Bun', 0.50),
(35, 'Add on', 'Sesame Bun', 0.20),
(35, 'Add on', 'Extra Cheese', 0.50),
(35, 'Add on', 'Bacon', 0.75),
(35, 'Add on', 'Grilled Onions', 0.25),
(35, 'Add on', 'BBQ Sauce', 0.00),
(35, 'Add on', 'Mustard', 0.00),
(35, 'Add on', 'Mayo', 0.00),

-- Loaded Fries (36)
(36, 'Add on', 'Gluten-Free Bun', 0.50),
(36, 'Add on', 'Sesame Bun', 0.20),
(36, 'Add on', 'Extra Cheese', 0.50),
(36, 'Add on', 'Bacon', 0.75),
(36, 'Add on', 'Grilled Onions', 0.25),
(36, 'Add on', 'BBQ Sauce', 0.00),
(36, 'Add on', 'Mustard', 0.00),
(36, 'Add on', 'Mayo', 0.00),

-- Falafel Wrap (37)
(37, 'Add on', 'Gluten-Free Bun', 0.50),
(37, 'Add on', 'Sesame Bun', 0.20),
(37, 'Add on', 'Extra Cheese', 0.50),
(37, 'Add on', 'Bacon', 0.75),
(37, 'Add on', 'Grilled Onions', 0.25),
(37, 'Add on', 'BBQ Sauce', 0.00),
(37, 'Add on', 'Mustard', 0.00),
(37, 'Add on', 'Mayo', 0.00),

-- Cheese Nachos (38)
(38, 'Add on', 'Gluten-Free Bun', 0.50),
(38, 'Add on', 'Sesame Bun', 0.20),
(38, 'Add on', 'Extra Cheese', 0.50),
(38, 'Add on', 'Bacon', 0.75),
(38, 'Add on', 'Grilled Onions', 0.25),
(38, 'Add on', 'BBQ Sauce', 0.00),
(38, 'Add on', 'Mustard', 0.00),
(38, 'Add on', 'Mayo', 0.00),

-- Spicy Ramen (39)
(39, 'Add on', 'Gluten-Free Bun', 0.50),
(39, 'Add on', 'Sesame Bun', 0.20),
(39, 'Add on', 'Extra Cheese', 0.50),
(39, 'Add on', 'Bacon', 0.75),
(39, 'Add on', 'Grilled Onions', 0.25),
(39, 'Add on', 'BBQ Sauce', 0.00),
(39, 'Add on', 'Mustard', 0.00),
(39, 'Add on', 'Mayo', 0.00),
-- Stinky Tofu (40)
(40, 'Add on', 'Gluten-Free Bun', 0.50),
(40, 'Add on', 'Sesame Bun', 0.20),
(40, 'Add on', 'Extra Cheese', 0.50),
(40, 'Add on', 'Bacon', 0.75),
(40, 'Add on', 'Grilled Onions', 0.25),
(40, 'Add on', 'BBQ Sauce', 0.00),
(40, 'Add on', 'Mustard', 0.00),
(40, 'Add on', 'Mayo', 0.00),
-- Grilled Cold Noodles
(41, 'Add on', 'Gluten-Free Bun', 0.50),
(41, 'Add on', 'Sesame Bun', 0.20),
(41, 'Add on', 'Extra Cheese', 0.50),
(41, 'Add on', 'Bacon', 0.75),
(41, 'Add on', 'Grilled Onions', 0.25),
(41, 'Add on', 'BBQ Sauce', 0.00),
(41, 'Add on', 'Mustard', 0.00),
(41, 'Add on', 'Mayo', 0.00),

-- Frozen Treats Options (Fruit Flavor)
-- Ice Blocks
(42, 'Fruit Flavor', 'Strawberry', 0.00), 
(42, 'Fruit Flavor', 'Banana', 0.00), 
(42, 'Fruit Flavor', 'Mixed Berry', 0.00), 
(42, 'Fruit Flavor', 'Mango', 0.00), 
(42, 'Fruit Flavor', 'Peach', 0.00), 
(42, 'Fruit Flavor', 'Blackberry', 0.00),

-- Real Fruit Ice Creams
(43, 'Fruit Flavor', 'Strawberry', 0.00), 
(43, 'Fruit Flavor', 'Banana', 0.00), 
(43, 'Fruit Flavor', 'Mixed Berry', 0.00), 
(43, 'Fruit Flavor', 'Mango', 0.00), 
(43, 'Fruit Flavor', 'Peach', 0.00), 
(43, 'Fruit Flavor', 'Blackberry', 0.00),

-- Sorbet
(44, 'Fruit Flavor', 'Strawberry', 0.00), 
(44, 'Fruit Flavor', 'Banana', 0.00), 
(44, 'Fruit Flavor', 'Mixed Berry', 0.00), 
(44, 'Fruit Flavor', 'Mango', 0.00), 
(44, 'Fruit Flavor', 'Peach', 0.00), 
(44, 'Fruit Flavor', 'Blackberry', 0.00),

-- Frozen Yogurt
(45, 'Fruit Flavor', 'Strawberry', 0.00), 
(45, 'Fruit Flavor', 'Banana', 0.00), 
(45, 'Fruit Flavor', 'Mixed Berry', 0.00), 
(45, 'Fruit Flavor', 'Mango', 0.00), 
(45, 'Fruit Flavor', 'Peach', 0.00), 
(45, 'Fruit Flavor', 'Blackberry', 0.00),

-- Gelato
(46, 'Fruit Flavor', 'Strawberry', 0.00), 
(46, 'Fruit Flavor', 'Banana', 0.00), 
(46, 'Fruit Flavor', 'Mixed Berry', 0.00), 
(46, 'Fruit Flavor', 'Mango', 0.00), 
(46, 'Fruit Flavor', 'Peach', 0.00), 
(46, 'Fruit Flavor', 'Blackberry', 0.00),

-- Travel Essentials & Souvenirs (No Option)
(47, 'No Option', 'No option', 0.00),
(48, 'No Option', 'No option', 0.00),
(49, 'No Option', 'No option', 0.00),
(50, 'No Option', 'No option', 0.00);
INSERT INTO `inventory` (`staff_id`, `manager_id`, `product_id`, `option_id`, `quantity`)
VALUES
-- Frozen Treats (Fruit Flavor)
-- Ice Blocks
(1, 1, 42, 25, 50), -- Ice Blocks (Strawberry)
(1, 1, 42, 26, 50), -- Ice Blocks (Banana)
(1, 1, 42, 27, 50), -- Ice Blocks (Mixed Berry)
(1, 1, 42, 28, 50), -- Ice Blocks (Mango)
(1, 1, 42, 29, 50), -- Ice Blocks (Peach)
(1, 1, 42, 30, 50), -- Ice Blocks (Blackberry)

-- Real Fruit Ice Creams
(1, 1, 43, 25, 50), -- Real Fruit Ice Creams (Strawberry)
(1, 1, 43, 26, 50), -- Real Fruit Ice Creams (Banana)
(1, 1, 43, 27, 50), -- Real Fruit Ice Creams (Mixed Berry)
(1, 1, 43, 28, 50), -- Real Fruit Ice Creams (Mango)
(1, 1, 43, 29, 50), -- Real Fruit Ice Creams (Peach)
(1, 1, 43, 30, 50), -- Real Fruit Ice Creams (Blackberry)

-- Sorbet
(1, 1, 44, 25, 50), -- Sorbet (Strawberry)
(1, 1, 44, 26, 50), -- Sorbet (Banana)
(1, 1, 44, 27, 50), -- Sorbet (Mixed Berry)
(1, 1, 44, 28, 50), -- Sorbet (Mango)
(1, 1, 44, 29, 50), -- Sorbet (Peach)
(1, 1, 44, 30, 50), -- Sorbet (Blackberry)

-- Frozen Yogurt
(1, 1, 45, 25, 50), -- Frozen Yogurt (Strawberry)
(1, 1, 45, 26, 50), -- Frozen Yogurt (Banana)
(1, 1, 45, 27, 50), -- Frozen Yogurt (Mixed Berry)
(1, 1, 45, 28, 50), -- Frozen Yogurt (Mango)
(1, 1, 45, 29, 50), -- Frozen Yogurt (Peach)
(1, 1, 45, 30, 50), -- Frozen Yogurt (Blackberry)

-- Gelato
(1, 1, 46, 25, 50), -- Gelato (Strawberry)
(1, 1, 46, 26, 50), -- Gelato (Banana)
(1, 1, 46, 27, 50), -- Gelato (Mixed Berry)
(1, 1, 46, 28, 50), -- Gelato (Mango)
(1, 1, 46, 29, 50), -- Gelato (Peach)
(1, 1, 46, 30, 50), -- Gelato (Blackberry)

-- Soft Drinks (only product inventory)
(1, 1, 9, NULL, 50), -- Coca-Cola
(1, 1, 10, NULL, 50), -- Sprite
(1, 1, 11, NULL, 50), -- Fanta
(1, 1, 12, NULL, 50), -- Pepsi
(1, 1, 13, NULL, 50), -- Ginger Ale

-- Milkshakes (only product inventory)
(1, 1, 14, NULL, 50), -- Classic Vanilla
(1, 1, 15, NULL, 50), -- Rich Chocolate
(1, 1, 16, NULL, 50), -- Strawberry Delight
(1, 1, 17, NULL, 50), -- Caramel Swirl
(1, 1, 18, NULL, 50), -- Banana Bliss
(1, 1, 19, NULL, 50), -- Cookies and Cream
(1, 1, 20, NULL, 50), -- Seasonal Berry

-- Iced Teas (only product inventory)
(1, 1, 21, NULL, 50), -- Classic Lemon Iced Tea
(1, 1, 22, NULL, 50), -- Peach Iced Tea
(1, 1, 23, NULL, 50), -- Raspberry Iced Tea
(1, 1, 24, NULL, 50), -- Green Iced Tea
(1, 1, 25, NULL, 50), -- Hibiscus Iced Tea
(1, 1, 26, NULL, 50), -- Mint Iced Tea

-- Fast Food (only product inventory)
(1, 1, 27, NULL, 50), -- American Hotdogs
(1, 1, 28, NULL, 50), -- Sweetcorn & Kumara Patties
(1, 1, 29, NULL, 50), -- Crepes
(1, 1, 30, NULL, 50), -- Smokey BBQ Pulled Pork in a Bun
(1, 1, 31, NULL, 50), -- Muffins
(1, 1, 32, NULL, 50), -- Slices
(1, 1, 33, NULL, 50), -- Chicken Tenders
(1, 1, 34, NULL, 50), -- Veggie Burger
(1, 1, 35, NULL, 50), -- Fish Tacos
(1, 1, 36, NULL, 50), -- Loaded Fries
(1, 1, 37, NULL, 50), -- Falafel Wrap
(1, 1, 38, NULL, 50), -- Cheese Nachos
(1, 1, 39, NULL, 50), -- Spicy Ramen
(1, 1, 40, NULL, 50), -- Stinky Tofu
(1, 1, 41, NULL, 50), -- Grilled Cold Noodles

-- Travel Essentials & Souvenirs (only product inventory)
(1, 1, 47, NULL, 50), -- Sandfly Spray
(1, 1, 48, NULL, 50), -- Sunscreen
(1, 1, 49, NULL, 50), -- Rain Gear
(1, 1, 50, NULL, 50); -- Greenstone Jewelry


-- 11. Insert into orders
INSERT INTO `orders` (`customer_id`, `total_price`, `special_requests`, `scheduled_pickup_time`, `status`, `created_at`) VALUES 
(1000, 20.00, 'Please add extra sugar to the Hot Chocolate.', '2024-05-19 15:00', 'ordered', '2024-05-19 14:00'),
(1000, 13.50, 'No ice in the Sprite, please.', '2024-05-18 16:00', 'ordered', '2024-05-18 15:00');


-- 11. Insert into order_item
INSERT INTO `order_item` (`order_id`, `product_id`, `quantity`) VALUES 
(1, 1, 1), -- Espresso
(1, 6, 1), -- Hot Chocolate
(1, 9, 2), -- Coca-Cola
(2, 4, 1), -- Flat White
(2, 10, 1), -- Sprite
(2, 11, 1); -- Fanta


-- 13. insert accommodation
INSERT INTO accommodation (accommodation_id, type, description, capacity, space, price_per_night, is_available, image)
VALUES
(1, 'Dorm', 'Our dorm features four comfortable single bunks, perfect for family or friends eager to stay together. Ideal for groups of four, you can book the entire room to enjoy a private experience. Alternatively, book just one bunk and embrace the opportunity to meet and share the space with three new friends. Whether you are a solo traveler or planning a group adventure, our dorm offers a fun and affordable accommodation option.', 4, 4, 55, TRUE, 'dorm.jpg'),
(2, 'Twin', 'Our twin bed room is thoughtfully designed for comfort and privacy, featuring two single beds for friends traveling together or solo travelers seeking extra space. Guests have convenient access to modern shared bathroom and kitchen facilities, which are maintained to the highest standards. Whether you’re in town for business or leisure, our twin bed room offers a comfortable base for your adventures.', 2, 1, 155, TRUE, 'twin.jpg'),
(3, 'Queen', 'Perfect for couples or families, our Queen bed room features a luxurious queen-sized bed and a convenient pull-out sofa, making it ideal for up to three guests. Guests have convenient access to modern shared bathroom and kitchen facilities, which are cleaned and maintained to the highest standards. It’s more than just a place to sleep—it’s a home away from home to live, laugh, and create memories.', 3, 1, 205, TRUE, 'queen.jpg');

-- 15. insert booking table--
INSERT INTO booking 
VALUES
(1, 1000, 1, 1, '2024-05-24', '2024-05-29', 1, 0, 1, 1, 'confirmed', '2024-05-11'),
(2, 1000, 1, 2, '2024-05-21', '2024-05-22', 1, 0, 1, 1, 'confirmed', '2024-05-12'),
(3, 1000, 1, 3, '2024-05-22', '2024-05-25', 1, 0, 1, 1, 'confirmed', '2024-05-12'),
(4, 1000, 1, 3, '2024-02-25', '2024-02-26', 1, 0, 1, 1, 'checked out', '2024-01-12');

-- 16. insert message table--
INSERT INTO `message` (`message_id`, `customer_id`, `manager_id`, `staff_id`, `content`)
VALUES (1, 1000, NULL, 1, 'This is a test message.');

-- 18. insert into payment_type
INSERT INTO `payment_type` (`payment_type_id`, `payment_type`)VALUES
(1, 'gift_card'),
(2, 'bank_card'),
(3, 'promotion');

-- 19. insert into bank_card
INSERT INTO `bank_card` (`bank_card_id`, `card_num`, `expire_Date`, `payment_type_id`) VALUES
(1, 1234567812345678, '2025-12-31', 2),
(2, 8765432187654321, '2024-06-30', 2),
(3, 1111222233334444, '2026-01-15', 2);

-- 20. insert into gift_Card
INSERT INTO `gift_card` (`gift_card_id`, `code`, `balance`, `expiration_date`, `is_active`, `purchase_amount`, `payment_type_id`)
VALUES (1, 'GFT123456', 100.00, '2025-01-31', TRUE, 100.00, 1);

-- 22. insert payment table--
INSERT INTO `payment` (`customer_id`, `payment_type_id`, `order_id`, `booking_id`, `paid_amount`)
VALUES
(1000, 1, NULL, 1, 55.00),
(1000, 2, NULL, 2, 155.00),
(1000, 2, NULL, 3, 615.00),
(1000, 2, NULL, 4, 205.00);


-- 26. insert cart table--


-- 27. insert cart_item_option table--
