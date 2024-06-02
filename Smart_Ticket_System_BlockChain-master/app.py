from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import time
import uuid
from web3 import Web3
import hashlib
from bson import ObjectId
from datetime import datetime
import random
import traceback

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['smart_tickets']  # Replace 'your_database' with your actual database name
tickets_collection = db['tickets']
customers_collection = db['customers']
purchases_collection = db['purchases']
winners_collection = db['winners']

# Web3 connection to Ganache
ganache_url = 'http://127.0.0.1:7545'
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Set the contract address deployed on Ganache
contract_address = '0xc7830438Cd4c06D7aE190DE980620E79cb450f80'  # Replace with your actual contract address

# Set a secret key for session management
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')



# Define a dictionary of default username and password
seller_credentials = {
    'username': 'admin',
    'password': 'admin'
}


"""
NAVBARS
"""
@app.route('/nav/seller_navbar')
def seller_navbar():
    return render_template('nav/seller_navbar.html')

@app.route('/nav/customer_navbar')
def customer_navbar():
    return render_template('nav/customer_navbar.html')


"""
NAVBARS END
"""

"""ALERT MESSAGES"""

@app.route('/alert_messages/signup_message')
def success():
    message = request.args.get('message')
    return render_template('alert_messages/signup_message.html', message=message)

"""ALERT MESSAGES END"""


"""
SELLER_ADMIN_DASHBOARD START
"""

@app.route('/admin/seller_login', methods=['GET', 'POST'])
def seller_login():
    if request.method == 'POST':
        # Retrieve the username and password from the form
        username = request.form['username']
        password = request.form['password']
        
        # Check if the entered credentials match the default credentials
        if username == seller_credentials['username'] and password == seller_credentials['password']:
            # If credentials are correct, set the user as authenticated in the session
            session['authenticated'] = True
            # Redirect to the seller admin dashboard
            return redirect(url_for('seller_admin_dashboard'))
        else:
            # If credentials are incorrect, display an error message
            error = 'Invalid username or password. Please try again.'
            return render_template('seller_login.html', error=error)
    # If the request method is GET, render the login page
    return render_template('admin/seller_login.html', error=None)

@app.route('/admin/seller_admin_dashboard')
def seller_admin_dashboard():
    # Check if the user is authenticated
    if not session.get('authenticated'):
        # If not authenticated, redirect to the login page
        return redirect(url_for('seller_login'))
    
    # You can pass any necessary data to the template here
    # For example, you might fetch some data from the database to display on the dashboard
    # For now, let's pass a sample data dictionary
    sample_data = {
        'total_tickets_sold': 1000,
        'total_profit': '$5000',
        'current_lottery_status': 'Active'
    }
    return render_template('admin/seller_admin_dashboard.html', data=sample_data)

@app.route('/admin/added_tickets')
def added_tickets():
    # Check if the user is authenticated
    if not session.get('authenticated'):
        # If not authenticated, redirect to the login page
        return redirect(url_for('seller_login'))
    
    # Fetch added tickets data from MongoDB
    tickets = tickets_collection.find()
    
    return render_template('admin/added_tickets.html', tickets=tickets)


# Route for adding a ticket
@app.route('/admin/add_ticket', methods=['GET', 'POST'])
def add_ticket():
    if request.method == 'POST':
        # Retrieve form data
        coupon_name = request.form['coupon_name']
        from_date = request.form['from_date']
        to_date = request.form['to_date']
        description = request.form['description']
        price_money = request.form['price_money']
        ticket_price = request.form['ticket_price']
        
        # Check if ticket with the same name already exists
        existing_ticket = tickets_collection.find_one({'coupon_name': coupon_name})
        if existing_ticket:
            return render_template('admin/add_ticket.html', error_message='Ticket with this name already exists!')
        
        # Generate unique ticket_id
        ticket_id = str(uuid.uuid4())
        
        # Hash ticket data
        hashed_data = hashlib.sha256(f"{ticket_id},{coupon_name},{from_date},{to_date},{description},{price_money}{ticket_price}".encode()).hexdigest()
        
        # Store hashed data in MongoDB
        ticket_data = {
            'ticket_id': ticket_id,
            'coupon_name': coupon_name,
            'from_date': from_date,
            'to_date': to_date,
            'description': description,
            'price_money': price_money,
            'ticket_price': ticket_price,
            'hash': hashed_data  # Store the hashed data in MongoDB
        }
        tickets_collection.insert_one(ticket_data)
        
        # Store hashed data in Ganache blockchain using smart contract
        # Replace 'YourContractFunction' with the actual function in your contract
        # contract = web3.eth.contract(address=contract_address, abi=abi)
        # tx_hash = contract.functions.YourContractFunction(hashed_data).transact()
        
        # For example, if you have a simple store function
        tx_hash = web3.eth.send_transaction({
            'to': contract_address,
            'from': web3.eth.accounts[0],  # Change to appropriate account
            'gas': 2000000,  # Adjust gas limit as needed
            'data': web3.to_hex(text=hashed_data)  # Encode the hashed data here
        })
        
        # Wait for transaction receipt
        web3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Redirect to a success page with a success message
        return redirect(url_for('success', message='Ticket added successfully!'))
    else:
        return render_template('admin/add_ticket.html', error_message=None)
    

