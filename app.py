from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import sqlite3
from pathlib import Path
from functools import wraps
from datetime import datetime
import csv, io, os
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'assetsphere_v21.db'

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'assetsphere-v21-dev-only-change-me')
app.config['SESSION_COOKIE_NAME'] = 'assetsphere_v21_session'
APP_VERSION = 'v2.1 RBAC'


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'technician'
    );

    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_tag TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        brand TEXT,
        model TEXT,
        serial_no TEXT,
        assigned_to TEXT,
        department TEXT,
        status TEXT NOT NULL DEFAULT 'Available',
        purchase_date TEXT,
        warranty_until TEXT,
        purchase_cost REAL DEFAULT 0,
        location TEXT,
        notes TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        service_date TEXT NOT NULL,
        service_type TEXT NOT NULL,
        vendor TEXT,
        cost REAL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'Completed',
        notes TEXT,
        created_by TEXT,
        FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL
    );
    ''')

    users = cur.execute('SELECT COUNT(*) c FROM users').fetchone()['c']
    if users == 0:
        cur.executemany('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)', [
            ('System Administrator','admin@demo.com',generate_password_hash('Admin@123'),'admin'),
            ('IT Technician','tech@demo.com',generate_password_hash('Tech@123'),'technician'),
            ('Audit Viewer','viewer@demo.com',generate_password_hash('View@123'),'viewer'),
        ])

    count = cur.execute('SELECT COUNT(*) c FROM assets').fetchone()['c']
    if count == 0:
        sample_assets = [
            ('AS-1001','Dell Latitude 5440','Laptop','Dell','Latitude 5440','DL5440-AX91','Arun Kumar','Finance','Assigned','2025-06-10','2028-06-10',74500,'Chennai HQ','Primary finance workstation'),
            ('AS-1002','MacBook Air M3','Laptop','Apple','MacBook Air M3','MBA-M3-7782','Priya S','Engineering','Assigned','2026-01-22','2027-01-22',112900,'Chennai HQ','Development machine'),
            ('AS-1003','HP ProDesk 400','Desktop','HP','ProDesk 400 G9','HPD-400-5210','','Operations','Available','2025-08-15','2028-08-15',58900,'IT Store','Ready for allocation'),
            ('AS-1004','Cisco CBS350 Switch','Network','Cisco','CBS350-24T-4G','CSW-90331','','Infrastructure','Active','2024-11-05','2027-11-05',41900,'Server Room','Core access switch'),
            ('AS-1005','Epson EcoTank L6270','Printer','Epson','L6270','EPS-6270-1102','Admin Desk','Administration','Maintenance','2024-07-19','2026-07-19',27990,'Chennai HQ','Paper feed issue under service'),
            ('AS-1006','Samsung 27-inch Monitor','Monitor','Samsung','S27C310','SAM27-50021','Vikram R','Engineering','Assigned','2025-09-12','2028-09-12',12999,'Chennai HQ','External display'),
            ('AS-1007','APC Smart UPS 1500VA','Power','APC','SMC1500I','APC-1500-2231','','Infrastructure','Active','2025-03-02','2027-03-02',32750,'Server Room','Rack UPS'),
            ('AS-1008','Lenovo ThinkPad E14','Laptop','Lenovo','ThinkPad E14 Gen 6','LNV-E14-0192','','Support','Available','2026-03-18','2029-03-18',68900,'IT Store','Spare support laptop'),
        ]
        cur.executemany('''INSERT INTO assets(asset_tag,name,category,brand,model,serial_no,assigned_to,department,status,purchase_date,warranty_until,purchase_cost,location,notes,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        [(*x, datetime.now().isoformat(timespec='seconds')) for x in sample_assets])
        cur.execute('''INSERT INTO maintenance(asset_id,service_date,service_type,vendor,cost,status,notes,created_by)
                       VALUES(5,'2026-09-16','Repair','Epson Authorized Service',1850,'In Progress','Paper feed roller inspection and replacement','IT Technician')''')
    conn.commit()
    conn.close()


