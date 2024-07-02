import os
from cs50 import SQL
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.urandom(24)

db = SQL("sqlite:///icebath.db")

def create_tables():
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
    );
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS bath_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        temperature REAL NOT NULL,
        duration INTEGER NOT NULL
    );
    """)

create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_ice_bath():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    date = request.form['date']
    time = request.form['time']
    temperature = request.form['temperature']
    duration = request.form['duration']

    db.execute("INSERT INTO bath_log (date, time, temperature, duration, user_id) VALUES (?, ?, ?, ?, ?)",
               date, time, temperature, duration, user_id)

    return redirect(url_for('index'))


@app.route('/log')
def log():
    bath_log = db.execute("SELECT * FROM bath_log")
    return render_template('log.html', bath_log=bath_log)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        if not username:
            return apology("must provide username", 400)
        if not password:
            return apology("must provide password", 400)
        if not confirmation:
            return apology("must confirm password", 400)
        if password != confirmation:
            return apology("passwords do not match", 400)

        if is_username_taken(username):
            return apology("username already exists", 400)

        hashed_password = generate_password_hash(password)

        insert_user(username, hashed_password)

        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

def is_username_taken(username):
    user = db.execute("SELECT * FROM users WHERE username = ?", username)
    return len(user) > 0

def insert_user(username, hashed_password):
    db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")

    else:
        return render_template("login.html")


def apology(message, code):
    return f"<h1>{code}</h1><p>{message}</p>"


@app.route('/statistics')
def statistics():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    try:
        total_time_spent = db.execute("SELECT SUM(duration) as total FROM bath_log WHERE user_id = ?", user_id)[0]['total']
        print(f"Total time spent: {total_time_spent}")

        average_duration = db.execute("SELECT AVG(duration) as average FROM bath_log WHERE user_id = ?", user_id)[0]['average']
        print(f"Average duration: {average_duration}")

        frequency = db.execute("SELECT COUNT(*) as count FROM bath_log WHERE user_id = ?", user_id)[0]['count']
        print(f"Frequency: {frequency}")

        return render_template('statistics.html',
                               total_time_spent=total_time_spent or 0,
                               average_duration=average_duration or 0,
                               frequency=frequency or 0)
    except Exception as e:
        print(f"Error occurred: {e}")
        return "An error occurred while fetching statistics."



@app.route('/delete/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    user_id = session.get('user_id')
    db.execute("DELETE FROM bath_log WHERE id = ? AND user_id = ?", log_id, user_id)
    return redirect(url_for('log'))


if __name__ == '__main__':
    app.run(debug=True)
