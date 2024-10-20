from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ubicación fija para la base de datos (carpeta actual del proyecto)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'users.db')

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db = SQLAlchemy(app)

# Definición del modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.String(10), nullable=False)
    terms_accepted = db.Column(db.Boolean, nullable=False)

# Crear las tablas en la base de datos si no existen
with app.app_context():
    db.create_all()

# Ruta principal que redirige al login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Ruta para el login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user_email'] = user.email
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birthdate = request.form['birthdate']
        email = request.form['email']
        password = request.form['password']
        terms_accepted = request.form.get('terms')

        if not terms_accepted:
            flash('Debes aceptar los términos de privacidad.')
            return redirect(url_for('signup'))

        user = User.query.filter_by(email=email).first()

        if user:
            flash('El correo ya está registrado')
        else:
            new_user = User(first_name=first_name, last_name=last_name, birthdate=birthdate,
                            email=email, password=password, terms_accepted=True)
            db.session.add(new_user)
            db.session.commit()
            flash('Cuenta creada exitosamente. Ahora puedes iniciar sesión.')
            return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/dashboard')
def dashboard():
    # Obtener el nombre del usuario desde la sesión o la base de datos
    if 'user_email' in session:
        # Suponiendo que el nombre del usuario está almacenado en la base de datos
        user = User.query.filter_by(email=session['user_email']).first()
        if user:
            user_name = user.first_name  # O user.nombre si el campo se llama así en tu modelo
        else:
            user_name = 'Usuario'
    else:
        return redirect(url_for('login'))

    return render_template('dashboard.html', user_name=user_name)


@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Has cerrado sesión')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
