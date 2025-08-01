from flask import Flask, request, render_template, redirect, url_for, session
import uuid
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'flashpaste-secret-key'
clipboard_content = ""
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
            user_id INTEGER
        )''')
        # 新增用户表
        c.execute('''CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        conn.commit()
        conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    global clipboard_content
    if request.method == 'POST':
        clipboard_content = request.form.get('content', '')
    return render_template('index.html', content=clipboard_content, share_url=request.args.get('share_url'))

@app.route('/share', methods=['POST'])
def share():
    content = request.form.get('content', '')
    burn = request.form.get('burn_after_reading', '') == '1'
    password = request.form.get('password', '').strip()
    share_id = str(uuid.uuid4())
    user_id = session.get('user_id')
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO shared_clips (share_id, content, burn, password, user_id) VALUES (?, ?, ?, ?, ?)',
              (share_id, content, int(burn), password, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index', share_url=url_for('shared', share_id=share_id, _external=True)))

@app.route('/s/<share_id>', methods=['GET', 'POST'])
def shared(share_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT content, burn, password FROM shared_clips WHERE share_id=?', (share_id,))
    row = c.fetchone()
    if row is None:
        conn.close()
        return "分享内容不存在或已失效。"
    content, burn, password = row
    burn = bool(burn)
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
    # 阅后即焚
    if burn:
        c.execute('DELETE FROM shared_clips WHERE share_id=?', (share_id,))
        conn.commit()
        burn_tip = '该内容已被销毁，刷新页面将无法再次查看。'
    else:
        burn_tip = ''
    conn.close()
    return render_template('shared.html', content=content, burn=burn, burn_tip=burn_tip)

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
    c.execute('SELECT share_id, content FROM shared_clips WHERE user_id=?', (session['user_id'],))
    shares = c.fetchall()
    conn.close()
    return render_template('myshares.html', shares=shares)

if __name__ == "__main__":
    app.run(debug=True)
