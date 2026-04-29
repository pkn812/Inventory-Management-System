-- ============================================================
-- PROJECT 07: INVENTORY MANAGEMENT SYSTEM
-- schema.sql — Database Schema
-- DATCOM Lab, NEU College of Technology
-- ============================================================

CREATE DATABASE IF NOT EXISTS inventory_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE inventory_db;

-- -------------------------------------------------------
-- TABLE: Suppliers
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS Suppliers (
    SupplierID   INT          AUTO_INCREMENT PRIMARY KEY,
    SupplierName VARCHAR(100) NOT NULL,
    Address      VARCHAR(255),
    PhoneNumber  VARCHAR(20)
);

-- -------------------------------------------------------
-- TABLE: Products
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS Products (
    ProductID   INT             AUTO_INCREMENT PRIMARY KEY,
    ProductName VARCHAR(100)    NOT NULL,
    Description TEXT,
    UnitPrice   DECIMAL(15,2)   NOT NULL CHECK (UnitPrice >= 0),
    SupplierID  INT,
    CONSTRAINT fk_product_supplier
        FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- TABLE: Warehouses
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS Warehouses (
    WarehouseID   INT          AUTO_INCREMENT PRIMARY KEY,
    WarehouseName VARCHAR(100) NOT NULL,
    Address       VARCHAR(255),
    Capacity      INT          DEFAULT 0 CHECK (Capacity >= 0)
);

-- -------------------------------------------------------
-- TABLE: StockEntries  (purchase orders / goods received)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS StockEntries (
    EntryID     INT  AUTO_INCREMENT PRIMARY KEY,
    ProductID   INT  NOT NULL,
    WarehouseID INT  NOT NULL,
    Quantity    INT  NOT NULL CHECK (Quantity > 0),
    EntryDate   DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_entry_product
        FOREIGN KEY (ProductID)   REFERENCES Products(ProductID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_entry_warehouse
        FOREIGN KEY (WarehouseID) REFERENCES Warehouses(WarehouseID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- -------------------------------------------------------
-- TABLE: InventoryHistory  (all IN/OUT movements)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS InventoryHistory (
    HistoryID       INT                  AUTO_INCREMENT PRIMARY KEY,
    ProductID       INT                  NOT NULL,
    WarehouseID     INT                  NOT NULL,
    Quantity        INT                  NOT NULL CHECK (Quantity > 0),
    TransactionType ENUM('IN', 'OUT')    NOT NULL DEFAULT 'IN',
    TransactionDate DATETIME             NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hist_product
        FOREIGN KEY (ProductID)   REFERENCES Products(ProductID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_hist_warehouse
        FOREIGN KEY (WarehouseID) REFERENCES Warehouses(WarehouseID)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_products_name      ON Products(ProductName);
CREATE INDEX idx_history_warehouse  ON InventoryHistory(WarehouseID);
CREATE INDEX idx_history_product    ON InventoryHistory(ProductID);
CREATE INDEX idx_history_txdate     ON InventoryHistory(TransactionDate);
CREATE INDEX idx_entries_date       ON StockEntries(EntryDate);
CREATE INDEX idx_entries_product    ON StockEntries(ProductID);

-- ============================================================
-- VIEWS
-- ============================================================

-- View: Current stock per product per warehouse
CREATE OR REPLACE VIEW vw_StockLevelPerWarehouse AS
SELECT
    w.WarehouseID,
    w.WarehouseName,
    p.ProductID,
    p.ProductName,
    SUM(CASE WHEN ih.TransactionType = 'IN'  THEN ih.Quantity ELSE 0 END) -
    SUM(CASE WHEN ih.TransactionType = 'OUT' THEN ih.Quantity ELSE 0 END) AS CurrentStock
FROM InventoryHistory ih
JOIN Products   p ON ih.ProductID   = p.ProductID
JOIN Warehouses w ON ih.WarehouseID = w.WarehouseID
GROUP BY w.WarehouseID, w.WarehouseName, p.ProductID, p.ProductName;

-- View: Supplier delivery history
CREATE OR REPLACE VIEW vw_SupplierDeliveryHistory AS
SELECT
    s.SupplierID,
    s.SupplierName,
    p.ProductID,
    p.ProductName,
    se.EntryID,
    se.Quantity,
    se.EntryDate,
    w.WarehouseName
FROM StockEntries se
JOIN Products   p ON se.ProductID   = p.ProductID
JOIN Suppliers  s ON p.SupplierID   = s.SupplierID
JOIN Warehouses w ON se.WarehouseID = w.WarehouseID
ORDER BY se.EntryDate DESC;

-- View: Low-stock alert (products with fewer than 10 units)
CREATE OR REPLACE VIEW vw_LowStockAlert AS
SELECT *
FROM vw_StockLevelPerWarehouse
WHERE CurrentStock < 10;

-- View: Total stock value per warehouse
CREATE OR REPLACE VIEW vw_StockValuePerWarehouse AS
SELECT
    v.WarehouseID,
    v.WarehouseName,
    SUM(v.CurrentStock * p.UnitPrice) AS TotalStockValue
FROM vw_StockLevelPerWarehouse v
JOIN Products p ON v.ProductID = p.ProductID
GROUP BY v.WarehouseID, v.WarehouseName;

-- ============================================================
-- STORED PROCEDURES
-- ============================================================
DELIMITER $$

-- Procedure: Restock a product (insert a StockEntry; trigger handles history)
CREATE PROCEDURE sp_RestockProduct(
    IN p_ProductID   INT,
    IN p_WarehouseID INT,
    IN p_Quantity    INT
)
BEGIN
    IF p_Quantity <= 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Quantity must be greater than zero.';
    END IF;
    INSERT INTO StockEntries (ProductID, WarehouseID, Quantity, EntryDate)
    VALUES (p_ProductID, p_WarehouseID, p_Quantity, CURDATE());
    SELECT LAST_INSERT_ID() AS NewEntryID;
END$$

-- Procedure: Get inventory balance for a product in a warehouse
CREATE PROCEDURE sp_GetInventoryBalance(
    IN p_ProductID   INT,
    IN p_WarehouseID INT
)
BEGIN
    SELECT
        p.ProductID,
        p.ProductName,
        w.WarehouseID,
        w.WarehouseName,
        SUM(CASE WHEN ih.TransactionType = 'IN'  THEN ih.Quantity ELSE 0 END) AS TotalIn,
        SUM(CASE WHEN ih.TransactionType = 'OUT' THEN ih.Quantity ELSE 0 END) AS TotalOut,
        SUM(CASE WHEN ih.TransactionType = 'IN'  THEN ih.Quantity ELSE 0 END) -
        SUM(CASE WHEN ih.TransactionType = 'OUT' THEN ih.Quantity ELSE 0 END) AS Balance
    FROM InventoryHistory ih
    JOIN Products   p ON ih.ProductID   = p.ProductID
    JOIN Warehouses w ON ih.WarehouseID = w.WarehouseID
    WHERE ih.ProductID   = p_ProductID
      AND ih.WarehouseID = p_WarehouseID
    GROUP BY p.ProductID, p.ProductName, w.WarehouseID, w.WarehouseName;
END$$

-- Procedure: Generate full inventory snapshot report
CREATE PROCEDURE sp_InventoryReport()
BEGIN
    SELECT
        w.WarehouseName,
        p.ProductName,
        p.UnitPrice,
        v.CurrentStock,
        (v.CurrentStock * p.UnitPrice) AS StockValue
    FROM vw_StockLevelPerWarehouse v
    JOIN Products   p ON v.ProductID   = p.ProductID
    JOIN Warehouses w ON v.WarehouseID = w.WarehouseID
    ORDER BY w.WarehouseName, p.ProductName;
END$$

DELIMITER ;

-- ============================================================
-- USER DEFINED FUNCTIONS
-- ============================================================
DELIMITER $$

-- UDF: Stock turnover rate  =  TotalOut / AvgInventory
CREATE FUNCTION fn_StockTurnoverRate(
    p_ProductID   INT,
    p_WarehouseID INT
)
RETURNS DECIMAL(10, 4)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total_out  DECIMAL(15, 2) DEFAULT 0;
    DECLARE v_total_in   DECIMAL(15, 2) DEFAULT 0;
    DECLARE v_avg_stock  DECIMAL(15, 2) DEFAULT 0;

    SELECT
        SUM(CASE WHEN TransactionType = 'OUT' THEN Quantity ELSE 0 END),
        SUM(CASE WHEN TransactionType = 'IN'  THEN Quantity ELSE 0 END)
    INTO v_total_out, v_total_in
    FROM InventoryHistory
    WHERE ProductID = p_ProductID AND WarehouseID = p_WarehouseID;

    -- Average inventory = (opening + closing) / 2
    -- Approximation: (TotalIn + (TotalIn - TotalOut)) / 2
    SET v_avg_stock = (v_total_in + GREATEST(v_total_in - v_total_out, 0)) / 2;

    IF v_avg_stock = 0 THEN
        RETURN 0;
    END IF;

    RETURN ROUND(v_total_out / v_avg_stock, 4);
END$$

-- UDF: Average delivery interval (days) between consecutive deliveries per supplier
CREATE FUNCTION fn_AvgDeliveryTime(p_SupplierID INT)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_avg_days DECIMAL(10, 2) DEFAULT 0;

    SELECT AVG(DATEDIFF(se2.EntryDate, se1.EntryDate))
    INTO v_avg_days
    FROM StockEntries se1
    JOIN StockEntries se2
        ON  se1.ProductID  = se2.ProductID
        AND se2.EntryID    > se1.EntryID
    JOIN Products p ON se1.ProductID = p.ProductID
    WHERE p.SupplierID = p_SupplierID;

    RETURN IFNULL(v_avg_days, 0);
END$$

DELIMITER ;

-- ============================================================
-- TRIGGERS
-- ============================================================
DELIMITER $$

-- Trigger: After a new StockEntry, auto-add an IN record to InventoryHistory
CREATE TRIGGER trg_AfterStockEntryInsert
AFTER INSERT ON StockEntries
FOR EACH ROW
BEGIN
    INSERT INTO InventoryHistory
        (ProductID, WarehouseID, Quantity, TransactionType, TransactionDate)
    VALUES
        (NEW.ProductID, NEW.WarehouseID, NEW.Quantity, 'IN', NOW());
END$$

-- Trigger: Prevent negative inventory on OUT transactions
CREATE TRIGGER trg_BeforeInventoryHistoryInsert
BEFORE INSERT ON InventoryHistory
FOR EACH ROW
BEGIN
    DECLARE v_balance INT DEFAULT 0;

    IF NEW.TransactionType = 'OUT' THEN
        SELECT
            COALESCE(SUM(CASE WHEN TransactionType = 'IN'  THEN Quantity ELSE 0 END) -
                     SUM(CASE WHEN TransactionType = 'OUT' THEN Quantity ELSE 0 END), 0)
        INTO v_balance
        FROM InventoryHistory
        WHERE ProductID = NEW.ProductID AND WarehouseID = NEW.WarehouseID;

        IF v_balance < NEW.Quantity THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Insufficient stock: OUT quantity exceeds current balance.';
        END IF;
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- USER ROLES AND SECURITY
-- ============================================================

-- Admin user: full privileges
CREATE USER IF NOT EXISTS 'inv_admin'@'localhost'   IDENTIFIED BY 'Admin@Inv2024!';
-- Inventory manager: limited write access
CREATE USER IF NOT EXISTS 'inv_manager'@'localhost' IDENTIFIED BY 'Mgr@Inv2024!';
-- Read-only reporter
CREATE USER IF NOT EXISTS 'inv_reporter'@'localhost' IDENTIFIED BY 'Rep@Inv2024!';

-- Admin: everything
GRANT ALL PRIVILEGES ON inventory_db.* TO 'inv_admin'@'localhost';

-- Manager: can add/update products, add stock entries, read all
GRANT SELECT, INSERT, UPDATE ON inventory_db.Products          TO 'inv_manager'@'localhost';
GRANT SELECT, INSERT         ON inventory_db.StockEntries       TO 'inv_manager'@'localhost';
GRANT SELECT, INSERT         ON inventory_db.InventoryHistory   TO 'inv_manager'@'localhost';
GRANT SELECT                 ON inventory_db.Warehouses         TO 'inv_manager'@'localhost';
GRANT SELECT                 ON inventory_db.Suppliers          TO 'inv_manager'@'localhost';
GRANT SELECT ON inventory_db.vw_StockLevelPerWarehouse   TO 'inv_manager'@'localhost';
GRANT SELECT ON inventory_db.vw_SupplierDeliveryHistory  TO 'inv_manager'@'localhost';
GRANT SELECT ON inventory_db.vw_LowStockAlert            TO 'inv_manager'@'localhost';
GRANT SELECT ON inventory_db.vw_StockValuePerWarehouse   TO 'inv_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE inventory_db.sp_RestockProduct     TO 'inv_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE inventory_db.sp_GetInventoryBalance TO 'inv_manager'@'localhost';

-- Reporter: read-only
GRANT SELECT ON inventory_db.* TO 'inv_reporter'@'localhost';

FLUSH PRIVILEGES;
