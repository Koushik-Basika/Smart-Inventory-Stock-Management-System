# Smart Inventory & Stock Management System

Intermediate Flask + MySQL full-stack project.

## Features
- Registration, login, logout and password hashing
- Staff/admin roles (new registrations default to staff)
- Dashboard metrics, low-stock alerts and Chart.js stock chart
- Product CRUD, categories and suppliers
- Stock-in and stock-out transactions with insufficient-stock validation
- Inventory and transaction reports
- JSON endpoint: `GET /api/products`
- CSRF protection on forms

## 1. Requirements
- Python 3.10+
- MySQL Server and MySQL Workbench (Workbench is optional)
- VS Code

## 2. Create database
Open MySQL Workbench and execute `schema.sql`. This creates `inventory_db`.
The Flask app also runs `db.create_all()` when started.

## 3. Create virtual environment
Windows PowerShell:
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 4. Configure database
Copy `.env.example` to `.env` and update the MySQL username/password:
```env
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost/inventory_db
```
If your MySQL password contains characters such as `@`, `#`, `/` or `:`, URL-encode them.

## 5. Run
```powershell
python app.py
```
Open http://127.0.0.1:5000

## 6. Create an admin account
Register through the website. New accounts are staff by default.
For local development only, promote your account in MySQL Workbench:
```sql
USE inventory_db;
UPDATE user SET role = 'admin' WHERE email = 'your-email@example.com';
```
Log out and log back in. Admin users can delete products that have no stock transaction history.

## Database relationships
- One category can have many products.
- One supplier can supply many products.
- One product can have many stock transactions.
- One user can create many stock transactions.

## Suggested test flow
1. Register, then promote your account to admin using the SQL above.
2. Log in and create categories and suppliers.
3. Add products with opening stock.
4. Record Stock In and Stock Out movements.
5. Try to stock out more than the available quantity; it should be rejected.
6. Set a product's reorder level above its current quantity to test low-stock alerts.
7. Review the dashboard and reports.

## Important production improvements
This is a learning project, not a production-hardened inventory platform. Before deployment:
- Replace the development secret key and disable Flask debug mode.
- Add admin-only user management and controlled staff onboarding.
- Add pagination, audit logging, database migrations (Flask-Migrate), backups and automated tests.
- Add server-side rate limiting and stronger password policy.
- For concurrent stock operations, use database transactions and row-level locking.
- Consider archiving products instead of deleting them.
