from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
import random

app = Flask(__name__)
app.secret_key = "secret123"

# Database Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin",
    database="timetable_db"
)
cursor = db.cursor(dictionary=True)

# Home Page
@app.route('/')
def home():
    return render_template('login.html')

# Login Route
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    cursor.execute("SELECT * FROM staff WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    
    if user:
        session['user_id'] = user['id']
        session['name'] = user['name']
        session['role'] = 'admin' if email == "admin@test.com" else 'staff'
        
        if session['role'] == 'admin':
            return redirect('/admin')
        else:
            return redirect('/staff')
    else:
        return "Invalid credentials! <a href='/'>Try again</a>"

# Admin Dashboard
@app.route('/admin')
def admin():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/')
    
    cursor.execute("SELECT * FROM staff")
    staff = cursor.fetchall()
    
    cursor.execute("SELECT * FROM timetable")
    timetable = cursor.fetchall()
    
    return render_template('admin.html', staff=staff, timetable=timetable)

# Add Staff
@app.route('/add_staff', methods=['POST'])
def add_staff():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    contact = request.form['contact']
    
    cursor.execute("INSERT INTO staff (name, email, password, contact) VALUES (%s, %s, %s, %s)",
                   (name, email, password, contact))
    db.commit()
    
    return redirect('/admin')

# Add Timetable
@app.route('/add_timetable', methods=['POST'])
def add_timetable():
    staff_id = request.form['staff_id']
    subject = request.form['subject']
    hours = int(request.form['hours'])
    
    cursor.execute("INSERT INTO timetable (staff_id, subject, hours) VALUES (%s, %s, %s)",
                   (staff_id, subject, hours))
    db.commit()
    
    return redirect('/admin')

# Staff Dashboard
@app.route('/staff')
def staff():
    if 'user_id' not in session or session['role'] != 'staff':
        return redirect('/')
    
    cursor.execute("SELECT * FROM timetable WHERE staff_id = %s", (session['user_id'],))
    timetable = cursor.fetchall()
    
    return render_template('staff.html', name=session['name'], timetable=timetable)

# Timetable Generator
@app.route('/generate_weekly_timetable', methods=['POST'])
def generate_weekly_timetable():
    try:
        cursor.execute("SELECT id, name FROM staff")
        staff = cursor.fetchall()
        
        cursor.execute("SELECT name FROM subjects")
        subjects = [row["name"] for row in cursor.fetchall()]

        if not staff or not subjects:
            return jsonify({"error": "No staff or subjects found"}), 400

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        weekly_timetable = {}

        for day in days:
            daily_schedule = []
            assigned_staff = random.sample(staff, min(len(staff), 5))  # Select up to 4 staff
            assigned_subjects = random.sample(subjects, min(len(subjects), 5))  # 4 subjects per day
            
            for i in range(5):  # 4 periods per day
                if i < len(assigned_staff) and i < len(assigned_subjects):
                    daily_schedule.append({
                        "period": i + 1,
                        "staff_name": assigned_staff[i]["name"],
                        "subject": assigned_subjects[i]
                    })

            weekly_timetable[day] = daily_schedule
        
        return jsonify(weekly_timetable)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)

