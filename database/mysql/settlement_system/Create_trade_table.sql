CREATE TABLE trade (
    trade_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- Counterparty and instrument
    counterparty_name VARCHAR(100) NOT NULL,
	symbol VARCHAR(10) NULL,
    cusip VARCHAR(15) NOT NULL,
    
    -- Trade details
    trade_date DATE NULL,
    settlement_date DATE NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(18, 6) NOT NULL,
	net_amount DECIMAL(18, 2) AS (quantity * price) STORED,
	trade_currency CHAR(3) DEFAULT 'USD',
    settlement_currency CHAR(3) DEFAULT 'USD',
    book_name VARCHAR(10) NOT NULL,
    
    -- Status tracking
    settlement_status ENUM('NOT_STARTED', 'IN_PROCESS', 'SETTLED', 'FAILED') DEFAULT 'NOT_STARTED',
    
    -- Optional references for traceability
	source_system VARCHAR(64),
    uitid VARCHAR(64),
    settlement_location VARCHAR(64),

    -- Timestamps and metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);