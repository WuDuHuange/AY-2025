from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import datetime

app = Flask(__name__)

def init_db():
    """Initialize the database and create the userlog table if it doesn't exist."""
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
    # Use POST to write to the database, then redirect to avoid duplicate submissions (PRG)
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
        # Redirect to GET /main to prevent resubmission on refresh
        return redirect(url_for('main'))

    # Render page for GET requests
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

    # Pass query results to the template for rendering
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
    init_db()  # Initialize database before starting
    app.run()