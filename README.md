# Project 07 — Inventory Management System
**DATCOM Lab | NEU College of Technology**

---

## Project Structure

```
inventory-management/
├── schema.sql       # Database schema (tables, indexes, views, SPs, UDFs, triggers, roles)
├── sample_data.sql  # Sample data (5-10 records per table)
├── app.py           # Python CLI application
└── README.md        # This file
```

---

## Requirements

| Tool | Version |
|------|---------|
| MySQL | 8.0+ |
| Python | 3.8+ |
| mysql-connector-python | latest |

Install the Python driver:
```bash
pip install mysql-connector-python
```

---

## Database Setup

### Step 1 — Run the schema

```bash
mysql -u root -p < schema.sql
```

### Step 2 — Load sample data

```bash
mysql -u root -p < sample_data.sql
```

### Step 3 — Verify

```sql
USE inventory_db;
SELECT * FROM vw_StockLevelPerWarehouse;
SELECT * FROM vw_LowStockAlert;
```

---

## Running the Application

1. Open `app.py` and update **DB_CONFIG**:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",           # or 'inv_admin' / 'inv_manager'
    "password": "your_password",  # <-- your MySQL password
    "database": "inventory_db",
}
```

2. Run:

```bash
python app.py
```

---

## Application Menu

| # | Feature | Description |
|---|---------|-------------|
| 1 | Add Product | Insert a new product with supplier link |
| 2 | Update Product | Edit name, price, or description |
| 3 | List Products | View all products with supplier info |
| 4 | Delete Product | Remove a product (cascades to history) |
| 5 | Add Supplier | Register a new supplier |
| 6 | List Suppliers | View all suppliers |
| 7 | Add Warehouse | Register a new warehouse |
| 8 | List Warehouses | View all warehouses |
| 9 | Add Stock Entry | Record goods received (IN) — trigger auto-updates InventoryHistory |
| 10 | Record Stock Out | Record goods dispatched (OUT) — trigger validates stock |
| 11 | Restock via Procedure | Uses `sp_RestockProduct` stored procedure |
| 12 | Inventory Balance | Uses `sp_GetInventoryBalance` stored procedure |
| 13 | Stock Level Report | Shows current stock per warehouse using `vw_StockLevelPerWarehouse` |
| 14 | Low Stock Alerts | Shows products < 10 units using `vw_LowStockAlert` |
| 15 | Inventory History | Shows last 50 IN/OUT movements |
| 16 | Supplier Deliveries | Uses `vw_SupplierDeliveryHistory` |
| 17 | Full Inventory Report | Uses `sp_InventoryReport` with total stock values |
| 18 | Stock Turnover Rate | Calls `fn_StockTurnoverRate(productID, warehouseID)` |
| 19 | Average Delivery Time | Calls `fn_AvgDeliveryTime(supplierID)` |

---

## Database Objects Summary

### Tables
| Table | PK | Key Relationships |
|-------|----|------------------|
| Suppliers | SupplierID | — |
| Products | ProductID | FK → Suppliers |
| Warehouses | WarehouseID | — |
| StockEntries | EntryID | FK → Products, Warehouses |
| InventoryHistory | HistoryID | FK → Products, Warehouses |

### Indexes
- `idx_products_name` — fast search by product name
- `idx_history_warehouse` — fast filtering by warehouse
- `idx_history_product` — fast filtering by product
- `idx_history_txdate` — fast date-range queries
- `idx_entries_date` — fast delivery date queries

### Views
- `vw_StockLevelPerWarehouse` — current balance per product/warehouse
- `vw_LowStockAlert` — products with stock < 10
- `vw_SupplierDeliveryHistory` — all deliveries per supplier
- `vw_StockValuePerWarehouse` — total VND value per warehouse

### Stored Procedures
- `sp_RestockProduct(productID, warehouseID, quantity)`
- `sp_GetInventoryBalance(productID, warehouseID)`
- `sp_InventoryReport()`

### User Defined Functions
- `fn_StockTurnoverRate(productID, warehouseID)` → DECIMAL
- `fn_AvgDeliveryTime(supplierID)` → DECIMAL (days)

### Triggers
- `trg_AfterStockEntryInsert` — auto-inserts IN record into InventoryHistory on StockEntry
- `trg_BeforeInventoryHistoryInsert` — prevents OUT quantity exceeding current balance

### User Roles
| User | Permissions |
|------|-------------|
| `inv_admin` | ALL PRIVILEGES |
| `inv_manager` | SELECT/INSERT/UPDATE on main tables + EXECUTE procedures |
| `inv_reporter` | SELECT only |

---

## Backup & Recovery

```bash
# Backup
mysqldump -u root -p inventory_db > backup_$(date +%F).sql

# Restore
mysql -u root -p inventory_db < backup_2024-01-01.sql
```

---

## Future Enhancements

- **Barcode scanning** — integrate a USB/Bluetooth scanner to auto-fill ProductID on stock entries
- **ERP integration** — expose a REST API (Flask/FastAPI) to connect with SAP or Odoo
- **Predictive restocking** — use moving average of OUT transactions to forecast reorder points
- **GUI** — Tkinter or a web dashboard (Streamlit / Flask + Bootstrap)
- **Audit log** — additional trigger to track who changed what and when

---

## References

- MySQL 8.0 Documentation: https://dev.mysql.com/doc/refman/8.0/en/
- mysql-connector-python: https://pypi.org/project/mysql-connector-python/
- NEU DATCOM Lab Project Brief (PDF attached to report)
