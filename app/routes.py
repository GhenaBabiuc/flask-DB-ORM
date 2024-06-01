from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from functools import wraps
from app import app, db, bcrypt
from app.models import User, Spectacol, Rezervare
from datetime import datetime

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    spectacole = Spectacol.query.all()
    return render_template('index.html', spectacole=spectacole)

@app.route('/add_show', methods=['GET', 'POST'])
@login_required
@admin_required
def adauga_spectacol():
    if request.method == 'POST':
        nume = request.form['nume']
        data_ora = datetime.strptime(request.form['data_ora'], '%Y-%m-%dT%H:%M')
        locuri_disponibile = request.form['locuri_disponibile']

        if not nume or not data_ora or not locuri_disponibile:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('adauga_spectacol'))

        spectacol = Spectacol(nume=nume, data_ora=data_ora, locuri_disponibile=int(locuri_disponibile))
        db.session.add(spectacol)
        db.session.commit()

        flash('Spectacol adăugat cu succes', 'success')
        return redirect(url_for('index'))
    return render_template('add_show.html')

@app.route('/delete_show/<int:id>', methods=['POST'])
@login_required
@admin_required
def sterge_spectacol(id):
    spectacol = Spectacol.query.get_or_404(id)
    db.session.delete(spectacol)
    db.session.commit()

    flash('Spectacol șters cu succes', 'success')
    return redirect(url_for('index'))

@app.route('/shows', methods=['GET'])
def listeaza_spectacole():
    spectacole = Spectacol.query.filter(Spectacol.data_ora >= datetime.now()).all()
    return render_template('shows.html', spectacole=spectacole)

@app.route('/make_reservation/<int:spectacol_id>', methods=['GET', 'POST'])
@login_required
def fa_rezervare(spectacol_id):
    spectacol = Spectacol.query.get_or_404(spectacol_id)
    if request.method == 'POST':
        locuri_rezervate = int(request.form['locuri_rezervate'])

        if spectacol.locuri_disponibile < locuri_rezervate:
            flash('Locuri insuficiente disponibile', 'error')
            return redirect(url_for('fa_rezervare', spectacol_id=spectacol_id))

        spectacol.locuri_disponibile -= locuri_rezervate
        rezervare = Rezervare(spectacol_id=spectacol_id, user_id=current_user.id, locuri_rezervate=locuri_rezervate)
        db.session.add(rezervare)
        db.session.commit()

        flash('Rezervare realizată cu succes', 'success')
        return redirect(url_for('index'))
    return render_template('make_reservation.html', spectacol=spectacol)

@app.route('/cancel_reservation/<int:id>', methods=['POST'])
@login_required
def anuleaza_rezervare(id):
    rezervare = Rezervare.query.get_or_404(id)
    if rezervare.user_id != current_user.id and current_user.role != 'admin':
        flash('Nu aveți permisiunea să anulați această rezervare.', 'error')
        return redirect(url_for('vizualizeaza_rezervari'))

    spectacol = Spectacol.query.get_or_404(rezervare.spectacol_id)
    spectacol.locuri_disponibile += rezervare.locuri_rezervate

    db.session.delete(rezervare)
    db.session.commit()

    flash('Rezervare anulată cu succes', 'success')
    return redirect(url_for('vizualizeaza_rezervari'))

@app.route('/reservations', methods=['GET'])
@login_required
def vizualizeaza_rezervari():
    rezervari = Rezervare.query.filter_by(user_id=current_user.id).all()
    return render_template('reservations.html', rezervari=rezervari)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, role='user')
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/register_admin', methods=['GET', 'POST'])
@login_required
@admin_required
def register_admin():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, role='admin')
        db.session.add(user)
        db.session.commit()
        flash('Admin account has been created!', 'success')
        return redirect(url_for('index'))
    return render_template('register_admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
