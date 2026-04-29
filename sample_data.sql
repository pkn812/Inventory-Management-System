-- ============================================================
-- PROJECT 07: INVENTORY MANAGEMENT SYSTEM
-- sample_data.sql — Sample Data (5-10 records per table)
-- Run AFTER schema.sql
-- ============================================================

USE inventory_db;

-- -------------------------------------------------------
-- Suppliers  (7 records)
-- -------------------------------------------------------
INSERT INTO Suppliers (SupplierName, Address, PhoneNumber) VALUES
('Tech Supplies Co.',    '123 Industrial Ave, Hanoi',      '024-3456-7890'),
('Global Parts Ltd.',    '456 Commerce St, Ho Chi Minh',   '028-9876-5432'),
('VN Electronics',       '789 Market Rd, Da Nang',         '023-6543-2109'),
('Fast Delivery Corp.',  '321 Logistics Blvd, Hai Phong',  '022-1234-5678'),
('Prime Materials Inc.', '654 Trade Center, Can Tho',      '029-8765-4321'),
('Alpha Wholesale',      '12 Enterprise Zone, Hue',        '023-3344-5566'),
('Omega Distributors',   '88 Harbor Road, Vung Tau',       '025-7788-9900');

-- -------------------------------------------------------
-- Products  (10 records)
-- -------------------------------------------------------
INSERT INTO Products (ProductName, Description, UnitPrice, SupplierID) VALUES
('Laptop Dell Inspiron 15', 'Intel i5-1235U, 8GB RAM, 256GB SSD',   15000000.00, 1),
('USB-C Hub 7-in-1',        '4K HDMI, 3× USB 3.0, SD Card reader',    450000.00, 1),
('Wireless Mouse',          'Ergonomic 2.4 GHz, 12-month battery',     200000.00, 2),
('Mechanical Keyboard TKL', 'Brown switches, tenkeyless, RGB backlit', 850000.00, 2),
('24-inch IPS Monitor',     '1920×1080, 75 Hz, HDMI + VGA ports',    3200000.00, 3),
('8-Port Gigabit Switch',   'Unmanaged, plug-and-play, metal case',    650000.00, 3),
('External SSD 1 TB',       'USB 3.2 Gen2, 1050 MB/s read speed',    1800000.00, 4),
('Full HD Webcam 1080p',    'Autofocus, built-in microphone, USB-A',   380000.00, 5),
('Surge Protector 6-out',   '2500 J, 6 outlets, 2 m cable',           220000.00, 6),
('Ethernet Cable Cat6 5m',  'Flat design, RJ45 connectors, shielded',   45000.00, 7);

-- -------------------------------------------------------
-- Warehouses  (5 records)
-- -------------------------------------------------------
INSERT INTO Warehouses (WarehouseName, Address, Capacity) VALUES
('Hanoi Main Warehouse',  'Km 5 Highway 1A, Dong Anh, Hanoi',         5000),
('HCMC South Warehouse',  '23 Industrial Zone, Binh Chanh, HCMC',     8000),
('Da Nang Central Store', '15 Port Road, Son Tra, Da Nang',            3000),
('Hai Phong Depot',       '7 Dock Street, Le Chan, Hai Phong',         4000),
('Can Tho Regional Hub',  '100 Mekong Boulevard, Ninh Kieu, Can Tho', 2500);

-- -------------------------------------------------------
-- StockEntries  (12 records)
-- NOTE: The trigger trg_AfterStockEntryInsert will automatically
--       insert the corresponding IN records into InventoryHistory.
-- -------------------------------------------------------
INSERT INTO StockEntries (ProductID, WarehouseID, Quantity, EntryDate) VALUES
-- Hanoi Main Warehouse
(1,  1,  50, '2024-01-10'),
(2,  1, 200, '2024-01-11'),
(3,  1, 150, '2024-01-15'),
-- HCMC South Warehouse
(4,  2, 150, '2024-01-16'),
(5,  2,  80, '2024-01-18'),
(6,  2, 120, '2024-02-01'),
-- Da Nang Central Store
(7,  3,  60, '2024-02-05'),
(8,  3, 250, '2024-02-08'),
-- Hai Phong Depot
(9,  4, 400, '2024-02-10'),
(10, 4, 500, '2024-02-12'),
-- Can Tho Regional Hub
(1,  5,  30, '2024-03-01'),
(3,  5, 100, '2024-03-05');

-- -------------------------------------------------------
-- InventoryHistory — OUT transactions  (8 manual records)
-- IN records above were auto-inserted by trigger.
-- -------------------------------------------------------
INSERT INTO InventoryHistory
    (ProductID, WarehouseID, Quantity, TransactionType, TransactionDate)
VALUES
(1,  1,   5, 'OUT', '2024-02-01 09:00:00'),
(2,  1,  20, 'OUT', '2024-02-03 10:30:00'),
(3,  1,  50, 'OUT', '2024-02-10 14:00:00'),
(4,  2,  30, 'OUT', '2024-02-15 16:00:00'),
(5,  2,  10, 'OUT', '2024-02-20 11:00:00'),
(7,  3,   8, 'OUT', '2024-03-01 09:00:00'),
(9,  4, 100, 'OUT', '2024-03-05 13:00:00'),
(10, 4, 200, 'OUT', '2024-03-08 15:30:00');

-- -------------------------------------------------------
-- Quick verification queries
-- -------------------------------------------------------
SELECT 'Suppliers'       AS TableName, COUNT(*) AS RecordCount FROM Suppliers
UNION ALL
SELECT 'Products',        COUNT(*) FROM Products
UNION ALL
SELECT 'Warehouses',      COUNT(*) FROM Warehouses
UNION ALL
SELECT 'StockEntries',    COUNT(*) FROM StockEntries
UNION ALL
SELECT 'InventoryHistory',COUNT(*) FROM InventoryHistory;

-- Preview stock levels (uses the view created in schema.sql)
SELECT * FROM vw_StockLevelPerWarehouse ORDER BY WarehouseID, ProductID;

-- Low-stock check
SELECT * FROM vw_LowStockAlert;
