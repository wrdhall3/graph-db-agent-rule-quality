
INSERT INTO trade (
    trade_id, uitid, counterparty_name, book_name, trader_id,
    instrument_symbol, instrument_name, asset_class,
    side, trade_date, settlement_date, quantity, price,
    trade_currency, settlement_currency,
    trade_status, source_system, mifid_flag, lei_code, trade_venue
) VALUES
(1001, 'UIT-0001-ABC', 'ACME Broker', 'BOOK1', 'T123',
 'AAPL', 'Apple Inc.', 'EQUITY',
 'BUY', NULL, '2025-06-03', 100, 180.25,
 'USD', 'USD',
 'CONFIRMED', 'Trade System', TRUE, 'LEI123APPLE', 'NASDAQ'),

(1002, 'UIT-0002-XYZ', 'Global Capital', 'BOOK2', 'T456',
 'TSLA', 'Tesla Inc.', 'EQUITY',
 'SELL', '2025-06-02', '2025-06-05', 50, 220.40,
 'USD', 'USD',
 'SETTLED', 'Trade System', FALSE, 'LEI456TESLA', 'NASDAQ'),

(1003, 'UIT-0003-DEF', 'Prime Dealer', 'BOOK3', 'T789',
 'MSFT', 'Microsoft Corp.', 'EQUITY',
 'BUY', '2025-06-03', '2025-06-06', 75, 310.00,
 'USD', 'USD',
 'CONFIRMED', 'Trade System', TRUE, 'LEI789MSFT', 'NASDAQ');
 