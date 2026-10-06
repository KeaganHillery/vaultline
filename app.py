import os, sqlite3, secrets
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,'data','vaultline.db')
UPLOADS=os.path.join(BASE,'uploads')
os.makedirs(os.path.dirname(DB),exist_ok=True); os.makedirs(UPLOADS,exist_ok=True)
app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY') or 'CHANGE-ME-'+secrets.token_hex(24)
app.config['MAX_CONTENT_LENGTH']=25*1024*1024

ALLOWED={'pdf','png','jpg','jpeg','webp','txt','doc','docx','xls','xlsx','csv'}

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user', active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category TEXT NOT NULL, description TEXT DEFAULT '', location TEXT DEFAULT '', owner TEXT DEFAULT '', expiry_date TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL, filename TEXT NOT NULL, stored_name TEXT NOT NULL, uploaded_at TEXT NOT NULL, FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT NOT NULL, target TEXT, created_at TEXT NOT NULL);
    ''');
    try: c.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    except sqlite3.OperationalError: pass
    try: c.execute("ALTER TABLE users ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError: pass
    c.commit(); c.close()

def audit(action,target=''):
    c=db(); c.execute('INSERT INTO audit(username,action,target,created_at) VALUES(?,?,?,?)',(session.get('user','system'),action,target,datetime.utcnow().isoformat(timespec='seconds'))); c.commit(); c.close()

def login_required(f):
    @wraps(f)
    def w(*a,**kw):
        if 'user' not in session: return redirect(url_for('login',next=request.path))
        return f(*a,**kw)
    return w

def allowed_file(fn): return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED

def admin_required(f):
    @wraps(f)
    def w(*a,**kw):
        if 'user' not in session: return redirect(url_for('login',next=request.path))
        c=db(); row=c.execute('SELECT role,active FROM users WHERE username=?',(session['user'],)).fetchone(); c.close()
        if not row or not row['active'] or row['role']!='admin': abort(403)
        return f(*a,**kw)
    return w

@app.after_request
def headers(r):
    r.headers['X-Content-Type-Options']='nosniff'; r.headers['X-Frame-Options']='DENY'; r.headers['Referrer-Policy']='no-referrer'; r.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:"
    return r

@app.route('/setup',methods=['GET','POST'])
def setup():
    c=db(); count=c.execute('SELECT COUNT(*) n FROM users').fetchone()['n']; c.close()
    if count: return redirect(url_for('login'))
    if request.method=='POST':
        u=request.form.get('username','').strip(); p=request.form.get('password',''); confirm=request.form.get('confirm_password','')
        if not u or len(p)<8 or p!=confirm:
            flash('Use a username and matching password of at least 8 characters.','error')
            return render_template('setup.html')
        c=db()
        c.execute('INSERT INTO users(username,password,role,active,created_at) VALUES(?,?,?,?,?)',(u,generate_password_hash(p),'admin',1,datetime.utcnow().isoformat(timespec='seconds')))
        c.commit(); c.close()
        flash('Administrator account created.','ok')
        return redirect(url_for('login'))
    return render_template('setup.html')

@app.route('/login',methods=['GET','POST'])
def login():
    c=db(); count=c.execute('SELECT COUNT(*) n FROM users').fetchone()['n']; c.close()
    if count==0: return redirect(url_for('setup'))
    if request.method=='POST':
        u=request.form.get('username','').strip(); p=request.form.get('password','')
        c=db(); row=c.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone(); c.close()
        if row and row['active'] and check_password_hash(row['password'],p): session['user']=u; audit('login'); return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid username or password.','error')
    return render_template('login.html')

@app.route('/admin')
@admin_required
def admin():
    c=db(); users=c.execute('SELECT id,username,role,active,created_at FROM users ORDER BY username COLLATE NOCASE').fetchall(); c.close()
    return render_template('admin.html',users=users)

@app.route('/admin/user/new',methods=['POST'])
@admin_required
def admin_new_user():
    u=request.form.get('username','').strip(); p=request.form.get('password',''); role=request.form.get('role','user')
    if not u or len(p)<8 or role not in ('user','admin'):
        flash('Enter a username, password of at least 8 characters, and a valid role.','error')
        return redirect(url_for('admin'))
    try:
        c=db()
        c.execute('INSERT INTO users(username,password,role,active,created_at) VALUES(?,?,?,?,?)',(u,generate_password_hash(p),role,1,datetime.utcnow().isoformat(timespec='seconds')))
        c.commit(); c.close()
        flash('User created.','ok')
    except sqlite3.IntegrityError:
        flash('Username already exists.','error')
    return redirect(url_for('admin'))

@app.route('/admin/user/<int:id>/toggle',methods=['POST'])
@admin_required
def admin_toggle_user(id):
    c=db(); row=c.execute('SELECT username,active FROM users WHERE id=?',(id,)).fetchone()
    if row and row['username']!=session['user']:
        c.execute('UPDATE users SET active=? WHERE id=?',(0 if row['active'] else 1,id)); c.commit()
    c.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    c=db(); total=c.execute('SELECT COUNT(*) n FROM items').fetchone()['n']; docs=c.execute('SELECT COUNT(*) n FROM documents').fetchone()['n']; today=date.today().isoformat(); soon=(date.today()).toordinal()+30
    rows=c.execute("SELECT * FROM items WHERE expiry_date!='' ORDER BY expiry_date LIMIT 100").fetchall(); exp=[]
    for r in rows:
        try:
            d=date.fromisoformat(r['expiry_date']); days=(d-date.today()).days
            if days<=30: exp.append((r,days))
        except: pass
    recent=c.execute('SELECT * FROM items ORDER BY updated_at DESC LIMIT 6').fetchall(); c.close()
    return render_template('dashboard.html',total=total,docs=docs,exp=exp,recent=recent)

@app.route('/items')
@login_required
def items():
    q=request.args.get('q','').strip(); cat=request.args.get('category','').strip(); c=db(); sql='SELECT * FROM items WHERE 1=1'; args=[]
    if q: sql+=' AND (name LIKE ? OR description LIKE ? OR owner LIKE ? OR location LIKE ?)'; args += [f'%{q}%']*4
    if cat: sql+=' AND category=?'; args.append(cat)
    sql+=' ORDER BY name COLLATE NOCASE'; rows=c.execute(sql,args).fetchall(); cats=[x['category'] for x in c.execute('SELECT DISTINCT category FROM items ORDER BY category').fetchall()]; c.close()
    return render_template('items.html',items=rows,cats=cats,q=q,category=cat)

@app.route('/item/new',methods=['GET','POST'])
@login_required
def new_item():
    if request.method=='POST':
        now=datetime.utcnow().isoformat(timespec='seconds'); vals=[request.form.get(x,'').strip() for x in ['name','category','description','location','owner','expiry_date']]
        if not vals[0] or not vals[1]: flash('Name and category are required.','error'); return render_template('item_form.html',item=None)
        c=db(); cur=c.execute('INSERT INTO items(name,category,description,location,owner,expiry_date,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(*vals,now,now)); iid=cur.lastrowid; c.commit(); c.close(); audit('create_item',str(iid)); return redirect(url_for('item',id=iid))
    return render_template('item_form.html',item=None)

@app.route('/item/<int:id>',methods=['GET','POST'])
@login_required
def item(id):
    c=db(); row=c.execute('SELECT * FROM items WHERE id=?',(id,)).fetchone(); docs=c.execute('SELECT * FROM documents WHERE item_id=? ORDER BY uploaded_at DESC',(id,)).fetchall(); c.close()
    if not row: abort(404)
    if request.method=='POST':
        now=datetime.utcnow().isoformat(timespec='seconds'); vals=[request.form.get(x,'').strip() for x in ['name','category','description','location','owner','expiry_date']]
        c=db(); c.execute('UPDATE items SET name=?,category=?,description=?,location=?,owner=?,expiry_date=?,updated_at=? WHERE id=?',(*vals,now,id)); c.commit(); c.close(); audit('update_item',str(id)); flash('Saved.','ok'); return redirect(url_for('item',id=id))
    return render_template('item.html',item=row,docs=docs)

@app.route('/item/<int:id>/delete',methods=['POST'])
@login_required
def delete_item(id):
    c=db(); docs=c.execute('SELECT stored_name FROM documents WHERE item_id=?',(id,)).fetchall();
    for d in docs:
        try: os.remove(os.path.join(UPLOADS,d['stored_name']))
        except OSError: pass
    c.execute('DELETE FROM documents WHERE item_id=?',(id,)); c.execute('DELETE FROM items WHERE id=?',(id,)); c.commit(); c.close(); audit('delete_item',str(id)); return redirect(url_for('items'))

@app.route('/item/<int:id>/upload',methods=['POST'])
@login_required
def upload(id):
    f=request.files.get('file'); c=db(); exists=c.execute('SELECT id FROM items WHERE id=?',(id,)).fetchone(); c.close()
    if not exists: abort(404)
    if not f or not f.filename: flash('Choose a file.','error'); return redirect(url_for('item',id=id))
    if not allowed_file(f.filename): flash('File type not allowed.','error'); return redirect(url_for('item',id=id))
    original=secure_filename(f.filename); stored=secrets.token_hex(16)+'_'+original; f.save(os.path.join(UPLOADS,stored)); c=db(); c.execute('INSERT INTO documents(item_id,filename,stored_name,uploaded_at) VALUES(?,?,?,?)',(id,original,stored,datetime.utcnow().isoformat(timespec='seconds'))); c.execute('UPDATE items SET updated_at=? WHERE id=?',(datetime.utcnow().isoformat(timespec='seconds'),id)); c.commit(); c.close(); audit('upload_document',str(id)); return redirect(url_for('item',id=id))

@app.route('/document/<int:id>/download')
@login_required
def download(id):
    c=db(); d=c.execute('SELECT * FROM documents WHERE id=?',(id,)).fetchone(); c.close()
    if not d: abort(404)
    audit('download_document',str(id)); return send_from_directory(UPLOADS,d['stored_name'],download_name=d['filename'],as_attachment=True)

@app.route('/document/<int:id>/delete',methods=['POST'])
@login_required
def delete_doc(id):
    c=db(); d=c.execute('SELECT * FROM documents WHERE id=?',(id,)).fetchone();
    if d:
        try: os.remove(os.path.join(UPLOADS,d['stored_name']))
        except OSError: pass
        c.execute('DELETE FROM documents WHERE id=?',(id,)); c.commit()
    c.close(); audit('delete_document',str(id)); return redirect(request.referrer or url_for('dashboard'))

@app.route('/export')
@login_required
def export():
    c=db(); items=[dict(x) for x in c.execute('SELECT * FROM items').fetchall()]; docs=[dict(x) for x in c.execute('SELECT id,item_id,filename,uploaded_at FROM documents').fetchall()]; c.close(); audit('export'); return jsonify({'vaultline_export_version':1,'exported_at':datetime.utcnow().isoformat(timespec='seconds')+'Z','items':items,'documents':docs})

@app.route('/health')
def health(): return jsonify(status='ok',version='1.1.0')

init()

if __name__=='__main__': app.run(host='0.0.0.0',port=8080)
