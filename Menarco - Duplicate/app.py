from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # required for sessions to work

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Simple in-memory user store for registered users (excluding admin)
users = {}

# Initialize database for visitor logs (you can also create it separately)
def init_db():
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            purpose TEXT,
            check_in_time TEXT,
            check_out_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        name = request.form['name'].strip()
        contact = request.form['contact'].strip()
        address = request.form['address'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            error = "Passwords do not match."
        elif username == ADMIN_USERNAME or username in users:
            error = "Username already taken."
        elif any(user['name'] == name for user in users.values()):
            error = "Email already registered."
        else:
            users[username] = {
                'name':name,
                'contact': contact,
                'address': address,
                'password': password
            }
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['username'] = username
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        elif username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = 'visitor'
            return redirect(url_for('visitor_dashboard'))  # ✅ Redirects to visitor dashboard
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)


@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if session.get('role') != 'visitor':  # changed from 'user' to 'visitor'
        return redirect(url_for('login'))

    username = session['username']
    message = None

    if request.method == 'POST':
        purpose = request.form['purpose'].strip()
        check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save visit record to DB
        conn = sqlite3.connect('visitors.db')
        c = conn.cursor()
        c.execute('INSERT INTO visits (username, purpose, check_in_time) VALUES (?, ?, ?)',
                  (username, purpose, check_in_time))
        conn.commit()
        conn.close()

        message = "Check-in successful at " + check_in_time

    # Fetch user's visit history
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('SELECT id, purpose, check_in_time, check_out_time FROM visits WHERE username = ? ORDER BY check_in_time DESC', (username,))
    visits = c.fetchall()
    conn.close()

    return render_template('user_dashboard.html', username=username, visits=visits, message=message)

@app.route('/visitor-form')
def visitor_form():
    return render_template('visitor_form.html')


@app.route('/visitor_dashboard')
def visitor_dashboard():
    if session.get('role') != 'visitor':
        return redirect(url_for('login'))
    return render_template('visitor_dashboard.html', username=session.get('username'))

    # Fetch user's visits
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('SELECT id, purpose, check_in_time, check_out_time FROM visits WHERE username = ? ORDER BY check_in_time DESC', (username,))
    visits = c.fetchall()
    conn.close()

    return render_template('user_dashboard.html', username=username, visits=visits, message=message)

@app.route('/visitor/profile')
def visitor_profile():
    if session.get('role') != 'visitor':
        return redirect(url_for('visitor_dashboard'))  # Or login if preferred
    return render_template('visitor_profile.html', username=session.get('username'))


@app.route('/visitor_checkout/<int:visitor_id>', methods=['POST'])
def visitor_checkout(visitor_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    check_out_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('UPDATE visits SET check_out_time = ? WHERE id = ?', (check_out_time, visitor_id))
    conn.commit()
    conn.close()

    flash('Visitor checked out successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect('visitors.db')
    c = conn.cursor()
    c.execute('SELECT id, username, purpose, check_in_time, check_out_time FROM visits ORDER BY check_in_time DESC')
    visitors = c.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', visitors=visitors)


@app.route('/admin/profile')
def admin_profile():
    # Pull actual admin info from session or DB
    return render_template('admin_profile.html')


@app.route('/admin/visitor-log')
def admin_visitor_log():
    visitors = [
        (1, 'John Doe', 'Meeting', '123-456-7890', '2025-06-01 10:00 AM'),
        (2, 'Jane Smith', 'Delivery', '987-654-3210', '2025-06-01 10:30 AM')
    ]
    return render_template('admin_visitor_log.html', visitors=visitors)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def home():
    return render_template('home.html')

print(app.url_map)


if __name__ == '__main__':
    app.run(debug=True)