def log_action(action, details=''):
    if 'user' not in session:
        return
    conn = db()
    conn.execute('INSERT INTO activity(user_name,action,details,created_at) VALUES(?,?,?,?)',
                 (session['user']['name'], action, details, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit(); conn.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


def roles_allowed(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            if session['user']['role'] not in roles:
                flash('You do not have permission to perform that action.', 'danger')
                return redirect(url_for('dashboard'))
            return fn(*args, **kwargs)
        return wrapper
    return deco


@app.context_processor
def helpers():
    return {'current_year': datetime.now().year, 'app_version': APP_VERSION}


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        conn = db(); user = conn.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone(); conn.close()
        if user and check_password_hash(user['password'], password):
            session['user'] = {'id':user['id'],'name':user['name'],'email':user['email'],'role':user['role']}
            log_action('Signed in', f"Role: {user['role']}")
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    conn = db()
    stats = conn.execute('''SELECT COUNT(*) total,
        SUM(CASE WHEN status='Assigned' THEN 1 ELSE 0 END) assigned,
        SUM(CASE WHEN status='Available' THEN 1 ELSE 0 END) available,
        SUM(CASE WHEN status='Maintenance' THEN 1 ELSE 0 END) maintenance,
        SUM(purchase_cost) total_value FROM assets''').fetchone()
    categories = conn.execute('SELECT category, COUNT(*) count FROM assets GROUP BY category ORDER BY count DESC').fetchall()
    recent_assets = conn.execute('SELECT * FROM assets ORDER BY id DESC LIMIT 5').fetchall()
    recent_activity = conn.execute('SELECT * FROM activity ORDER BY id DESC LIMIT 7').fetchall()
    maintenance_due = conn.execute("SELECT a.*, m.service_date, m.service_type, m.status mstatus FROM maintenance m JOIN assets a ON a.id=m.asset_id WHERE m.status!='Completed' ORDER BY m.service_date DESC LIMIT 5").fetchall()
    conn.close()
    max_cat = max([r['count'] for r in categories], default=1)
    return render_template('dashboard.html', stats=stats, categories=categories, max_cat=max_cat,
                           recent_assets=recent_assets, recent_activity=recent_activity, maintenance_due=maintenance_due)


@app.route('/assets')
@login_required
def assets():
    q = request.args.get('q','').strip()
    status = request.args.get('status','').strip()
    category = request.args.get('category','').strip()
    sql = 'SELECT * FROM assets WHERE 1=1'; params=[]
    if q:
        sql += ' AND (asset_tag LIKE ? OR name LIKE ? OR brand LIKE ? OR model LIKE ? OR assigned_to LIKE ? OR serial_no LIKE ?)'
        like=f'%{q}%'; params += [like]*6
    if status:
        sql += ' AND status=?'; params.append(status)
    if category:
        sql += ' AND category=?'; params.append(category)
    sql += ' ORDER BY id DESC'
    conn=db(); rows=conn.execute(sql,params).fetchall(); cats=conn.execute('SELECT DISTINCT category FROM assets ORDER BY category').fetchall(); conn.close()
    return render_template('assets.html', assets=rows, categories=cats, q=q, status=status, category=category)


@app.route('/assets/new', methods=['GET','POST'])
@roles_allowed('admin')
def asset_new():
    if request.method == 'POST':
        data = get_asset_form()
        try:
            conn=db(); conn.execute('''INSERT INTO assets(asset_tag,name,category,brand,model,serial_no,assigned_to,department,status,purchase_date,warranty_until,purchase_cost,location,notes,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (*data, datetime.now().isoformat(timespec='seconds'))); conn.commit(); conn.close()
            log_action('Created asset', f'{data[0]} — {data[1]}')
            flash('Asset created successfully.', 'success'); return redirect(url_for('assets'))
        except sqlite3.IntegrityError:
            flash('Asset tag must be unique.', 'danger')
    return render_template('asset_form.html', asset=None)


def get_asset_form():
    return (
        request.form.get('asset_tag','').strip(), request.form.get('name','').strip(), request.form.get('category','').strip(),
        request.form.get('brand','').strip(), request.form.get('model','').strip(), request.form.get('serial_no','').strip(),
        request.form.get('assigned_to','').strip(), request.form.get('department','').strip(), request.form.get('status','Available'),
        request.form.get('purchase_date',''), request.form.get('warranty_until',''), float(request.form.get('purchase_cost') or 0),
        request.form.get('location','').strip(), request.form.get('notes','').strip()
    )


@app.route('/assets/<int:asset_id>')
@login_required
def asset_detail(asset_id):
    conn=db(); asset=conn.execute('SELECT * FROM assets WHERE id=?',(asset_id,)).fetchone();
    maintenance=conn.execute('SELECT * FROM maintenance WHERE asset_id=? ORDER BY service_date DESC,id DESC',(asset_id,)).fetchall(); conn.close()
    if not asset: return ('Not found',404)
    return render_template('asset_detail.html', asset=asset, maintenance=maintenance)


@app.route('/assets/<int:asset_id>/edit', methods=['GET','POST'])
@roles_allowed('admin')
def asset_edit(asset_id):
    conn=db(); asset=conn.execute('SELECT * FROM assets WHERE id=?',(asset_id,)).fetchone(); conn.close()
    if not asset: return ('Not found',404)
    if request.method == 'POST':
        data=get_asset_form()
        try:
            conn=db(); conn.execute('''UPDATE assets SET asset_tag=?,name=?,category=?,brand=?,model=?,serial_no=?,assigned_to=?,department=?,status=?,purchase_date=?,warranty_until=?,purchase_cost=?,location=?,notes=? WHERE id=?''', (*data,asset_id)); conn.commit(); conn.close()
            log_action('Updated asset', f'{data[0]} — {data[1]}')
            flash('Asset updated successfully.', 'success'); return redirect(url_for('asset_detail',asset_id=asset_id))
        except sqlite3.IntegrityError:
            flash('Asset tag must be unique.', 'danger')
    return render_template('asset_form.html', asset=asset)


@app.post('/assets/<int:asset_id>/delete')
@roles_allowed('admin')
def asset_delete(asset_id):
    conn=db(); asset=conn.execute('SELECT * FROM assets WHERE id=?',(asset_id,)).fetchone()
    if asset:
        conn.execute('DELETE FROM maintenance WHERE asset_id=?',(asset_id,)); conn.execute('DELETE FROM assets WHERE id=?',(asset_id,)); conn.commit()
        log_action('Deleted asset', f"{asset['asset_tag']} — {asset['name']}")
        flash('Asset deleted.', 'success')
    conn.close(); return redirect(url_for('assets'))


@app.post('/assets/<int:asset_id>/maintenance')
@roles_allowed('admin','technician')
def maintenance_add(asset_id):
    conn=db(); asset=conn.execute('SELECT * FROM assets WHERE id=?',(asset_id,)).fetchone()
    if not asset: conn.close(); return ('Not found',404)
    service_date=request.form.get('service_date') or datetime.now().strftime('%Y-%m-%d')
    stype=request.form.get('service_type','Inspection').strip(); vendor=request.form.get('vendor','').strip()
    cost=float(request.form.get('cost') or 0); status=request.form.get('status','Completed'); notes=request.form.get('notes','').strip()
    conn.execute('INSERT INTO maintenance(asset_id,service_date,service_type,vendor,cost,status,notes,created_by) VALUES(?,?,?,?,?,?,?,?)',
                 (asset_id,service_date,stype,vendor,cost,status,notes,session['user']['name']))
    if status == 'In Progress': conn.execute("UPDATE assets SET status='Maintenance' WHERE id=?",(asset_id,))
    conn.commit(); conn.close()
    log_action('Added maintenance record', f"{asset['asset_tag']} — {stype}")
    flash('Maintenance record added.', 'success'); return redirect(url_for('asset_detail',asset_id=asset_id))


@app.route('/export/assets.csv')
@login_required
def export_csv():
    conn=db(); rows=conn.execute('SELECT * FROM assets ORDER BY asset_tag').fetchall(); conn.close()
    out=io.StringIO(); writer=csv.writer(out)
    writer.writerow(['Asset Tag','Name','Category','Brand','Model','Serial No','Assigned To','Department','Status','Purchase Date','Warranty Until','Purchase Cost','Location'])
    for r in rows:
        writer.writerow([r['asset_tag'],r['name'],r['category'],r['brand'],r['model'],r['serial_no'],r['assigned_to'],r['department'],r['status'],r['purchase_date'],r['warranty_until'],r['purchase_cost'],r['location']])
    log_action('Exported assets', f'{len(rows)} records')
    return Response(out.getvalue(), mimetype='text/csv', headers={'Content-Disposition':'attachment; filename=assetsphere-assets.csv'})


@app.route('/activity')
@login_required
def activity():
    conn=db(); rows=conn.execute('SELECT * FROM activity ORDER BY id DESC LIMIT 100').fetchall(); conn.close()
    return render_template('activity.html', activity=rows)


if __name__ == '__main__':
    init_db()
    print('AssetSphere Pro v2.1 RBAC running at http://127.0.0.1:5001')
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1', host='127.0.0.1', port=5001)
