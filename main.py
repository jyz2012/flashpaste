from flask import Flask, request, render_template, redirect, url_for, session
import uuid
import sqlite3
import os

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
            password TEXT
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
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO shared_clips (share_id, content, burn, password) VALUES (?, ?, ?, ?)',
              (share_id, content, int(burn), password))
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

if __name__ == "__main__":
    app.run(debug=True)
