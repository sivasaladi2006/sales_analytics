CREATE TABLE categories (
  category_id INT PRIMARY KEY AUTO_INCREMENT,
  category_name VARCHAR(100) NOT NULL
);


CREATE TABLE suppliers (
  supplier_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(150) NOT NULL,
  contact_info VARCHAR(100) NOT NULL
);


CREATE TABLE customers (
  customer_id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(150) NOT NULL,
  region VARCHAR(100) NOT NULL
);


CREATE TABLE products (
  product_id INT PRIMARY KEY AUTO_INCREMENT,
  product_name VARCHAR(150) NOT NULL,
  category_id INT NOT NULL,
  supplier_id INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,

  FOREIGN KEY (category_id) REFERENCES categories(category_id),
  FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);


CREATE TABLE orders (
  order_id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT NOT NULL,
  order_date DATE NOT NULL,

  FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);


CREATE TABLE order_items (
  order_item_id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity DECIMAL(10,2) NOT NULL,
  unit_price_at_order DECIMAL(10,2) NOT NULL,

  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);


CREATE TABLE inventory (
  product_id INT PRIMARY KEY,
  stock_available DECIMAL(10,2) NOT NULL,
  last_restocked_date DATE NOT NULL,

  FOREIGN KEY (product_id) REFERENCES products(product_id)
);


CREATE INDEX idx_orders_order_date
ON orders(order_date);

CREATE INDEX idx_inventory_stock_available
ON inventory(stock_available);