"""CUSTOMER LIST"""

@app.route('/admin/customer_list')
def customer_list():
    if not session.get('authenticated'):
        return redirect(url_for('seller_login'))
    
    # Fetch signed-up customers from MongoDB
    customers = list(customers_collection.find())
    
    return render_template('admin/customer_list.html', customers=customers)

"""CUSTOMER LIST END"""


@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect(url_for('seller_login'))  # Change to the appropriate login route


"""DISPLAY TICKETS"""
tickets = [
    {'coupon_name': 'Ticket 1', 'from_date': '2024-04-01', 'to_date': '2024-04-10', 'description': 'Description of Ticket 1', 'price_money': '$10'},
    {'coupon_name': 'Ticket 2', 'from_date': '2024-04-15', 'to_date': '2024-04-25', 'description': 'Description of Ticket 2', 'price_money': '$15'},
    {'coupon_name': 'Ticket 3', 'from_date': '2024-05-01', 'to_date': '2024-05-10', 'description': 'Description of Ticket 3', 'price_money': '$20'}
]



"""DISPLAY TICKTS END"""

"""CUSTOMER SINGUP"""

@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'POST':
        name = request.form['name']
        contact_number = request.form['contact_number']

        # Check if the customer with the same name and contact number already exists
        existing_customer = customers_collection.find_one({'$or': [{'name': name}, {'contact_number': contact_number}]})
        if existing_customer:
            return render_template('customer/customer_login.html', error_message='You are already registered.')

        # If the customer doesn't exist, proceed with signup
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        password = request.form['password']
        
        # Generate unique customer_id
        customer_id = str(uuid.uuid4())
        
        # Insert customer data into MongoDB
        customer_data = {
            'customer_id': customer_id,
            'name': name,
            'contact_number': contact_number,
            'age': age,
            'gender': gender,
            'address': address,
            'password': password
        }
        customers_collection.insert_one(customer_data)
        
        # Redirect to a success page with a success message
        return redirect(url_for('success', message='You have been successfully registered!'))
    else:
        return render_template('customer/customer_signup.html', error_message=None)

"""CUSTOMER SIGNUP END"""

"""CUSTOMER LOGING"""

@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        contact_number = request.form['contact_number']
        password = request.form['password']
        
        # Query MongoDB to find the user with the provided contact number
        user = customers_collection.find_one({'contact_number': contact_number})
        
        if user and user['password'] == password:
            # If user exists and password is correct, set the user as authenticated in the session
            session['authenticated'] = True
            # Convert the ObjectId to a string before storing in the session
            user['_id'] = str(user['_id'])
            session['user'] = user
            # Redirect to the customer dashboard upon successful login
            return redirect(url_for('customer_dashboard'))
        
        # If no matching user found or password is incorrect, display an error message
        error_message = 'Invalid contact number or password. Please try again.'
        return render_template('customer/customer_login.html', error_message=error_message)
    
    # If the request method is GET, render the login page
    return render_template('customer/customer_login.html', error_message=None)

@app.route('/customer/customer_dashboard')
def customer_dashboard():
    # Check if the user is authenticated
    if not session.get('authenticated'):
        # If not authenticated, redirect to the login page
        return redirect(url_for('customer_login'))
    
    # Render the customer dashboard with user information
    user = session['user']
    # Retrieve tickets data from MongoDB
    tickets = list(tickets_collection.find()) 
    return render_template('customer/customer_dashboard.html', user=user, tickets=tickets)


# Route for displaying tickets
@app.route('/display_tickets')
def display_tickets():
    # Check if the user is authenticated
    if not session.get('authenticated'):
        # If not authenticated, redirect to the login page
        return redirect(url_for('customer_login'))
    
    # Fetch added tickets data from MongoDB
    tickets = tickets_collection.find()
    
    return render_template('display_tickets.html', tickets=tickets)

