INSERT INTO trade (
    trader_id, symbol, cusip, side, trade_date, settle_date,
    quantity, price, trade_currency, settlement_currency,
    book_name, uitid
) VALUES
('T123', 'AAPL', '037833100', 'BUY', '2025-06-01', '2025-06-03', 100, 180.25, 'USD', 'USD', 'BOOK1', 'UIT-0001-ABC'),
('T456', 'TSLA', '88160R101', 'SELL', '2025-06-02', '2025-06-05', -15, 220.40, 'USD', 'USD', 'BOOK2', 'UIT-0002-XYZ'),
('T789', 'MSFT', '594918104', 'BUY', '2025-06-03', '2025-06-06', 75, 310.00, 'USD', 'USD', 'BOOK3', 'UIT-0003-DEF');

