# AssetSphere Pro

A premium **IT Asset & Infrastructure Management System** built as a portfolio project for Software Developer / IT Support roles.

## Highlights
- Role-based login: Admin, Technician, Viewer
- IT asset CRUD and lifecycle tracking
- Assignment, department, location and status management
- Maintenance/service history per asset
- Dashboard KPIs and category distribution
- Search and multi-filter asset registry
- CSV export
- Audit activity log
- Responsive premium UI
- SQLite database with seeded demo data

## Tech Stack
- Python 3
- Flask
- SQLite
- HTML5 / CSS3 / Vanilla JavaScript
- Werkzeug password hashing

## Run locally
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```
Open: http://127.0.0.1:5001

## Demo Accounts
| Role | Email | Password |
|---|---|---|
| Admin | admin@demo.com | Admin@123 |
| Technician | tech@demo.com | Tech@123 |
| Viewer | viewer@demo.com | View@123 |

## Role Permissions
- **Admin:** create, edit, assign/reassign, delete assets, add maintenance records, and export inventory
- **Technician:** view asset details and add service/maintenance records; cannot create, edit, assign/reassign, or delete assets
- **Viewer:** read-only asset visibility and export

## Resume-ready project description
**AssetSphere Pro — IT Asset & Infrastructure Management System**  
Developed a role-based full-stack web application using Flask and SQLite to manage enterprise IT assets, ownership, lifecycle status, maintenance history and audit activity. Implemented secure authentication, CRUD workflows, searchable inventory, dashboard analytics, CSV export and responsive UI for Admin, Technician and Viewer roles.

## Suggested resume bullets
- Built a Flask + SQLite IT asset management platform with secure role-based authentication and complete CRUD workflows.
- Designed asset assignment, maintenance logging, audit tracking, analytics and CSV export features for IT operations.
- Created a responsive premium dashboard using custom HTML/CSS/JavaScript, with separate permissions for Admin, Technician and Viewer roles.

## GitHub topics
`flask` `python` `sqlite` `it-asset-management` `full-stack` `inventory-management` `role-based-access-control` `portfolio-project`


## RBAC v2.1 permissions

- **Admin**: create, edit, assign/reassign, delete assets; add maintenance; export CSV; view audit log.
- **Technician**: view assets and add maintenance/service records only. Cannot create, edit, assign/reassign, or delete assets.
- **Viewer**: read-only dashboard, registry, asset details, and audit visibility. Cannot change asset or maintenance data.

### Clean-build verification
This v2.1 package uses `assetsphere_v21.db` and port `5001`, so it does not reuse the previous `assetsphere.db` or the old port-5000 development server. After first launch, the dashboard should begin with the seeded 8 assets. The top bar shows **v2.1 RBAC**.


## GitHub-ready notes
- The SQLite database is generated automatically on first run and is excluded from Git via `.gitignore`.
- Set `SECRET_KEY` as an environment variable before any public deployment.
- Set `FLASK_DEBUG=1` only for local development when debug mode is needed.
- Demo accounts are intended for local portfolio demonstration only.
