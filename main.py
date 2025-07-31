from flask import Flask, request, render_template_string, redirect, url_for
import uuid

app = Flask(__name__)
clipboard_content = ""
shared_clips = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    global clipboard_content
    if request.method == 'POST':
        clipboard_content = request.form.get('content', '')
    return render_template_string('''
        <h2>FlashPaste 在线剪贴板</h2>
        <form method="post">
            <textarea name="content" rows="10" cols="50">{{ content }}</textarea><br>
            <button type="submit">保存</button>
        </form>
        <form method="post" action="/share">
            <input type="hidden" name="content" value="{{ content }}">
            <label><input type="checkbox" name="burn_after_reading" value="1"> 阅后即焚</label>
            <button type="submit">生成分享链接</button>
        </form>
        <p>当前内容：</p>
        <pre>{{ content }}</pre>
        {% if share_url %}
        <p>分享链接：<a href="{{ share_url }}" target="_blank">{{ share_url }}</a></p>
        {% endif %}
    ''', content=clipboard_content, share_url=request.args.get('share_url'))

@app.route('/share', methods=['POST'])
def share():
    content = request.form.get('content', '')
    burn = request.form.get('burn_after_reading', '') == '1'
    share_id = str(uuid.uuid4())
    shared_clips[share_id] = {'content': content, 'burn': burn}
    return redirect(url_for('index', share_url=url_for('shared', share_id=share_id, _external=True)))

@app.route('/s/<share_id>')
def shared(share_id):
    clip = shared_clips.get(share_id, None)
    if clip is None:
        return "分享内容不存在或已失效。"
    content = clip['content']
    burn = clip['burn']
    if burn:
        shared_clips.pop(share_id, None)
        burn_tip = '<p style="color:red;">该内容已被销毁，刷新页面将无法再次查看。</p>'
    else:
        burn_tip = ''
    return render_template_string('''
        <h2>FlashPaste 分享内容{% if burn %}（阅后即焚）{% endif %}</h2>
        <pre>{{ content }}</pre>
        <a href="/">返回首页</a>
        {{ burn_tip|safe }}
    ''', content=content, burn=burn, burn_tip=burn_tip)

if __name__ == "__main__":
    app.run(debug=True)
