from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Website(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    domain = db.Column(db.String(255))
    waf_enabled = db.Column(db.Boolean, default=True)

# --- Routes ---
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    websites = Website.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', websites=websites)

@app.route('/add-website', methods=['GET', 'POST'])
def add_website():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        domain = request.form['domain']
        website = Website(user_id=session['user_id'], domain=domain)
        db.session.add(website)
        db.session.commit()
        flash('Website added successfully')
        return redirect(url_for('dashboard'))
    return render_template('add_website.html')

@app.route('/website/<int:website_id>')
def website_detail(website_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    website = Website.query.filter_by(id=website_id, user_id=session['user_id']).first()
    if not website:
        flash('Website not found or unauthorized')
        return redirect(url_for('dashboard'))
    return render_template('website_detail.html', website=website)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5001,debug=True)
