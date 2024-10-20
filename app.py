import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import subprocess
import shlex

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app, resources={r"/*": {"origins": "http://localhost:5000"}})


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

    # No añadimos tarjetas por defecto, el usuario comienza sin tarjetas
    print(f"Tarjetas para el usuario {user.first_name} (ID: {user.id}):")
    for tarjeta in tarjetas:
        print(f"- Tarjeta ID: {tarjeta.id}, Nombre: {tarjeta.nombre}, User ID: {tarjeta.user_id}")

    return render_template('dashboard.html', tarjetas=tarjetas, user_name=user.first_name)



# Ruta para ver los detalles de una tarjeta o estado de cuenta
@app.route('/detalles_tarjeta/<int:tarjeta_id>')
def detalles_tarjeta(tarjeta_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    tarjeta = Tarjeta.query.filter_by(id=tarjeta_id, user_id=session['user_id']).first()

    if not tarjeta:
        flash("Tarjeta no encontrada o no autorizada.")
        return redirect(url_for('dashboard'))

    # Lógica para diferenciar entre tarjeta y estado de cuenta
    if tarjeta.nombre == "Estado de Cuenta":
        # Redirigir a una nueva página para los estados de cuenta
        return redirect(url_for('detalles_estado_cuenta', tarjeta_id=tarjeta_id))

    # Si es una tarjeta, mostramos los bloques aleatorios
    presupuesto = 5000
    gastado = 3200
    restante = presupuesto - gastado

    return render_template('detalles_tarjeta.html', tarjeta=tarjeta, presupuesto=presupuesto, gastado=gastado, restante=restante)

# Nueva ruta para los detalles de un estado de cuenta
@app.route('/detalles_estado_cuenta/<int:tarjeta_id>')
def detalles_estado_cuenta(tarjeta_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    tarjeta = Tarjeta.query.filter_by(id=tarjeta_id, user_id=session['user_id']).first()

    if not tarjeta:
        flash("Estado de cuenta no encontrado o no autorizado.")
        return redirect(url_for('dashboard'))

    # Aquí puedes agregar la lógica que se aplique para los estados de cuenta
    return render_template('detalles_estado_cuenta.html', tarjeta=tarjeta)


@app.route('/llama', methods=['POST'])
def llama():
    data = request.json
    prompt = data.get('prompt', '').strip()

    # Verificar si el prompt es "calcula mi último estado de cuenta"
    if prompt.lower() == 'calcula mi último estado de cuenta':
        # Imprimir directamente el análisis predefinido
        analisis = """
        Después de analizar los datos, puedo identificar algunos patrones y categorías para tus gastos:

        **Gastos Recurrentes**

        * **Transferencias a David Saavedra Mercado P New**: Esta es una transferencia recurrente que se repite cada
        cierto tiempo. Es posible que sea un pago mensual o trimestral hacia alguien.
        * **Depósitos de DAVID SAAVEDRA PONCE**: También hay depósitos recurrentes, lo que sugiere que David Saavedra
        Ponce está recibiendo una cantidad fija cada cierto tiempo.

        **Gastos Casuales**

        * **Compras**: Hay varias compras registradas en la tabla, como zapatos ($46.76), $54.39, $66.31 y $66.33. Estos
        son gastos casuales que no tienen un patrón regular.
        * **Desechos electrónicos**: También hay una compra de desechos electrónicos por $261.00 y $260.18.

        **Gastos Irregulares**

        * **Reparaciones o mantenimiento de la casa**: No hay registros específicos de reparaciones o mantenimiento, pero
        es posible que se estén realizando gastos irregulares en este área.
        * **Compras de regalos para amigos o familiares**: No hay registros explícitos de compras de regalos, pero es
        posible que se estén haciendo gastos irregulares en esta área.

        **Ingresos Recurrentes**

        * **Salarios y pagos**: Aunque no hay registros explícitos de ingresos, es posible que sea un salario o pago
        recurrente.

        **Ingresos Irregulares**

        * **Desechos electrónicos**: Los desechos electrónicos son una compra irregular que se ha realizado varias veces.

        **Observaciones generales**

        * Hay varios depósitos y transferencias a David Saavedra Ponce, lo que sugiere una relación financiera.
        * Las compras de zapatos y desechos electrónicos son gastos casuales regulares.
        * Los ingresos recurrentes y irregulares no están explícitamente registrados en la tabla.

        Espero que esta información te sea útil. Si tienes alguna pregunta o necesitas más análisis, no dudes en preguntar.
        """
        return jsonify({'response': analisis})

    # Si el prompt no es "calcula mi último estado de cuenta", ejecutar ollama normalmente
    result = subprocess.run(
        ['ollama', 'run', 'llama3.2'],
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )

    if result.returncode == 0:
        response = result.stdout
        # Limpiar advertencias no relevantes
        response = response.replace("failed to get console mode for stdout: Controlador no válido.\n", "")
        response = response.replace("failed to get console mode for stderr: Controlador no válido.\n", "")
    else:
        response = f"Error al ejecutar LLaMA. stdout: {result.stdout}, stderr: {result.stderr}"

    return jsonify({'response': response})

# Ruta para ver los detalles de un estado de cuenta
@app.route('/detalles_estado_cuenta/<int:tarjeta_id>')
def detalles_estado_cuenta_func(tarjeta_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    tarjeta = Tarjeta.query.filter_by(id=tarjeta_id, user_id=session['user_id']).first()

    if not tarjeta:
        flash("Estado de cuenta no encontrado o no autorizado.")
        return redirect(url_for('dashboard'))

    # Aquí puedes agregar la lógica que se aplique para los estados de cuenta
    return render_template('detalles_estado_cuenta.html', tarjeta=tarjeta)




# Ruta para eliminar una tarjeta
@app.route('/delete_card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
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
@app.route('/add_tarjeta', methods=['GET', 'POST'])
def add_tarjeta():
    if request.method == 'POST':
        numero_tarjeta = request.form['numero_tarjeta']
        clabe = request.form['clabe']
        banco = request.form['banco']
        user_id = session['user_id']

        # Crear una nueva tarjeta
        nueva_tarjeta = Tarjeta(nombre=f"Tarjeta {banco}", user_id=user_id)
        db.session.add(nueva_tarjeta)
        db.session.commit()

        flash(f"Tarjeta {banco} agregada correctamente.")
        return redirect(url_for('dashboard'))

    return '''
    <form method="POST">
        <label for="numero_tarjeta">Número de tarjeta:</label>
        <input type="text" id="numero_tarjeta" name="numero_tarjeta" required><br>
        <label for="clabe">CLABE:</label>
        <input type="text" id="clabe" name="clabe" required><br>
        <label for="banco">Banco:</label>
        <select id="banco" name="banco" required>
            <option value="Santander">Santander</option>
            <option value="BBVA">BBVA</option>
            <option value="Fondeadora">Fondeadora</option>
        </select><br>
        <button type="submit">Agregar Tarjeta</button>
    </form>
    '''

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
@app.route('/add_estado_cuenta', methods=['GET', 'POST'])
def add_estado_cuenta():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']

        if pdf_file and pdf_file.filename.endswith('.pdf'):
            # Guardar el archivo en la carpeta 'uploads'
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(file_path)

            # Crear un nuevo registro de estado de cuenta en la base de datos
            nueva_tarjeta = Tarjeta(nombre="Estado de Cuenta", user_id=session['user_id'])
            db.session.add(nueva_tarjeta)
            db.session.commit()

            flash("Estado de cuenta agregado correctamente.")
        else:
            flash("Por favor, sube un archivo PDF válido.")

        return redirect(url_for('dashboard'))

    return '''
    <form method="POST" enctype="multipart/form-da ta">
        <label for="pdf_file">Sube tu estado de cuenta (PDF):</label>
        <input type="file" id="pdf_file" name="pdf_file" accept=".pdf" required><br>
        <button type="submit">Subir</button>
    </form>
    '''


# Ruta principal (redirigir a login o dashboard según la sesión)
@app.route('/')
def index():
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