""" PURCHASE TICKET"""
@app.route('/purchase_ticket', methods=['POST'])
def purchase_ticket():
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

    data = request.json
    selected_ticket = {
        'coupon_name': data['coupon_name'],
        'ticket_price': data['ticket_price'],
        'customer_name': data['customer_name']  # Retrieve customer's name from the frontend
    }

    # Get user details from session or database
    user = session.get('user')  # Assuming user details are stored in session

    # Create a unique purchase ID
    purchase_id = str(uuid.uuid4())

    # Store purchase details in MongoDB
    purchase_data = {
        'purchase_id': purchase_id,
        'customer_id': user['customer_id'],
        'customer_name': selected_ticket['customer_name'],  # Use customer's name from selected_ticket
        'coupon_name': selected_ticket['coupon_name'],
        'ticket_price': selected_ticket['ticket_price'],
        'timestamp': datetime.utcnow()
    }

    purchases_collection.insert_one(purchase_data)

    return jsonify({'success': True, 'message': 'Ticket purchased successfully', 'purchase_id': purchase_id})
"""PURCHASE TIKCET END"""

"""SOLD TICKETS LIST"""
@app.route('/admin/sold_tickets')
def sold_tickets():
    if not session.get('authenticated'):
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    user = session.get('user')  # Assuming user details are stored in session

    # Retrieve purchased tickets for the current user from MongoDB
    purchased_tickets = purchases_collection.find({'customer_id': user['customer_id']})

    return render_template('admin/sold_tickets.html', purchased_tickets=purchased_tickets)

"""SOLD TICKETS LIST END"""

"""customer orders"""
@app.route('/customer/purchase_list')
def purchase_list():
    if not session.get('authenticated'):
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    user = session.get('user')  # Assuming user details are stored in session

    # Retrieve purchased tickets for the current user from MongoDB
    purchased_tickets = purchases_collection.find({'customer_id': user['customer_id']})

    return render_template('customer/purchase_list.html', purchased_tickets=purchased_tickets)
"""customer orders end"""

"""Purchased Customers"""
@app.route('/admin/purchased_customers_list')
def purchased_customers_list():
    if not session.get('authenticated'):
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    # Retrieve unique customers who have purchased tickets from MongoDB
    unique_customers = purchases_collection.distinct('customer_name')

    # Initialize an empty list to store customer details
    customers_details = []

    # Fetch customer details for each unique customer
    for customer_name in unique_customers:
        customer_data = purchases_collection.find_one({'customer_name': customer_name})
        
        # Extract required details
        number = customer_data.get('number', 'N/A')
        address = customer_data.get('address', 'N/A')
        coupon_name = customer_data.get('coupon_name', 'N/A')
        ticket_price = customer_data.get('ticket_price', 'N/A')
        
        # Create a dictionary with customer details
        customer_detail = {
            'customer_name': customer_name,
            'number': number,
            'address': address,
            'coupon_name': coupon_name,
            'ticket_price': ticket_price
        }
        
        customers_details.append(customer_detail)

    return render_template('admin/purchased_customers_list.html', customers_details=customers_details)

"""Purchase Customers End"""

"""Decide Winner"""
@app.route('/admin/winner', methods=['GET'])
def winner():
    return render_template('admin/winner.html')


@app.route('/select_winner', methods=['POST'])
def select_winner():
    try:
        if not session.get('authenticated'):
            return jsonify({'success': False, 'message': 'User not authenticated'}), 401

        # Retrieve all purchases from MongoDB
        all_purchases = list(purchases_collection.find())

        if not all_purchases:
            return jsonify({'success': False, 'message': 'No tickets purchased yet'}), 400

        # Randomly select a winner from all purchases
        winning_purchase = random.choice(all_purchases)

        # Convert ObjectIds to strings for JSON serialization
        winning_purchase['_id'] = str(winning_purchase['_id'])

        # Store winner details in MongoDB
        winner_data = {
            'winner_name': winning_purchase['customer_name'],
            'customer_id': winning_purchase['customer_id'],
            'purchase_id': winning_purchase['purchase_id'],
            'coupon_name': winning_purchase['coupon_name'],
            'ticket_price': winning_purchase['ticket_price'],
            'timestamp': datetime.utcnow()
        }

        # Convert ObjectIds to strings in winner_data
        for key, value in winner_data.items():
            if isinstance(value, ObjectId):
                winner_data[key] = str(value)

        # Clear the winners_collection
        winners_collection.delete_many({})

        # Insert the winner_data
        winners_collection.insert_one(winner_data)

        # Convert winner_data ObjectId to string for JSON serialization
        winner_data['_id'] = str(winner_data['_id'])

        return jsonify({'success': True, 'winner': winner_data}), 200

    except Exception as e:
        print(f"Error selecting winner: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f"Error selecting winner: {e}"}), 500
"""Decide Winner End"""

"""results"""
@app.route('/results', methods=['GET'])
def results():
    # Fetch winner details from MongoDB
    winners_list = list(winners_collection.find())

    return render_template('results.html', winners_list=winners_list)


"""results end"""

@app.route('/customer_logout')
def customer_logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect(url_for('customer_login')) 



"""CUSTOMER LOGIN END"""


if __name__ == '__main__':
    app.run(debug=True)