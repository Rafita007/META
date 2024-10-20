import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ruta de la base de datos
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'users.db')

# Configurar la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db = SQLAlchemy(app)


# Definir el modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.String(10), nullable=False)
    tarjetas = db.relationship('Tarjeta', backref='user', lazy=True)


# Definir el modelo de tarjeta
class Tarjeta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Crear la base de datos y las tablas si no existen
if not os.path.exists(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Crea la carpeta instance si no existe
    with app.app_context():
        db.create_all()


# Ruta para mostrar el dashboard (solo si el usuario está logueado)
@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user_email = session['user_email']
    user = User.query.filter_by(email=user_email).first()

    # Verificar si el usuario existe
    if user is None:
        flash('Usuario no encontrado, por favor inicia sesión nuevamente.')
        return redirect(url_for('login'))

    # Obtener las tarjetas asociadas a este usuario
    tarjetas = Tarjeta.query.filter_by(user_id=user.id).all()

    # Si el usuario no tiene tarjetas, agregar las tarjetas por defecto
    if not tarjetas:
        tarjetas_por_defecto = [
            Tarjeta(nombre="Tarjeta Santander", user_id=user.id),
            Tarjeta(nombre="Tarjeta BBVA", user_id=user.id),
            Tarjeta(nombre="Tarjeta FONDEA", user_id=user.id)
        ]
        db.session.bulk_save_objects(tarjetas_por_defecto)
        db.session.commit()
        tarjetas = Tarjeta.query.filter_by(user_id=user.id).all()  # Volver a cargar las tarjetas

    # Depuración: Imprimir las tarjetas encontradas para el usuario
    print(f"Tarjetas para el usuario {user.first_name} (ID: {user.id}):")
    for tarjeta in tarjetas:
        print(f"- Tarjeta ID: {tarjeta.id}, Nombre: {tarjeta.nombre}")

    return render_template('dashboard.html', tarjetas=tarjetas, user_name=user.first_name)

# Ruta para eliminar una tarjeta
@app.route('/delete_card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    # Mostrar el card_id que estamos intentando eliminar
    print(f"Intentando eliminar tarjeta con ID: {card_id}")

    # Obtener el user_id de la sesión
    user_id = session.get('user_id')
    print(f"User ID en sesión: {user_id}")

    # Usar filter_by para obtener la tarjeta en lugar de get()
    tarjeta = Tarjeta.query.filter_by(id=card_id).first()

    # Verificar si la tarjeta fue encontrada
    if not tarjeta:
        print(f"Tarjeta con ID {card_id} no fue encontrada")
        return jsonify({"status": "error", "message": "Tarjeta no encontrada"})

    # Verificar si la tarjeta pertenece al usuario logueado
    print(f"Tarjeta encontrada. Perteneciente al usuario con ID: {tarjeta.user_id}")
    if tarjeta.user_id != user_id:
        print("La tarjeta no pertenece al usuario logueado")
        return jsonify({"status": "error", "message": "No autorizado para eliminar esta tarjeta"})

    try:
        # Eliminar la tarjeta
        db.session.delete(tarjeta)
        db.session.commit()
        print(f"Tarjeta con ID {card_id} eliminada correctamente")
        return jsonify({"status": "success"})
    except Exception as e:
        # Capturar cualquier error y mostrarlo
        print(f"Error al eliminar la tarjeta: {e}")
        return jsonify({"status": "error", "message": "Error al eliminar la tarjeta"})


# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user_email'] = user.email
            session['user_id'] = user.id
            session['user_name'] = user.first_name
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos')

    return render_template('login.html')


# Ruta para registrarse
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birthdate = request.form['birthdate']

        # Verificar si el email ya está registrado
        user_existente = User.query.filter_by(email=email).first()
        if user_existente:
            flash('El correo ya está registrado')
        else:
            nuevo_usuario = User(email=email, password=password, first_name=first_name, last_name=last_name,
                                 birthdate=birthdate)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Cuenta creada exitosamente. Ahora puedes iniciar sesión.')
            return redirect(url_for('login'))

    return render_template('signup.html')


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    session.pop('user_name', None)
    session.pop('user_id', None)
    flash('Has cerrado sesión')
    return redirect(url_for('login'))


# Ruta para agregar una tarjeta
@app.route('/add_card', methods=['POST'])
def add_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nombre_tarjeta = request.form['nombre_tarjeta']
    nueva_tarjeta = Tarjeta(nombre=nombre_tarjeta, user_id=session['user_id'])
    db.session.add(nueva_tarjeta)
    db.session.commit()

    return redirect(url_for('dashboard'))


# Ruta principal (redirigir a login o dashboard según la sesión)
@app.route('/')
def index():
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
