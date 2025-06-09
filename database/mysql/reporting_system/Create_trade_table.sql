CREATE TABLE trade (
    trade_id BIGINT PRIMARY KEY,
    
    -- Trade identifiers
	uitid VARCHAR(64) NULL,
    
    -- Party and instrument data
    counterparty_name VARCHAR(100),
    book_name VARCHAR(10),
    trader_id VARCHAR(32),
    instrument_symbol VARCHAR(20),
    instrument_name VARCHAR(100),
    asset_class ENUM('EQUITY', 'BOND', 'FX', 'DERIVATIVE', 'COMMODITY'),

    -- Trade economics
    side ENUM('BUY', 'SELL'),
    trade_date DATE NULL,
    settlement_date DATE,
    quantity INT,
    price DECIMAL(18, 6),
    notional_value DECIMAL(20, 2) GENERATED ALWAYS AS (quantity * price) STORED,
    trade_currency CHAR(3) DEFAULT 'USD',
    settlement_currency CHAR(3) DEFAULT 'USD',
    
    -- Status and metadata
    trade_status ENUM('CONFIRMED', 'CANCELLED', 'SETTLED', 'AMENDED'),
    source_system VARCHAR(64),
    reporting_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amended_timestamp DATETIME,

    -- Regulatory tagging
    mifid_flag BOOLEAN DEFAULT FALSE,
    lei_code VARCHAR(20),
    trade_venue VARCHAR(50)
);