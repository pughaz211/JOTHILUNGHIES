from flask import Flask, render_template, request, redirect, session, flash
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'jothi_secret_key'

DB_FILE = 'data.json'

# Initialize admin credentials (hashed password)
ADMIN_USERNAME = 'jothilingam'
ADMIN_PASSWORD_HASH = generate_password_hash('jothi3845')

# Load data from JSON
def load_data():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump({'customers': {}}, f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

# Save data to JSON
def save_data(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']

        # Debugging: Print the incoming username and password
        print(f"Login attempt for username: {uname}")

        # Admin login check  
        if uname == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, pwd):  
            session['admin'] = True  
            print(f"Admin login successful for: {uname}")
            return redirect('/admin')  

        # Load customer data
        data = load_data()
        customers = data['customers']

        # Customer login check  
        if uname in customers:
            print(f"Customer found: {uname}")
            if check_password_hash(customers[uname]['password'], pwd):  
                session['customer'] = uname  
                print(f"Customer login successful for: {uname}")
                return redirect('/customer')
            else:
                print(f"Invalid password for customer: {uname}")
        else:
            print(f"Customer not found: {uname}")

        flash('Invalid username or password')  

    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin'):
        return redirect('/')

    data = load_data()
    customers = data['customers']

    if request.method == 'POST':
        if request.form.get('create_customer') == 'true':
            new_user = request.form['new_username']
            new_pass = request.form['new_password']
            if new_user not in customers:
                # Create customer with hashed password
                customers[new_user] = {
                    'password': generate_password_hash(new_pass),
                    'pending_amount': 0,
                    'payments': []
                }
                save_data(data)
        else:
            username = request.form.get('username')
            amount = request.form.get('amount')
            date = request.form.get('date')
            action = request.form.get('action')

            # Check if all fields are provided
            if not all([username, amount, date, action]):
                flash("Please fill in all fields.")
                return redirect('/admin')

            try:
                amount = float(amount)
            except ValueError:
                flash("Amount must be a number.")
                return redirect('/admin')

            if username in customers:
                if action == 'add':
                    customers[username]['pending_amount'] += amount
                elif action == 'subtract':
                    customers[username]['pending_amount'] -= amount
                    amount = -amount
                customers[username]['payments'].append({
                    'amount': amount,
                    'date': date
                })
                save_data(data)
            else:
                flash("Customer does not exist.")
                return redirect('/admin')

    return render_template('admin_dashboard.html', customers=customers)

@app.route('/customer')
def customer_dashboard():
    uname = session.get('customer')
    if not uname:
        return redirect('/')

    data = load_data()
    customer = data['customers'].get(uname)
    if not customer:
        return redirect('/')

    return render_template(
        'customer_dashboard.html',
        username=uname,
        pending=customer['pending_amount'],
        payments=customer['payments']
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    # Run the app in debug mode to get detailed error messages
    app.run(debug=True)