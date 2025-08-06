from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import uuid
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'flashpaste-secret-key'
clipboard_content = ""
clipboard_title = ""
DATABASE = 'flashpaste.db'
def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE shared_clips (
            share_id TEXT PRIMARY KEY,
            content TEXT,
            burn INTEGER,
            password TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            view_count INTEGER DEFAULT 0,
            title TEXT
        )''')
        # 新增用户表
        c.execute('''CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        conn.commit()
        conn.close()
    else:
        # 检查并添加新列（为了兼容现有数据库）
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute('ALTER TABLE shared_clips ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('ALTER TABLE shared_clips ADD COLUMN expires_at TIMESTAMP')
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('ALTER TABLE shared_clips ADD COLUMN view_count INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        try:
            c.execute('ALTER TABLE shared_clips ADD COLUMN title TEXT')
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    global clipboard_content, clipboard_title
    if request.method == 'POST':
        clipboard_content = request.form.get('content', '')
        clipboard_title = request.form.get('title', '')
    return render_template('index.html', content=clipboard_content, title=clipboard_title, share_url=request.args.get('share_url'))

@app.route('/share', methods=['POST'])
def share():
    content = request.form.get('content', '')
    title = request.form.get('title', '').strip()  # 使用内容标题
    burn = request.form.get('burn_after_reading', '') == '1'
    password = request.form.get('password', '').strip()
    expire_hours = request.form.get('expire_hours', '')
    
    # 如果没有标题，使用内容的前30个字符作为标题
    if not title:
        title = content[:30] + ('...' if len(content) > 30 else '')
    
    # 计算过期时间
    expires_at = None
    if expire_hours and expire_hours.isdigit():
        hours = int(expire_hours)
        if hours > 0:
            expires_at = datetime.now() + timedelta(hours=hours)
    
    share_id = str(uuid.uuid4())
    user_id = session.get('user_id')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO shared_clips 
                 (share_id, content, burn, password, user_id, title, expires_at, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (share_id, content, int(burn), password, user_id, title, expires_at, datetime.now()))
    conn.commit()
    conn.close()
    return redirect(url_for('index', share_url=url_for('shared', share_id=share_id, _external=True)))

@app.route('/s/<share_id>', methods=['GET', 'POST'])
def shared(share_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT content, burn, password, expires_at, title, view_count FROM shared_clips WHERE share_id=?', (share_id,))
    row = c.fetchone()
    if row is None:
        conn.close()
        return "分享内容不存在或已失效。"
    
    content, burn, password, expires_at, title, view_count = row
    burn = bool(burn)
    
    # 检查是否过期
    if expires_at:
        expire_time = datetime.fromisoformat(expires_at)
        if datetime.now() > expire_time:
            conn.close()
            return "分享内容已过期。"
    
    # 密码校验
    if password:
        if request.method == 'POST':
            input_pwd = request.form.get('password', '')
            if input_pwd == password:
                session['access_'+share_id] = True
            else:
                conn.close()
                return render_template('password.html', error=True)
        if not session.get('access_'+share_id, False):
            conn.close()
            return render_template('password.html', error=False)
    
    # 增加访问计数
    c.execute('UPDATE shared_clips SET view_count = view_count + 1 WHERE share_id=?', (share_id,))
    conn.commit()
    
    # 阅后即焚
    if burn:
        c.execute('DELETE FROM shared_clips WHERE share_id=?', (share_id,))
        conn.commit()
        burn_tip = '该内容已被销毁，刷新页面将无法再次查看。'
    else:
        burn_tip = ''
    
    conn.close()
    return render_template('shared.html', content=content, burn=burn, burn_tip=burn_tip, title=title)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            return render_template('register.html', error='用户名和密码不能为空')
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, generate_password_hash(password)))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='用户名已存在')
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT user_id, password FROM users WHERE username=?', (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[1], password):
            session['user_id'] = row[0]
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/myshares')
def myshares():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT share_id, content, title, created_at, expires_at, view_count, burn, password 
                 FROM shared_clips WHERE user_id=? ORDER BY created_at DESC''', (session['user_id'],))
    shares = c.fetchall()
    conn.close()
    
    # 处理分享数据，添加状态信息
    processed_shares = []
    for share in shares:
        share_id, content, title, created_at, expires_at, view_count, burn, password = share
        
        # 检查状态
        status = "正常"
        if expires_at:
            expire_time = datetime.fromisoformat(expires_at)
            if datetime.now() > expire_time:
                status = "已过期"
        
        processed_shares.append({
            'share_id': share_id,
            'content': content,
            'title': title or (content[:30] + ('...' if len(content) > 30 else '')),
            'created_at': created_at,
            'expires_at': expires_at,
            'view_count': view_count or 0,
            'status': status,
            'has_password': bool(password),
            'is_burn': bool(burn)
        })
    
    return render_template('myshares.html', shares=processed_shares)

@app.route('/delete_share/<share_id>', methods=['POST'])
def delete_share(share_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # 确保只能删除自己的分享
    c.execute('DELETE FROM shared_clips WHERE share_id=? AND user_id=?', (share_id, session['user_id']))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    
    if deleted:
        return jsonify({'success': True, 'message': '删除成功'})
    else:
        return jsonify({'success': False, 'message': '删除失败或无权限'})

@app.route('/edit_share/<share_id>', methods=['GET', 'POST'])
def edit_share(share_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    if request.method == 'GET':
        # 获取分享信息
        c.execute('''SELECT content, title, password, expires_at, burn 
                     FROM shared_clips WHERE share_id=? AND user_id=?''', 
                  (share_id, session['user_id']))
        row = c.fetchone()
        conn.close()
        
        if row is None:
            return "分享不存在或无权限编辑"
        
        content, title, password, expires_at, burn = row
        
        # 计算剩余小时数
        expire_hours = ""
        if expires_at:
            expire_time = datetime.fromisoformat(expires_at)
            remaining = expire_time - datetime.now()
            if remaining.total_seconds() > 0:
                expire_hours = str(int(remaining.total_seconds() / 3600))
        
        return render_template('edit_share.html', 
                             share_id=share_id,
                             content=content, 
                             title=title or "",
                             password=password or "",
                             expire_hours=expire_hours,
                             burn=bool(burn))
    
    else:  # POST - 更新分享
        content = request.form.get('content', '')
        title = request.form.get('title', '').strip()
        password = request.form.get('password', '').strip()
        expire_hours = request.form.get('expire_hours', '')
        burn = request.form.get('burn_after_reading', '') == '1'
        
        # 如果没有标题，使用内容的前30个字符作为标题
        if not title:
            title = content[:30] + ('...' if len(content) > 30 else '')
        
        # 计算新的过期时间
        expires_at = None
        if expire_hours and expire_hours.isdigit():
            hours = int(expire_hours)
            if hours > 0:
                expires_at = datetime.now() + timedelta(hours=hours)
        
        # 更新分享
        c.execute('''UPDATE shared_clips 
                     SET content=?, title=?, password=?, expires_at=?, burn=?
                     WHERE share_id=? AND user_id=?''',
                  (content, title, password, expires_at, int(burn), share_id, session['user_id']))
        
        updated = c.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            return redirect(url_for('myshares'))
        else:
            return "更新失败或无权限"

if __name__ == "__main__":
    app.run(debug=True)
