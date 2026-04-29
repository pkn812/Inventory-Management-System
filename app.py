"""
=============================================================
 PROJECT 07 — INVENTORY MANAGEMENT SYSTEM
 app.py — Command-line Interface
 DATCOM Lab, NEU College of Technology
=============================================================
 Requirements:
   pip install mysql-connector-python
 Usage:
   python app.py
 Configure DB_CONFIG below before running.
=============================================================
"""

import os
import sys
from datetime import date

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("[ERROR] mysql-connector-python is not installed.")
    print("  Run: pip install mysql-connector-python")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────
# DATABASE CONFIGURATION — edit these values
# ─────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",           # or 'inv_admin' / 'inv_manager'
    "password": "Pkn2006@",  # <-- change this
    "database": "inventory_db",
    "charset":  "utf8mb4",
}

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def get_connection():
    """Return a live MySQL connection or None on failure."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as exc:
        print(f"\n[DB ERROR] {exc}")
        return None


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def divider(char="─", width=80):
    print(char * width)


def prompt_int(label: str):
    """Prompt until an integer is entered."""
    while True:
        raw = input(label).strip()
        if raw.lstrip("-").isdigit():
            return int(raw)
        print("  [!] Please enter a valid integer.")


def prompt_float(label: str):
    while True:
        raw = input(label).strip()
        try:
            return float(raw)
        except ValueError:
            print("  [!] Please enter a valid number.")


def prompt_date(label: str, default_today: bool = True) -> str:
    hint = " (YYYY-MM-DD, blank = today)" if default_today else " (YYYY-MM-DD)"
    while True:
        raw = input(f"{label}{hint}: ").strip()
        if not raw and default_today:
            return str(date.today())
        try:
            d = date.fromisoformat(raw)
            return str(d)
        except ValueError:
            print("  [!] Invalid date format. Use YYYY-MM-DD.")


# ─────────────────────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────────────────────
def add_product():
    divider()
    print("  ADD NEW PRODUCT")
    divider()
    name   = input("  Product Name   : ").strip()
    desc   = input("  Description    : ").strip()
    price  = prompt_float("  Unit Price (VND): ")
    sup_id = prompt_int("  Supplier ID    : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Products (ProductName, Description, UnitPrice, SupplierID) "
            "VALUES (%s, %s, %s, %s)",
            (name, desc, price, sup_id),
        )
        conn.commit()
        print(f"\n  [OK] Product '{name}' added with ID = {cur.lastrowid}.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def update_product():
    divider()
    print("  UPDATE PRODUCT")
    divider()
    pid = prompt_int("  Product ID to update : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM Products WHERE ProductID = %s", (pid,))
        row = cur.fetchone()
        if not row:
            print(f"\n  [!] No product found with ID {pid}.")
            return

        print(f"\n  Current: {row['ProductName']}  |  Price: {row['UnitPrice']:,.0f}")
        name  = input("  New Name  (blank = keep): ").strip()
        price = input("  New Price (blank = keep): ").strip()
        desc  = input("  New Desc  (blank = keep): ").strip()

        updates, params = [], []
        if name:  updates.append("ProductName=%s");  params.append(name)
        if price: updates.append("UnitPrice=%s");    params.append(float(price))
        if desc:  updates.append("Description=%s");  params.append(desc)

        if not updates:
            print("\n  [!] Nothing to update.")
            return

        params.append(pid)
        cur.execute(f"UPDATE Products SET {', '.join(updates)} WHERE ProductID=%s", params)
        conn.commit()
        print(f"\n  [OK] Product ID {pid} updated.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def list_products():
    divider()
    print("  PRODUCT LIST")
    divider()
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT p.ProductID, p.ProductName, p.UnitPrice, "
            "       IFNULL(s.SupplierName, 'N/A') "
            "FROM Products p "
            "LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID "
            "ORDER BY p.ProductID"
        )
        rows = cur.fetchall()
        if not rows:
            print("  (no products found)")
            return
        fmt = "  {:<5} {:<32} {:>16} {:<28}"
        print(fmt.format("ID", "Product Name", "Unit Price (VND)", "Supplier"))
        divider("-")
        for r in rows:
            print(fmt.format(r[0], r[1][:32], f"{r[2]:,.0f}", r[3][:28]))
        print(f"\n  Total: {len(rows)} product(s).")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def delete_product():
    divider()
    print("  DELETE PRODUCT")
    divider()
    pid = prompt_int("  Product ID to delete : ")
    confirm = input(f"  Are you sure you want to delete Product ID {pid}? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  Cancelled.")
        return
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM Products WHERE ProductID = %s", (pid,))
        conn.commit()
        if cur.rowcount:
            print(f"\n  [OK] Product ID {pid} deleted.")
        else:
            print(f"\n  [!] No product found with ID {pid}.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# SUPPLIERS
# ─────────────────────────────────────────────────────────────
def add_supplier():
    divider()
    print("  ADD NEW SUPPLIER")
    divider()
    name  = input("  Supplier Name : ").strip()
    addr  = input("  Address       : ").strip()
    phone = input("  Phone Number  : ").strip()

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Suppliers (SupplierName, Address, PhoneNumber) VALUES (%s, %s, %s)",
            (name, addr, phone),
        )
        conn.commit()
        print(f"\n  [OK] Supplier '{name}' added with ID = {cur.lastrowid}.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def list_suppliers():
    divider()
    print("  SUPPLIER LIST")
    divider()
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT SupplierID, SupplierName, Address, PhoneNumber "
            "FROM Suppliers ORDER BY SupplierID"
        )
        rows = cur.fetchall()
        if not rows:
            print("  (no suppliers found)")
            return
        fmt = "  {:<5} {:<28} {:<38} {:<18}"
        print(fmt.format("ID", "Supplier Name", "Address", "Phone"))
        divider("-")
        for r in rows:
            print(fmt.format(r[0], r[1][:28], (r[2] or "")[:38], (r[3] or "")[:18]))
        print(f"\n  Total: {len(rows)} supplier(s).")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# WAREHOUSES
# ─────────────────────────────────────────────────────────────
def add_warehouse():
    divider()
    print("  ADD NEW WAREHOUSE")
    divider()
    name = input("  Warehouse Name : ").strip()
    addr = input("  Address        : ").strip()
    cap  = prompt_int("  Capacity       : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Warehouses (WarehouseName, Address, Capacity) VALUES (%s, %s, %s)",
            (name, addr, cap),
        )
        conn.commit()
        print(f"\n  [OK] Warehouse '{name}' added with ID = {cur.lastrowid}.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def list_warehouses():
    divider()
    print("  WAREHOUSE LIST")
    divider()
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT WarehouseID, WarehouseName, Address, Capacity "
            "FROM Warehouses ORDER BY WarehouseID"
        )
        rows = cur.fetchall()
        if not rows:
            print("  (no warehouses found)")
            return
        fmt = "  {:<5} {:<28} {:<42} {:>10}"
        print(fmt.format("ID", "Warehouse Name", "Address", "Capacity"))
        divider("-")
        for r in rows:
            print(fmt.format(r[0], r[1][:28], (r[2] or "")[:42], r[3]))
        print(f"\n  Total: {len(rows)} warehouse(s).")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# STOCK MANAGEMENT
# ─────────────────────────────────────────────────────────────
def add_stock_entry():
    divider()
    print("  ADD STOCK ENTRY  (goods received)")
    divider()
    pid = prompt_int("  Product ID   : ")
    wid = prompt_int("  Warehouse ID : ")
    qty = prompt_int("  Quantity     : ")
    dt  = prompt_date("  Entry Date")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO StockEntries (ProductID, WarehouseID, Quantity, EntryDate) "
            "VALUES (%s, %s, %s, %s)",
            (pid, wid, qty, dt),
        )
        conn.commit()
        print(
            f"\n  [OK] Stock entry added (ID={cur.lastrowid}). "
            "InventoryHistory updated automatically by trigger."
        )
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def record_stock_out():
    divider()
    print("  RECORD STOCK OUT  (goods dispatched)")
    divider()
    pid = prompt_int("  Product ID   : ")
    wid = prompt_int("  Warehouse ID : ")
    qty = prompt_int("  Quantity OUT : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO InventoryHistory "
            "(ProductID, WarehouseID, Quantity, TransactionType) "
            "VALUES (%s, %s, %s, 'OUT')",
            (pid, wid, qty),
        )
        conn.commit()
        print("\n  [OK] OUT transaction recorded in InventoryHistory.")
    except Error as exc:
        # Catch the trigger's insufficient-stock signal
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def restock_via_procedure():
    divider()
    print("  RESTOCK PRODUCT  (via stored procedure)")
    divider()
    pid = prompt_int("  Product ID   : ")
    wid = prompt_int("  Warehouse ID : ")
    qty = prompt_int("  Quantity     : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.callproc("sp_RestockProduct", [pid, wid, qty])
        conn.commit()
        for result in cur.stored_results():
            row = result.fetchone()
            if row:
                print(f"\n  [OK] Restock complete. New StockEntry ID = {row[0]}.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def get_inventory_balance():
    divider()
    print("  INVENTORY BALANCE  (via stored procedure)")
    divider()
    pid = prompt_int("  Product ID   : ")
    wid = prompt_int("  Warehouse ID : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.callproc("sp_GetInventoryBalance", [pid, wid])
        for result in cur.stored_results():
            rows = result.fetchall()
            if not rows:
                print("\n  [!] No data found for that product/warehouse combination.")
                return
            cols = result.column_names
            for row in rows:
                print()
                for col, val in zip(cols, row):
                    print(f"  {col:<18}: {val}")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────────────────────
def report_stock_levels():
    divider()
    print("  STOCK LEVEL REPORT  (per Warehouse / Product)")
    divider()
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT WarehouseID, WarehouseName, ProductID, ProductName, CurrentStock "
            "FROM vw_StockLevelPerWarehouse "
            "ORDER BY WarehouseID, ProductID"
        )
        rows = cur.fetchall()
        if not rows:
            print("  (no inventory data)")
            return
        fmt = "  {:<6} {:<26} {:<7} {:<30} {:>10}"
        print(fmt.format("WH ID", "Warehouse", "PID", "Product", "Stock"))
        divider("-")
        for r in rows:
            print(fmt.format(r[0], r[1][:26], r[2], r[3][:30], r[4]))
        print(f"\n  {len(rows)} line(s) displayed.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def report_low_stock():
    divider()
    print("  LOW STOCK ALERTS  (< 10 units)")
    divider()
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT WarehouseID, WarehouseName, ProductID, ProductName, CurrentStock "
            "FROM vw_LowStockAlert ORDER BY CurrentStock ASC"
        )
        rows = cur.fetchall()
        if not rows:
            print("  ✓  All products are adequately stocked.")
            return
        fmt = "  {:<6} {:<26} {:<7} {:<30} {:>8}  {}"
        print(fmt.format("WH ID", "Warehouse", "PID", "Product", "Stock", "Status"))
        divider("-")
        for r in rows:
            status = "🔴 OUT OF STOCK" if r[4] <= 0 else "🟡 LOW"
            print(fmt.format(r[0], r[1][:26], r[2], r[3][:30], r[4], status))
        print(f"\n  ⚠  {len(rows)} alert(s) found.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def report_inventory_history():
    divider()
    print("  INVENTORY HISTORY  (last 50 records)")
    divider()
    pid_raw = input("  Filter by Product ID (blank = all): ").strip()

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        base_sql = (
            "SELECT ih.HistoryID, p.ProductName, w.WarehouseName, "
            "       ih.Quantity, ih.TransactionType, ih.TransactionDate "
            "FROM InventoryHistory ih "
            "JOIN Products   p ON ih.ProductID   = p.ProductID "
            "JOIN Warehouses w ON ih.WarehouseID = w.WarehouseID "
        )
        if pid_raw.isdigit():
            cur.execute(base_sql + "WHERE ih.ProductID = %s ORDER BY ih.TransactionDate DESC LIMIT 50", (int(pid_raw),))
        else:
            cur.execute(base_sql + "ORDER BY ih.TransactionDate DESC LIMIT 50")

        rows = cur.fetchall()
        if not rows:
            print("  (no history records)")
            return
        fmt = "  {:<6} {:<28} {:<22} {:>6}  {:<5}  {}"
        print(fmt.format("H.ID", "Product", "Warehouse", "Qty", "Type", "Date"))
        divider("-")
        for r in rows:
            indicator = "↑ IN " if r[4] == "IN" else "↓ OUT"
            print(fmt.format(r[0], r[1][:28], r[2][:22], r[3], indicator, r[5]))
        print(f"\n  {len(rows)} record(s) shown.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def report_supplier_deliveries():
    divider()
    print("  SUPPLIER DELIVERY HISTORY")
    divider()
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT SupplierID, SupplierName, ProductID, ProductName, "
            "       EntryID, Quantity, EntryDate, WarehouseName "
            "FROM vw_SupplierDeliveryHistory LIMIT 50"
        )
        rows = cur.fetchall()
        if not rows:
            print("  (no delivery records)")
            return
        fmt = "  {:<6} {:<24} {:<7} {:<24} {:<8} {:>6}  {:<12}  {}"
        print(fmt.format("S.ID", "Supplier", "P.ID", "Product", "Entry", "Qty", "Date", "Warehouse"))
        divider("-")
        for r in rows:
            print(fmt.format(r[0], r[1][:24], r[2], r[3][:24], r[4], r[5], str(r[6]), r[7][:20]))
        print(f"\n  {len(rows)} delivery record(s) shown.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def report_full_inventory():
    divider()
    print("  FULL INVENTORY REPORT  (via stored procedure)")
    divider()
    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.callproc("sp_InventoryReport")
        for result in cur.stored_results():
            rows = result.fetchall()
            if not rows:
                print("  (no data)")
                return
            fmt = "  {:<26} {:<30} {:>16}  {:>8}  {:>18}"
            print(fmt.format("Warehouse", "Product", "Unit Price (VND)", "Stock", "Value (VND)"))
            divider("-")
            total_value = 0
            for r in rows:
                total_value += float(r[4])
                print(fmt.format(r[0][:26], r[1][:30], f"{r[2]:,.0f}", r[3], f"{r[4]:,.0f}"))
            divider("-")
            print(f"  {'TOTAL INVENTORY VALUE':>82}  {total_value:>18,.0f}")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# ADVANCED FEATURES (UDF / Stored Procedures)
# ─────────────────────────────────────────────────────────────
def show_turnover_rate():
    divider()
    print("  STOCK TURNOVER RATE  (UDF)")
    divider()
    pid = prompt_int("  Product ID   : ")
    wid = prompt_int("  Warehouse ID : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT fn_StockTurnoverRate(%s, %s)", (pid, wid))
        result = cur.fetchone()
        rate = result[0] if result[0] is not None else 0
        print(f"\n  Stock Turnover Rate: {rate:.4f}")
        if rate == 0:
            print("  (No transactions recorded or average stock is zero.)")
        elif rate < 1:
            print("  Interpretation: Slow-moving inventory.")
        elif rate < 3:
            print("  Interpretation: Moderate turnover.")
        else:
            print("  Interpretation: Fast-moving inventory — consider restocking soon.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


def show_avg_delivery_time():
    divider()
    print("  AVERAGE DELIVERY TIME  (UDF)")
    divider()
    sid = prompt_int("  Supplier ID : ")

    conn = get_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT fn_AvgDeliveryTime(%s)", (sid,))
        result = cur.fetchone()
        days = result[0] if result[0] is not None else 0
        print(f"\n  Average delivery interval: {days:.1f} day(s) between consecutive deliveries.")
    except Error as exc:
        print(f"\n  [ERROR] {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────────────────────
MENU = """\
╔══════════════════════════════════════════════════════════╗
║              INVENTORY MANAGEMENT SYSTEM                 ║
╠══════════════════════════════════════════════════════════╣
║  PRODUCTS                                                ║
║   1. Add Product          2. Update Product              ║
║   3. List Products        4. Delete Product              ║
╠══════════════════════════════════════════════════════════╣
║  SUPPLIERS                                               ║
║   5. Add Supplier         6. List Suppliers              ║
╠══════════════════════════════════════════════════════════╣
║  WAREHOUSES                                              ║
║   7. Add Warehouse        8. List Warehouses             ║
╠══════════════════════════════════════════════════════════╣
║  STOCK MANAGEMENT                                        ║
║   9.  Add Stock Entry (IN)   10. Record Stock Out        ║
║  11.  Restock via Procedure  12. Inventory Balance       ║
╠══════════════════════════════════════════════════════════╣
║  REPORTS                                                 ║
║  13. Stock Levels (by Warehouse)                         ║
║  14. Low Stock Alerts                                    ║
║  15. Inventory History                                   ║
║  16. Supplier Delivery History                           ║
║  17. Full Inventory Report (value)                       ║
╠══════════════════════════════════════════════════════════╣
║  ANALYTICS                                               ║
║  18. Stock Turnover Rate (UDF)                           ║
║  19. Average Delivery Time (UDF)                         ║
╠══════════════════════════════════════════════════════════╣
║   0. Exit                                                ║
╚══════════════════════════════════════════════════════════╝
"""

ACTIONS = {
    "1":  add_product,
    "2":  update_product,
    "3":  list_products,
    "4":  delete_product,
    "5":  add_supplier,
    "6":  list_suppliers,
    "7":  add_warehouse,
    "8":  list_warehouses,
    "9":  add_stock_entry,
    "10": record_stock_out,
    "11": restock_via_procedure,
    "12": get_inventory_balance,
    "13": report_stock_levels,
    "14": report_low_stock,
    "15": report_inventory_history,
    "16": report_supplier_deliveries,
    "17": report_full_inventory,
    "18": show_turnover_rate,
    "19": show_avg_delivery_time,
}


def main():
    clear_screen()
    print("  Connecting to MySQL database...")
    conn = get_connection()
    if not conn:
        print("\n  Please check DB_CONFIG settings in app.py and try again.")
        sys.exit(1)
    conn.close()
    print("  Connected successfully!\n")

    while True:
        print(MENU)
        try:
            choice = input("  Enter choice: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Goodbye!")
            break

        if choice == "0":
            print("  Goodbye!")
            break

        action = ACTIONS.get(choice)
        if action:
            print()
            action()
        else:
            print("\n  [!] Invalid choice. Please enter a number from the menu.")

        input("\n  Press Enter to continue...")
        clear_screen()


if __name__ == "__main__":
    main()
