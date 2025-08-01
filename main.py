from flask import Flask, request, render_template, redirect, url_for, session
import uuid

app = Flask(__name__)
app.secret_key = 'flashpaste-secret-key'
clipboard_content = ""
shared_clips = {}

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
    shared_clips[share_id] = {'content': content, 'burn': burn, 'password': password}
    return redirect(url_for('index', share_url=url_for('shared', share_id=share_id, _external=True)))

@app.route('/s/<share_id>', methods=['GET', 'POST'])
def shared(share_id):
    clip = shared_clips.get(share_id, None)
    if clip is None:
        return "分享内容不存在或已失效。"
    password = clip.get('password', '')
    burn = clip.get('burn', False)
    content = clip.get('content', '')
    # 密码校验
    if password:
        if request.method == 'POST':
            input_pwd = request.form.get('password', '')
            if input_pwd == password:
                session['access_'+share_id] = True
            else:
                return render_template('password.html', error=True)
        if not session.get('access_'+share_id, False):
            return render_template('password.html', error=False)
    # 阅后即焚
    if burn:
        shared_clips.pop(share_id, None)
        burn_tip = '该内容已被销毁，刷新页面将无法再次查看。'
    else:
        burn_tip = ''
    return render_template('shared.html', content=content, burn=burn, burn_tip=burn_tip)

if __name__ == "__main__":
    app.run(debug=True)
