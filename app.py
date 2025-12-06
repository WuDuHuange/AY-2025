from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import datetime

app = Flask(__name__)

def init_db():
    """初始化数据库，创建 userlog 表（如果不存在）"""
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS userlog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            timestamp TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route('/main', methods=["GET", "POST"])
def main():
    # 使用 POST 提交写入数据库，之后使用重定向避免重复提交（PRG）
    if request.method == 'POST':
        name = (request.form.get("q") or "").strip()
        if name:
            timestamp = datetime.datetime.now()
            conn = sqlite3.connect('user.db')
            c = conn.cursor()
            c.execute("INSERT INTO userlog (name, timestamp) VALUES (?, ?)", (name, timestamp))
            conn.commit()
            c.close()
            conn.close()
        # 重定向到 GET /main，防止刷新重复提交
        return redirect(url_for('main'))

    # GET 请求渲染页面
    return render_template("main.html")

@app.route('/paynow', methods=["POST"])
def paynow():
    return render_template("paynow.html")

@app.route('/depositmoney', methods=["POST"])
def depositmoney():
    return render_template("depositmoney.html")

@app.route('/userlog', methods=["GET"])
def userlog():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("SELECT id, name, timestamp FROM userlog ORDER BY id DESC")
    rows = c.fetchall()
    c.close()
    conn.close()

    # 将查询结果传给模板，模板负责展示
    return render_template("userlog.html", rows=rows)

@app.route('/deleteuserlog', methods=["POST"])
def deleteuserlog():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    c.execute("DELETE FROM userlog")
    conn.commit()
    c.close()
    conn.close()
    return render_template("deleteuserlog.html")

if __name__ == '__main__':
    init_db()  # 启动前初始化数据库
    app.run()