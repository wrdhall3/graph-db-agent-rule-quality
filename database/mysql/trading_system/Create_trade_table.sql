CREATE TABLE trade (
    trade_id INT AUTO_INCREMENT PRIMARY KEY,
    trader_id VARCHAR(32) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    cusip VARCHAR(15) NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    trade_date DATE, 
    settle_date DATE,
    quantity INT NOT NULL,
    price DECIMAL(15, 4) NOT NULL,
    net_amount DECIMAL(18, 2) AS (quantity * price) STORED,
    trade_currency CHAR(3) DEFAULT 'USD',
    settlement_currency CHAR(3) DEFAULT 'USD',
    book_name VARCHAR(10) NOT NULL,
    uitid VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
