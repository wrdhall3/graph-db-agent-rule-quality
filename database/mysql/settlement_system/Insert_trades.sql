INSERT INTO trade (
    counterparty_name, symbol, cusip, trade_date, settlement_date, side,
    quantity, price, trade_currency, settlement_currency, book_name,
    settlement_status, source_system, uitid, settlement_location
) VALUES
('ACME Broker', 'AAPL', '037833100', '2025-06-01', '2025-06-03', 'BUY', 100, 180.25, 'USD', 'USD', 'BOOK1', 'IN_PROCESS', 'Trade System', 'UIT-0001-ABC', 'NYC'),
('Global Capital', 'TSLA', '88160R101', '2025-06-02', '2025-06-05', 'SELL', 50, 220.40, 'USD', 'USD', 'BOOK2', 'SETTLED', 'Trade System', 'UIT-0002-XYZ', 'LON'),
('Prime Dealer', NULL, '594918104', '2025-06-03', '2025-06-06', 'BUY', 75, 310.00, 'USD', 'USD', 'BOOK3', 'NOT_STARTED', 'Trade System', 'UIT-0003-DEF', 'SGP');
