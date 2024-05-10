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

-- 5. manager
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

-- 6 . product_category
CREATE TABLE `product_category` (
    `category_id` INT AUTO_INCREMENT,
    `name` VARCHAR(225) NOT NULL,
    `description` VARCHAR(500),
    PRIMARY KEY (`category_id`)
) ENGINE=InnoDB;

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
	`option_type_id` INT AUTO_INCREMENT,
    `description` VARCHAR(500),
	PRIMARY KEY (`option_type_id`) -- 描述产品选项的类型，如大小、糖浆类型、牛奶类型。
)ENGINE=InnoDB;

CREATE TABLE `product_option` (
    `option_id` INT AUTO_INCREMENT,
    `option_type_id` INT,
    `name` VARCHAR(500),
    `additional_cost` DECIMAL(10, 2),
    PRIMARY KEY (`option_id`),
    FOREIGN KEY (`option_type_id`) REFERENCES `product_option_type` (`option_type_id`)
) ENGINE=InnoDB;

CREATE TABLE `product_option_mapping` (
	`product_id` INT,
    `option_id` INT,
    PRIMARY KEY (`product_id`, `option_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product` (`product_id`),
    FOREIGN KEY (`option_id`) REFERENCES `product_option` (`option_id`)
)AUTO_INCREMENT=1;

-- 8. orders
CREATE TABLE `orders` (
    `order_id` INT AUTO_INCREMENT,
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
    `order_item_id` INT AUTO_INCREMENT,
    `order_id` INT,
    `product_id` INT,
    `quantity` INT,
    PRIMARY KEY (`order_item_id`),
    FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
    FOREIGN KEY (`product_id`) REFERENCES `product`(`product_id`)
)AUTO_INCREMENT=1;

-- 10. inventory
CREATE TABLE `inventory` (
    `inventory_id` INT AUTO_INCREMENT,
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
    `accommodation_id` INT AUTO_INCREMENT,
    `type` ENUM('dorm', 'twin', 'queen') NOT NULL,
    `description` TEXT,
    `capacity` INT,
    `price_per_night` DECIMAL(10,2),
    `is_available` BOOLEAN DEFAULT TRUE,
    `image` VARCHAR(500),
    PRIMARY KEY (`accommodation_id`)
)AUTO_INCREMENT=1;

CREATE TABLE `blocked_dates` (
    `block_id` INT AUTO_INCREMENT,
    `accommodation_id` INT,
    `start_date` DATE,
    `end_date` DATE,
    `is_active` BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (`block_id`),
    FOREIGN KEY (`accommodation_id`) REFERENCES `accommodation` (`accommodation_id`)
)AUTO_INCREMENT=1;

-- 11. booking
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


-- 12. message
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

-- 13. loyalty_point
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

-- 14. payment_type
CREATE TABLE `payment_type` (
    `payment_type_id` INT AUTO_INCREMENT,
    `payment_type` VARCHAR(50),
    PRIMARY KEY (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 15. bank_card
CREATE TABLE `bank_Card` (
    `bank_card_id` INT AUTO_INCREMENT,
    `card_num` INT,
    `expire_Date` DATE,
	`payment_type_id` INT,
    PRIMARY KEY (`bank_card_id`),
    FOREIGN KEY (`payment_type_id`) REFERENCES `payment_type` (`payment_type_id`)
)AUTO_INCREMENT=1;

-- 16. gift_card
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

-- 17. promotion
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

-- 18. payment
CREATE TABLE `payment` (
    `payment_id` INT AUTO_INCREMENT,
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
    `news_id` INT AUTO_INCREMENT,
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
VALUES (1000, 3, 'cc', 'CC', '123-456-7890', '1985-10-25', 'Male', 'AB1234567', CURRENT_TIMESTAMP, 'cc.jpg', 'active');

INSERT INTO `payment_type` (`payment_type_id`, `payment_type`)
VALUES (1, 'gift_card');

INSERT INTO `gift_card` (`gift_card_id`, `code`, `balance`, `expiration_date`, `is_active`, `purchase_amount`, `payment_type_id`)
VALUES (1, 'GFT123456', 100.00, '2025-01-31', TRUE, 100.00, 1);

INSERT INTO `message` (`message_id`, `customer_id`, `manager_id`, `staff_id`, `content`)
VALUES (1, 1000, NULL, 1, 'This is a test message.');

-- Insert into product_category
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
-- Insert into product
INSERT INTO `product` (`category_id`, `name`, `description`, `unit_price`, `special_requests`, `is_available`, `image`)
VALUES 
(1, 'Espresso', 'Strong black coffee made by forcing steam through ground coffee beans.', 4.50, '', TRUE, 'espresso.jpg'),
(1, 'Latte', 'Coffee drink made with espresso and steamed milk.', 6.00, '', TRUE, 'latte.jpg'),
(1, 'Cappuccino', 'Coffee-based drink made with equal parts of espresso, steamed milk, and frothed milk.', 6.00, '', TRUE, 'cappuccino.jpg'),
(1, 'Flat White', 'Smooth and velvety coffee made with espresso and steamed milk.', 6.00, '', TRUE, 'flatwhite.jpg'),
(1, 'Mocha', 'Espresso with steamed milk and chocolate syrup, topped with whipped cream.', 6.50, '', TRUE, 'mocha.jpg'),
(2, 'Hot Chocolate', 'Rich and creamy hot chocolate made with real cocoa.', 5.00, '', TRUE, 'hotchocolate.jpg'),
(2, 'Herbal Tea', 'A soothing blend of herbal ingredients steeped to perfection.', 6.50, '', TRUE, 'herbaltea.jpg'),
(2, 'Chai Latte', 'Spiced tea beverage made with aromatic spices and steamed milk.', 5.00, '', TRUE, 'chai.jpg'),
(3, 'Coca-Cola', 'Classic cola-flavored soft drink.',3.00, 'Diet option available', TRUE, 'cola.jpg'),
(3, 'Sprite', 'Crisp, refreshing lemon-lime flavored soda.', 3.00, '', TRUE, 'sprite.jpg'),
(3, 'Fanta', 'Bright, bubbly and instantly refreshing orange soda.', 3.00, '', TRUE, 'fanta.jpg'),
(3, 'Pepsi', 'Bold, refreshing cola drink with a rich flavor.', 3.00, 'Diet option available', TRUE, 'pepsi.jpg'),
(3, 'Ginger Ale', 'Gently carbonated, soothing ginger-flavored soda.', 5.00, '', TRUE, 'ginger.jpg'),
(4, 'Classic Vanilla', 'Smooth and creamy vanilla milkshake.', 7.00, '', TRUE, 'vanilla.jpg'),
(4, 'Rich Chocolate', 'Decadent chocolate milkshake made from real cocoa.', 7.00, '', TRUE, 'chocolate.jpg'),
(4, 'Strawberry Delight', 'Fresh and fruity strawberry milkshake.', 7.00, '', TRUE, 'strawberry.jpg'),
(4, 'Caramel Swirl', 'Creamy milkshake with rich caramel swirls.', 7.00, '', TRUE, 'caramel.jpg'),
(4, 'Banana Bliss', 'Creamy milkshake blended with ripe bananas.', 7.00, '', TRUE, 'banana.jpg'),
(4, 'Cookies and Cream', 'Crushed cookies mixed into a creamy milkshake.', 7.00, '', TRUE, 'cookie.jpg'),
(4, 'Seasonal Berry', 'Blend of seasonal berries in a refreshing milkshake.', 7.00, '', TRUE, 'berry.jpg'),
(5, 'Classic Lemon Iced Tea', 'Iced tea flavored with a twist of lemon.', 4.50, 'Sweetened and Unsweetened options available', TRUE, 'lemontea.jpg'),
(5, 'Peach Iced Tea', 'Refreshing iced tea infused with peach flavors.', 4.50, 'Sweetened and Unsweetened options available', TRUE, 'peachtea.jpg'),
(5, 'Raspberry Iced Tea', 'Iced tea infused with the essence of raspberries.', 4.50, 'Sweetened and Unsweetened options available', TRUE, 'rasberrytea.jpg'),
(5, 'Green Iced Tea', 'Smooth and mellow green tea served chilled.', 4.50, 'Sweetened and Unsweetened options available', TRUE, 'greentea.jpg'),
(5, 'Hibiscus Iced Tea', 'Tangy and refreshing hibiscus-flavored iced tea.', 4.50, 'Sweetened and Unsweetened options available', TRUE, 'hibiscuctea.jpg'),
(5, 'Mint Iced Tea', 'Cooling mint-flavored iced tea.', 4.50, 'Sweetened and Unsweetened options available', TRUE, 'minttea.jpg'),
(6, 'American Hotdogs', 'Classic grilled hotdogs with a selection of toppings.', 8.00, 'Add-ons available: cheese, bacon, onions, relish', TRUE, 'hotdog.jpg'),
(6, 'Sweetcorn & Kumara Patties', 'Delicious patties made from sweetcorn and kumara.', 8.50, 'Gluten-free option available', TRUE, 'pattie.jpg'),
(6, 'Crepes', 'Thin pancakes served with various toppings.', 8.00, 'Topping choices: chocolate, fruits, honey, syrup', TRUE, 'crepes.jpg'),
(6, 'Smokey BBQ Pulled Pork in a Bun', 'Slow-cooked pulled pork smothered in Smokey BBQ sauce, served in a soft bun.', 10.00, '', TRUE, 'bun.jpg'),
(6, 'Muffins', 'Freshly baked muffins available in several flavors.', 4.50, 'Flavor choices: blueberry, chocolate chip, bran', TRUE, 'muffins.jpg'),
(6, 'Slices', 'Assorted homemade slices.', 3.00, 'Varieties include: lemon, brownie, caramel', TRUE, 'slice.jpg'),
(6, 'Chicken Tenders', 'Crispy on the outside, juicy on the inside, our chicken tenders are served with your choice of dipping sauces.', 7.50, '', TRUE, 'chicken_tenders.jpg'),
(6, 'Veggie Burger', 'A hearty, meat-free patty served on a toasted bun with lettuce, tomato, and your choice of sauce.', 9.00, '', TRUE, 'veggie_burger.jpg'),
(6, 'Fish Tacos', 'Soft tacos filled with lightly seasoned grilled fish, fresh slaw, and a creamy cilantro sauce.', 9.50, '', TRUE, 'fish_tacos.jpg'),
(6, 'Loaded Fries', 'Crispy fries topped with melted cheese, bacon bits, and green onions, served with a side of sour cream.', 4.50, '', TRUE, 'loaded_fries.jpg'),
(6, 'Falafel Wrap', 'Crunchy falafel balls wrapped in a soft tortilla with lettuce, tomato, and a drizzle of tahini.', 9.00, '', TRUE, 'falafel_wrap.jpg'),
(6, 'Cheese Nachos', 'Corn tortilla chips covered with a generous layer of melted cheese, jalapeños, and a side of salsa.', 7.00, '', TRUE, 'nachos.jpg'),
(6, 'Spicy Ramen', 'Authentic Spicy Ramen noodles served in a rich, fiery broth, topped with sliced pork, boiled eggs, and fresh green onions.', 8.50, '', TRUE, 'spicy_ramen.jpg'),
(6, 'Stinky Tofu', 'Deep-fried Stinky Tofu, renowned for its pungent aroma and crisp exterior, served with pickled cabbage and chili sauce.', 6.50, '', TRUE, 'stinky_tofu.jpg'),
(6, 'Grilled Cold Noodles', 'Chilled noodles with a sesame and soy sauce dressing, grilled to perfection and topped with cucumber, peanuts, and coriander.', 7.00, '', TRUE, 'grilled_cold_noodles.jpg'),
(7, 'Ice Blocks', 'Refreshing flavored ice blocks.', 3.50, 'Flavors include: raspberry, cola, lime', TRUE, 'iceblock.jpg'),
(7, 'Real Fruit Ice Creams', 'Ice cream made with real fruit blended on the spot.', 7.50, 'Fruit options: strawberry, banana, mixed berry', TRUE, 'icecream.jpg'),
(7, 'Sorbet', 'Light and refreshing, our sorbet comes in a variety of fruity flavors, perfect for a dairy-free refreshment.', 3.00, '', TRUE, 'sorbet.jpg'),
(7, 'Frozen Yogurt', 'Enjoy our creamy frozen yogurt, available in classic and exotic flavors, topped with your choice of fruits or nuts.', 3.50, '', TRUE, 'froyo.jpg'),
(7, 'Gelato', 'Indulge in our rich and creamy gelato, crafted with the finest ingredients for a smooth and flavorful experience.', 8.00, '', TRUE, 'gelato.jpg'),
(8, 'Sandfly Spray', 'Effective protection against sandflies and other biting insects, essential for enjoying the outdoors in comfort.', 12.00, '', TRUE, 'sandflyspray.jpg'),
(8, 'Sunscreen', 'The UV levels can be quite high, so sunscreen is a must to protect your skin.', 15.00, '', TRUE, 'sunscreen.jpg'),
(8, 'Rain Gear', 'The region is known for its rainfall, so a waterproof jacket or umbrella is advisable.', 50.00, 'Available in various sizes and colors', TRUE, 'raingear.jpg'),
(8, 'Greenstone Jewelry', 'A significant cultural icon in New Zealand, sourced mainly from the West Coast.', 120.00, '', TRUE, 'greenstone.jpg');

-- Insert into product_option_type
INSERT INTO `product_option_type` (`description`)
VALUES 
('Milk Type'), 
('Syrup Type'),
('Ice Level'), 
('Extra Flavor'),
('Bun Type'), 
('Toppings'), 
('Sauce Type'),
('Cooking Style'),
('Fruit Flavor');

-- Insert into product_option (assuming Milk Type is option_type_id 1 and Syrup Type is option_type_id 2)
INSERT INTO `product_option` (`option_type_id`, `name`, `additional_cost`)
VALUES 
(1, 'Soy Milk', 0.50),
(1, 'Almond Milk', 0.50),
(1, 'Oat Milk', 0.50),
(2, 'Vanilla Syrup', 0.50),
(2, 'Caramel Syrup', 0.50),
(2, 'Hazelnut Syrup', 0.50),
(3, 'Light Ice', 0.00),
(3, 'No Ice', 0.00),
(4, 'Lemon Flavor', 0.50),
(4, 'Cinnamon', 0.20),
(4, 'Mint Flavor', 0.50),
(5, 'Gluten-Free Bun', 0.50),
(5, 'Sesame Bun', 0.20),
(6, 'Extra Cheese', 0.50),
(6, 'Bacon', 0.75),
(6, 'Grilled Onions', 0.25),
(7, 'BBQ Sauce', 0.00),
(7, 'Mustard', 0.00),
(7, 'Mayo', 0.00),
(8, 'Well Done', 0.00),
(8, 'Medium Well', 0.00),
(9, 'Strawberry', 0.00),
(9, 'Banana', 0.00),
(9, 'Mixed Berry', 0.00),
(9, 'Mango', 0.00),
(9, 'Peach', 0.00),
(9, 'Blackberry', 0.00),
(9, 'Kiwi', 0.00);

INSERT INTO `product_option_mapping` (`product_id`, `option_id`)
VALUES 
-- Map milk and syrup options to all coffee products
(1, 1), (1, 2), (1, 3), -- Soy Milk, Almond Milk, Oat Milk for Espresso
(1, 4), (1, 5), (1, 6), -- Vanilla, Caramel, Hazelnut Syrup for Espresso
(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), -- All milk and syrup options for Latte
(3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), -- All milk and syrup options for Cappuccino
(4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), -- All milk and syrup options for Flat White
(5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), -- All milk and syrup options for Mocha
-- Map ice level options to soft drinks and iced teas
(21, 7), (21, 8), -- Light Ice, No Ice for Coca-Cola
(22, 7), (22, 8), -- Light Ice, No Ice for Sprite
(23, 7), (23, 8), -- Light Ice, No Ice for Fanta
(24, 7), (24, 8), -- Light Ice, No Ice for Pepsi
(25, 7), (25, 8), -- Light Ice, No Ice for Ginger Ale
(26, 7), (26, 8), -- Light Ice, No Ice for Classic Lemon Iced Tea
(27, 7), (27, 8), -- Light Ice, No Ice for Peach Iced Tea
(28, 7), (28, 8), -- Light Ice, No Ice for Raspberry Iced Tea
(29, 7), (29, 8), -- Light Ice, No Ice for Green Iced Tea
(30, 7), (30, 8), -- Light Ice, No Ice for Hibiscus Iced Tea
(31, 7), (31, 8), -- Light Ice, No Ice for Mint Iced Tea

-- Map bun types, toppings, and sauce types to fast food items
(32, 5), (32, 6), (32, 7), -- Gluten-Free Bun, Sesame Bun, Extra Cheese for American Hotdogs
(33, 5), (33, 6), (33, 7), -- Gluten-Free Bun, Sesame Bun, Extra Cheese for Veggie Burger
(34, 5), (34, 6), (34, 7), -- Gluten-Free Bun, Sesame Bun, Extra Cheese for Fish Tacos
(32, 8), (32, 9), (32, 10), -- BBQ Sauce, Mustard, Mayo for American Hotdogs
(33, 8), (33, 9), (33, 10), -- BBQ Sauce, Mustard, Mayo for Veggie Burger
(34, 8), (34, 9), (34, 10), -- BBQ Sauce, Mustard, Mayo for Fish Tacos
(35, 5), (35, 6), (35, 7), (35, 8), (35, 9), (35, 10), -- Gluten-Free Bun, Sesame Bun, Extra Cheese, BBQ Sauce, Mustard, Mayo for Smokey BBQ Pulled Pork
(36, 5), (36, 6), (36, 7), (36, 8), (36, 9), (36, 10), -- Gluten-Free Bun, Sesame Bun, Extra Cheese, BBQ Sauce, Mustard, Mayo for Muffins
(37, 5), (37, 6), (37, 7), (37, 8), (37, 9), (37, 10), -- Gluten-Free Bun, Sesame Bun, Extra Cheese, BBQ Sauce, Mustard, Mayo for Slices
(38, 5), (38, 6), (38, 7), (38, 8), (38, 9), (38, 10), -- Gluten-Free Bun, Sesame Bun, Extra Cheese, BBQ Sauce, Mustard, Mayo for Chicken Tenders
(39, 5), (39, 6), (39, 7), (39, 8), (39, 9), (39, 10), -- Gluten-Free Bun, Sesame Bun, Extra Cheese, BBQ Sauce, Mustard, Mayo for Falafel Wrap
(40, 5), (40, 6), (40, 7), (40, 8), (40, 9), (40, 10), -- Gluten-Free Bun, Sesame Bun, Extra Cheese, BBQ Sauce, Mustard, Mayo for Cheese Nachos
(41, 5), (41, 6), (41, 7), (41, 8), (41, 9), (41, 10), -- Gluten-Free Bun, Sesame Bun, Extra Cheese, BBQ Sauce, Mustard, Mayo for Loaded Fries

-- Map fruit flavors to various frozen treat products
(42, 20), (42, 21), (42, 22), (42, 23), (42, 24), (42, 25), (42, 26), -- Strawberry, Banana, Mixed Berry, Mango, Peach, Blackberry, Kiwi for Ice Blocks
(43, 20), (43, 21), (43, 22), (43, 23), (43, 24), (43, 25), (43, 26), -- Strawberry, Banana, Mixed Berry, Mango, Peach, Blackberry, Kiwi for Real Fruit Ice Creams
(44, 20), (44, 21), (44, 22), (44, 23), (44, 24), (44, 25), (44, 26), -- Strawberry, Banana, Mixed Berry, Mango, Peach, Blackberry, Kiwi for Sorbet
(45, 20), (45, 21), (45, 22), (45, 23), (45, 24), (45, 25), (45, 26), -- Strawberry, Banana, Mixed Berry, Mango, Peach, Blackberry, Kiwi for Frozen Yogurt
(46, 20), (46, 21), (46, 22), (46, 23), (46, 24), (46, 25), (46, 26); -- Strawberry, Banana, Mixed Berry, Mango, Peach, Blackberry, Kiwi for Gelato
