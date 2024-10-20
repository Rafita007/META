import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import subprocess
from pdf import extraer_texto_pdf, detectar_fechas, detectar_descripciones, extraer_datos_financieros

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

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'response': 'Por favor, inicia sesión para acceder a tu estado de cuenta.'})

    tarjeta = Tarjeta.query.filter_by(user_id=user_id, nombre="Estado de Cuenta").first()
    if not tarjeta:
        return jsonify({'response': 'Lo siento, no tienes actualmente datos de tu estado de cuenta.'})

    mi_ultimo_estado_de_cuenta = {
        'fecha': '30/07/2024',
        'descripcion': 'Depósito de DAVID SAAVEDRA PONCE',
        'cargos': 0.00,
        'abonos': 70.00,
        'saldo': 74.96
    }

    if prompt.lower() == 'calcula mi último estado de cuenta':
        if not mi_ultimo_estado_de_cuenta:
            return jsonify({'response': 'Lo siento, no tengo acceso a tu último estado de cuenta.'})

        fecha = mi_ultimo_estado_de_cuenta['fecha']
        descripcion = mi_ultimo_estado_de_cuenta['descripcion']
        cargos = f"{mi_ultimo_estado_de_cuenta['cargos']:.2f}"
        abonos = f"{mi_ultimo_estado_de_cuenta['abonos']:.2f}"
        saldo = f"{mi_ultimo_estado_de_cuenta['saldo']:.2f}"

        # Generar la tabla y almacenarla en la sesión
        tabla_estado_cuenta = f"""
        Fecha: {fecha}, 
        Descripción: {descripcion}, 
        Cargos: {cargos}, 
        Abonos: {abonos}, 
        Saldo: {saldo}
        """
        session['tabla_estado_cuenta'] = tabla_estado_cuenta

        llama_prompt = f"""
        Oye, te voy a pasar una tabla y necesito que por favor me hagas categorías, 
        una de gastos recurrentes, gastos casuales, ingresos casuales e ingresos recurrentes. 
        Aquí está la tabla: {tabla_estado_cuenta}
        """

        # Ejecutar ollama con el prompt generado
        result = subprocess.run(
            ['ollama', 'run', 'llama3.2'],
            input=llama_prompt,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            response = result.stdout
            response = response.replace("failed to get console mode for stdout: Controlador no válido.\n", "")
            response = response.replace("failed to get console mode for stderr: Controlador no válido.\n", "")
        else:
            response = f"Error al ejecutar LLaMA. stdout: {result.stdout}, stderr: {result.stderr}"

        return jsonify({'response': response})

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

    # Aquí vamos a añadir la lógica para comprobar si hay un estado de cuenta y extraer los datos
    # Esto es una simulación, puedes ajustar cómo los datos son recuperados
    # Supongamos que tenemos una variable 'datos_estado_cuenta' con la información extraída del PDF
    datos_estado_cuenta = None

    # Aquí debería haber la lógica que obtiene el estado de cuenta del PDF procesado
    # En este ejemplo, asumimos que la variable ya está generada desde el proceso anterior
    if tarjeta.nombre == "Estado de Cuenta":
        # Aquí podemos agregar la lógica para obtener los datos del estado de cuenta
        # por ejemplo, de una base de datos o de la variable que contiene los datos.
        texto_pdf = extraer_texto_pdf(os.path.join(app.config['UPLOAD_FOLDER'], 'estado_cuenta.pdf'))  # ruta del PDF subido
        fechas = detectar_fechas(texto_pdf)
        descripciones = detectar_descripciones(texto_pdf)
        cargos, abonos, saldos = extraer_datos_financieros(texto_pdf)

        # Crear una cadena o lista de los datos del estado de cuenta
        datos_estado_cuenta = [
            {
                "Fecha": fechas[i],
                "Descripción": descripciones[i],
                "Cargos": cargos[i],
                "Abonos": abonos[i],
                "Saldos": saldos[i]
            }
            for i in range(len(fechas))
        ]

    # Verificar si hay datos del estado de cuenta o si no existen
    if datos_estado_cuenta:
        # Pasar los datos al template
        return render_template('detalles_estado_cuenta.html', tarjeta=tarjeta, datos_estado_cuenta=datos_estado_cuenta)
    else:
        flash("No hay datos disponibles para este estado de cuenta.")
        return redirect(url_for('dashboard'))




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
@app.route('/login', methods=['GET', 'POST'])
def login_page():
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

            # Extraer texto del PDF y procesarlo usando las funciones de pdf.py
            texto_pdf = extraer_texto_pdf(file_path)
            fechas = detectar_fechas(texto_pdf)
            descripciones = detectar_descripciones(texto_pdf)
            cargos, abonos, saldos = extraer_datos_financieros(texto_pdf)

            # Crear una sola cadena con los datos extraídos
            longitud_maxima = max(len(cargos), len(abonos), len(saldos))
            cargos += [None] * (longitud_maxima - len(cargos))
            abonos += [None] * (longitud_maxima - len(abonos))
            saldos += [None] * (longitud_maxima - len(saldos))

            datos_concatenados = "; ".join(
                f"Fecha: {fechas[i]}, Descripción: {descripciones[i]}, Cargos: {cargos[i]}, Abonos: {abonos[i]}, Saldos: {saldos[i]}"
                for i in range(len(fechas))
            )

            # Guardar la cadena en un archivo .txt
            txt_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'estado_cuenta.txt')
            with open(txt_file_path, 'w') as txt_file:
                txt_file.write(datos_concatenados)

            # Crear un nuevo registro de estado de cuenta en la base de datos
            nueva_tarjeta = Tarjeta(nombre="Estado de Cuenta", user_id=session['user_id'])
            db.session.add(nueva_tarjeta)
            db.session.commit()

            flash(f"Estado de cuenta procesado y guardado en 'estado_cuenta.txt'")

        else:
            flash("Por favor, sube un archivo PDF válido.")

        return redirect(url_for('dashboard'))

    return '''
    <form method="POST" enctype="multipart/form-data">
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
