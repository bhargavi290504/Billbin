from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from flask_migrate import Migrate
from datetime import datetime, date
import datetime as dt
import os

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from notify_utils import send_notification  


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key') 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
REDIRECT_URI = "http://127.0.0.1:5000/callback"

def authorize():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    session['state'] = state
    return redirect(auth_url)

@app.route('/callback')
def callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['credentials'] = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }
    return redirect(url_for('dashboard'))

def get_calendar_events():
    if 'credentials' not in session:
        return []
    creds = Credentials(**session['credentials'])
    service = build('calendar', 'v3', credentials=creds)
    now = dt.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    return events

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(80))
    limit = db.Column(db.Integer, default=0)
    min_balance = db.Column(db.Integer, default=0)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer)
    purpose = db.Column(db.String(200))
    date = db.Column(db.Date)
    user = db.relationship('User', backref=db.backref('bills', lazy=True))

# Auth
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id')
    return redirect(url_for('index')) 
@app.route('/filter_bills', methods=['POST']) 
@login_required
def filter_bills():
    user = User.query.get(session['user_id'])
    filter_date = request.form['filter_date']

    filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()

    filtered_bills = Bill.query.filter_by(user_id=user.id, date=filter_date_obj).all()

    spent = sum(b.amount for b in filtered_bills)

    remaining = user.limit - spent
    return render_template('dashboard.html', 
                           limit=user.limit, 
                           min_balance=user.min_balance, 
                           spent=spent,  
                           remaining=remaining,  
                           bills=filtered_bills, 
                           filtered_bills=filtered_bills,
                           filter_date=filter_date)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user = User.query.get(session['user_id'])

    today = date.today()
    bills = Bill.query.filter_by(user_id=user.id).filter(
        db.extract('month', Bill.date) == today.month,
        db.extract('year', Bill.date) == today.year
    ).all()

   
    spent = sum(b.amount for b in bills)
    remaining = user.limit - spent
    if remaining < user.min_balance:
        send_notification(user.email, remaining)
   
    filtered_bills = []
    filter_date = None

    if request.method == 'POST':
        try:
            if 'limit' in request.form:
                new_limit = int(request.form['limit'])
                
                user.limit += new_limit 
                user.min_balance = int(request.form['min_balance'])
                db.session.commit()
                flash('Limits updated successfully!')

            elif 'voice' in request.form:
                from voice_utils import extract_from_voice
                purpose, amount = extract_from_voice()
                db.session.add(Bill(user_id=user.id, amount=amount, purpose=purpose, date=today))
                db.session.commit()
                flash('Bill added via voice!')

            elif 'bill_img' in request.files:
                from ocr_utils import extract_from_image
                purpose, amount = extract_from_image(request.files['bill_img'])
                db.session.add(Bill(user_id=user.id, amount=amount, purpose=purpose, date=today))
                db.session.commit()
                flash('Bill added from image!')

            elif 'add_manual' in request.form:
                bill_date = datetime.strptime(request.form['bill_date'], '%Y-%m-%d').date()
                purpose = request.form['purpose']
                amount = int(request.form['amount'])
                db.session.add(Bill(user_id=user.id, amount=amount, purpose=purpose, date=bill_date))
                db.session.commit()
                flash('Bill added manually!')

            elif 'filter' in request.form:  
                filter_date = request.form['filter_date']
                filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
                filtered_bills = Bill.query.filter_by(user_id=user.id, date=filter_date_obj).all()
            spent = sum(b.amount for b in bills) 
            remaining = user.limit - spent

        except Exception as e:
            flash(f"Error processing form: {e}") 
        

        return redirect(url_for('dashboard'))

    return render_template('dashboard.html',
                           limit=user.limit,
                           min_balance=user.min_balance,
                           bills=bills,
                           spent=spent,
                           remaining=remaining,
                           filtered_bills=filtered_bills,
                           filter_date=filter_date)

  
  
@app.route('/bills_json')
@login_required
def bills_json():
    user = User.query.get(session['user_id'])
    bills = Bill.query.filter_by(user_id=user.id).all()
    bill_events = [
        {
            'title': f"{bill.purpose}: ₹{bill.amount}",
            'start': bill.date.isoformat() if bill.date else ''
        }
        for bill in bills if bill.date
    ]
    return jsonify(bill_events)

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))  # Use Render's PORT or default to 5000
    app.run(host='0.0.0.0', port=port, debug=False) 

