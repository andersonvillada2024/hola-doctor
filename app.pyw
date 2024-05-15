from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta, date
from flask import session
from flask import jsonify
from werkzeug.security import generate_password_hash,check_password_hash
from contextlib import closing
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from flask import send_file
from io import BytesIO
import os
import csv
from werkzeug.utils import secure_filename
# import matplotlib.pyplot as plt



app = Flask(__name__)
app.secret_key = 'Admin12345*+'


#--------------------------INICIA SESSION LOGIN----------------------------

def connect_db():
    conn = sqlite3.connect('database.db')
    return conn

# The above code is a Python Flask application that implements a simple authentication system for different user roles (administrative, apprentice) with session management. Here is a breakdown of the main functionalities:

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role, redirect_route, first_login = authenticate(username, password)
        if role:
            session['username'] = username
            session['role'] = role
            if first_login:
                flash('Es tu primera vez iniciando sesión. Por favor, cambia tu contraseña.')
                return redirect(url_for('change_password'))
            else:
                return redirect(url_for(redirect_route))
        else:
            error = 'Credenciales inválidas. Inténtalo de nuevo.'
            return render_template('login.html', error=error)
    return render_template('login.html')

# Función para autenticar al usuario
def authenticate(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role, first_login FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        role = user[0]  # Obtiene el rol del usuario
        first_login = user[1]  # Obtiene el estado de primer inicio de sesión
       
        if role == 'administrativo':
            return role, 'admin', first_login
        elif role == 'aprendiz':
            return role, 'aprendices', first_login
    else:
        return None, None, None

# Ruta para cambiar la contraseña
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' in session:
        if request.method == 'POST':
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            if new_password == confirm_password:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password=?, first_login=0 WHERE username=?", (new_password, session['username']))
                conn.commit()
                conn.close()
                flash('Contraseña cambiada exitosamente.')
                return redirect(url_for('login'))
            else:
                error = 'Las contraseñas no coinciden. Inténtalo de nuevo.'
                return render_template('change_password.html', error=error)
        return render_template('change_password.html')
    return redirect(url_for('login'))

# Ruta para el panel de control de los médicos
@app.route('/index')
def index():

    return render_template('index.html')

@app.route('/manualmedicos')
def manualmedicos():
    return render_template('manualmedicos.html')

# Ruta para el panel de control de los administrativos
@app.route('/admin')
def admin():
    if 'username' in session and session['role'] == 'administrativo':
        return render_template('admin.html', username=session['username'])
    return redirect(url_for('login'))

# Ruta para el panel de control de los aprendices
@app.route('/aprendices')
def aprendices():
    if 'username' in session and session['role'] == 'aprendiz':
        return render_template('aprendices.html', username=session['username'])
    return redirect(url_for('login'))

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

#---------------------FINALIZA SESSION LOGIN-------------------------------


@app.route('/')
def inicio():
    return render_template('index.html')

# --------------- INICIA REGISTRO DE PACIENTES---------------------

# The above code is a Python Flask application that serves as a backend for a web application related to patient registrations and data processing. Here is a breakdown of the main functionalities:

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/formulario1', methods=['POST'])
def procesar_formulario1():
    tipo_de_documento = request.form.get('tipo_de_documento')
    numero_de_documento = request.form.get('numero_de_documento')
    fecha_de_atencion = request.form.get('fecha_de_atencion')
    medico_quien_atiende = request.form.get('medico_quien_atiende')
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Obtener la fecha y hora actuales
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("INSERT INTO pacientes (tipo_de_documento, numero_de_documento, fecha_de_atencion, medico_quien_atiende, fecha_envio) VALUES (?, ?, ?, ?, ?)", (tipo_de_documento, numero_de_documento, fecha_de_atencion, medico_quien_atiende, fecha_envio,))
    conn.commit()
    conn.close()

    # Almacenar los valores de los campos del formulario en variables de sesión
    session['medico_quien_atiende'] = medico_quien_atiende
    session['fecha_de_atencion'] = fecha_de_atencion

    return redirect(url_for('registro'))

@app.route('/obtener_datos', methods=['GET'])
def obtener_datos():
    medico_quien_atiende = request.args.get('medico_quien_atiende')
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("SELECT tipo_de_documento, numero_de_documento, fecha_de_atencion,id FROM pacientes WHERE medico_quien_atiende = ? ORDER BY fecha_de_atencion DESC", (medico_quien_atiende,))
    data = c.fetchall()
    conn.close()
    return jsonify(data=data)

@app.route('/obtener_contadores/<medico_quien_atiende>')
def obtener_contadores(medico_quien_atiende):
    # Fecha actual
    fecha_envio = date.today()

    # Conexión a la base de datos
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()

    # Contador de datos ingresados hoy
    cursor.execute('SELECT COUNT(*) FROM pacientes WHERE DATE(fecha_envio) = ? AND medico_quien_atiende = ?', (fecha_envio, medico_quien_atiende))
    datos_hoy = cursor.fetchone()[0]

    # Contador de datos ingresados este mes
    inicio_mes = date(fecha_envio.year, fecha_envio.month, 1)
    cursor.execute('SELECT COUNT(*) FROM pacientes WHERE fecha_envio >= ? AND medico_quien_atiende = ?', (inicio_mes, medico_quien_atiende))
    datos_mes = cursor.fetchone()[0]

    conn.close()

    # Devuelve los contadores en formato JSON
    return jsonify({'datosHoy': datos_hoy, 'datosMes': datos_mes})

@app.route('/exportar_a_excel3')
def exportar_a_excel3():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('usuarios.db') as conn:
        df = pd.read_sql_query("SELECT * FROM pacientes", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='pacientes')
    writer._save()

    # Asegurarse de que el archivo Excel se cierre correctamente
    writer.close()

    # Crear un objeto de respuesta Flask que envía el archivo Excel
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='registro de ateciones.xlsx')

# ---------------------FINALIZA REGISTRO DE PACIENTES-----------------------------

# ------------------INICIA FORMULARIO REGISTRO DE ACTIVOS------------------------------
 
# The above code is a Python script that defines a Flask web application with routes for creating a database, rendering a form, processing form data, and exporting data to an Excel file. Here is a breakdown of the main functionalities:

def create_database():
    conn = sqlite3.connect('registro.db') 
    c = conn.cursor()

   
    c.execute('''CREATE TABLE IF NOT EXISTS registro
                 (nombres_completos text, cedula text, cargo text, numero_puesto text, extension text, ml_pc text, ml_pantalla text, mause text, guaya text, cargador text, diadema text, otros text, silla text, cubiculo text, descansapies text, observaciones text)''')

    conn.commit()
    conn.close()

create_database()


@app.route('/form')
def form():
    success_message = session.get('success_message', None)
    return render_template('form.html', success_message=success_message)
   

@app.route('/formulario2', methods=['POST'])
def procesar_formulario2():
    nombres_completos = request.form.get('nombres_completos')
    cedula = request.form.get('cedula')
    cargo = request.form.get('cargo')
    estado = request.form.get('estado')
    numero_puesto = request.form.get('numero_puesto')
    extension = request.form.get('extension')
    ml_pc = request.form.get('ml_pc')
    ml_pantalla = request.form.get('ml_pantalla')
    mause = "Sí" if request.form.get('mause')  == 'on' else "No"
    guaya = "Sí" if request.form.get('guaya')  == 'on' else "No"
    cargador = "Sí" if request.form.get('cargador')  == 'on' else "No"
    diadema =  "Sí" if request.form.get('diadema')  == 'on' else "No"
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    silla = "Sí" if request.form.get('silla')  == 'on' else "No"
    cubiculo = "Sí" if request.form.get('cubiculo')  == 'on' else "No"
    descansapies = "Sí" if request.form.get('descansapies')  == 'on' else "No"
    observaciones = request.form.get('observaciones')
    

    conn = sqlite3.connect('registro.db')
    c = conn.cursor()
    c.execute("INSERT INTO registro (nombres_completos, cedula, cargo,estado, numero_puesto, extension, ml_pc, ml_pantalla, mause, guaya, cargador, diadema, fecha_envio, silla, cubiculo, descansapies, observaciones) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (nombres_completos, cedula, cargo,estado, numero_puesto, extension, ml_pc, ml_pantalla, mause, guaya, cargador,diadema,fecha_envio,silla,cubiculo,descansapies,observaciones))
    conn.commit()
    conn.close()
    
    session['success_message'] = "Formulario enviado correctamente!"

    # Redirect back to the form
    return redirect(url_for('inicio'))

    # return 'formulario registrado con éxito!'

@app.route('/exportar_a_excel4')
def exportar_a_excel4():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('registro.db') as conn:
        df = pd.read_sql_query("SELECT * FROM registro", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='registro')
    writer._save()
    writer.close()
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='registro inventario.xlsx')

# -------------------FINALIZA FORMULARIO DE REGISTRO DE ACTIVOS------------------------------------

# ---------------------INICIA FORMULARIO DE SOPORTE-----------------------------------

# The above code is a Python Flask application that defines two routes:

@app.route('/formulario3', methods=['POST'])
def procesar_formulario3():
    nombre_medico = request.form.get('nombre_medico')
    tipo_de_inconveniente = request.form.get('tipo_de_inconveniente')
    numero_de_cubiculo = request.form.get('numero_de_cubiculo')
    observaciones = request.form.get('observaciones')
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Obtener la fecha y hora actuales
    estado_de_solicitud = 'en gestion'

    # Insertar los datos en la base de datos
    conn = sqlite3.connect('soporte.db')
    c = conn.cursor()
    c.execute("INSERT INTO solicitar_soporte (nombre_medico, tipo_de_inconveniente, numero_cubiculo, observaciones, fecha_envio,estado_de_solicitud) VALUES (?, ?, ?,?,?,?)", (nombre_medico, tipo_de_inconveniente, numero_de_cubiculo, observaciones, fecha_envio, estado_de_solicitud))
    conn.commit()
    conn.close()

    return redirect(url_for('inicio'))  # Ajusta el nombre de la función de ruta según tu aplicación

@app.route('/actualizar_estado2/<fecha_envio>', methods=['POST'])
def actualizar_estado2(fecha_envio):
    # Obtener los datos del formulario
    estado_de_solicitud = request.form.get('estado_de_solicitud')
    observaciones2 = request.form.get('observaciones2')

    # Construir la consulta SQL para actualizar
    query = "UPDATE solicitar_soporte SET estado_de_solicitud=?, observaciones2=? WHERE fecha_envio=?"

    # Ejecutar la consulta SQL
    conn = sqlite3.connect('soporte.db')
    cursor = conn.cursor()
    cursor.execute(query, (estado_de_solicitud, observaciones2, fecha_envio))
    conn.commit()
    conn.close()

    return redirect(url_for('estado_solicitud1')) 



# ------------------------FINALIZA FORMULARIO DE SOPORTE--------------------------------------------

#
# -------------------------INICIA FORMULARIO DE NOVEDADES---------------------------------------------
 
# The above code is a Python Flask application that handles a form submission for registering a new entry in a database table called "novedades" which stores information about novelties or updates. Here is a breakdown of the key functionalities:

@app.route('/registrar_novedad')
def registrar_novedad():
    return render_template('registrar_novedad.html')

@app.route('/formulario4', methods=['POST'])
def procesar_formulario4():
    # Extraer datos del formulario
    nombre = request.form['nombre']
    tipo_novedad = request.form['tipo_novedad']
    lider_a_cargo = request.form['lider_a_cargo']
    fecha_inicio = request.form['fecha_inicio']
    fecha_fin = request.form['fecha_fin']
    dias_novedad = request.form['dias_novedad']
    observaciones = request.form['observaciones']
    archivo_pdf = request.files['archivo_pdf']
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 

    # Leer el archivo PDF y convertirlo en bytes
    pdf_data = archivo_pdf.read()

    # Conectar a la base de datos y guardar los datos
    conn = sqlite3.connect('novedades.db')
    c = conn.cursor()
    c.execute("INSERT INTO novedades (nombre, tipo_novedad, lider_a_cargo, fecha_inicio, fecha_fin, dias_novedad, observaciones, archivo_pdf,fecha_envio) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)",
              (nombre, tipo_novedad, lider_a_cargo, fecha_inicio, fecha_fin, dias_novedad, observaciones, sqlite3.Binary(pdf_data),fecha_envio))
    conn.commit()
    conn.close()
    
    flash('El formulario se guardó correctamente.', 'success')

    return redirect(url_for('admin'))

@app.route('/exportar_a_excel2')
def exportar_a_excel2():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('novedades.db') as conn:
        df = pd.read_sql_query("SELECT * FROM novedades", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='novedades')
    writer._save()
    writer.close()
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='otras novedades.xlsx')

#-------------------------FINALIZA FORMULARIO NOVEDADES DE NOMINA------------------------------------------

#----------------------INICIA SESSION DE TALENTO HUMANO-------------------------

# The above code is a Python script using Flask framework to create a web application for managing human resources data. Here is a summary of what the code is doing:

# Función para establecer una conexión a la base de datos
def talento_humano_connection():
    return sqlite3.connect('talento_humano.db')

# Rutas relacionadas con la gestión del personal
@app.route('/personal')
def personal():
    with closing(talento_humano_connection()) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM personal")
        asignacionespersonal = cursor.fetchall()
        cursor.execute("SELECT NOMBRE_COMPLETO, cargo FROM personal")
        personal_info = cursor.fetchall()
    return render_template('personal.html', asignacionespersonal=asignacionespersonal, personal_info=personal_info)

@app.route('/update4', methods=['POST'])
def update4():
    # Obtener los datos del formulario
    data = {
        'NUMERO_CARPETA': request.form['NUMERO_CARPETA'],
        'NUMERO_CEDULA': request.form['NUMERO_CEDULA'],
        'CORREO_PERSONAL': request.form['CORREO_PERSONAL'],
        'CORREO_CORPORATIVO': request.form['CORREO_CORPORATIVO'],
        'NUMERO_CELULAR': request.form['NUMERO_CELULAR'],
        'NOMBRE_COMPLETO': request.form['NOMBRE_COMPLETO'],
        'CARGO': request.form['CARGO'],
        'PROCESO': request.form['PROCESO'],
        'FECHA_INGRESO': request.form['FECHA_INGRESO'],
        'ESTADO': request.form['ESTADO'],
        'FECHA_FIN': request.form['FECHA_FIN']
    }

    # Construir la consulta SQL para actualizar
    query = ("UPDATE personal SET NUMERO_CEDULA=?, CORREO_PERSONAL=?, CORREO_CORPORATIVO=?, "
             "NUMERO_CELULAR=?, NOMBRE_COMPLETO=?, CARGO=?, PROCESO=?, FECHA_INGRESO=?, "
             "ESTADO=?, FECHA_FIN=? WHERE NUMERO_CARPETA=?")

    # Preparar los parámetros para la consulta
    params = [data[key] for key in data] + [data['NUMERO_CARPETA']]

    with closing(talento_humano_connection()) as db:
        cursor = db.cursor()
        cursor.execute(query, params)
        db.commit()

    return redirect(url_for('personal'))

@app.route('/insert3', methods=['POST'])
def insert3():
    # Obtener los datos del formulario
    data = {
        'NUMERO_CARPETA': request.form.get('NUMERO_CARPETA'),
        'CORREO_PERSONAL': request.form.get('CORREO_PERSONAL'),
        'CORREO_CORPORATIVO': request.form.get('CORREO_CORPORATIVO'),
        'NUMERO_CELULAR': request.form.get('NUMERO_CELULAR'),
        'NOMBRE_COMPLETO': request.form.get('NOMBRE_COMPLETO'),
        'CARGO': request.form.get('CARGO'),
        'PROCESO': request.form.get('PROCESO'),
        'FECHA_INGRESO': request.form.get('FECHA_INGRESO'),
        'ESTADO': request.form.get('ESTADO'),
        'FECHA_FIN': request.form.get('FECHA_FIN')
    }
       
    # Construir la consulta SQL para insertar
    columns = ', '.join(data.keys())
    placeholders = ', '.join('?' for _ in data)
    query = f"INSERT INTO personal ({columns}) VALUES ({placeholders})"

    # Preparar los parámetros para la consulta
    params = list(data.values())

    with closing(talento_humano_connection()) as db:
        cursor = db.cursor()
        cursor.execute(query, params)
        db.commit()

    return redirect(url_for('personal'))

# Rutas relacionadas con la gestión de talento humano
@app.route('/talento_humano')
def talento_humano_page():
    with closing(talento_humano_connection()) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM actividades3 WHERE completada=0')
        actividades3 = c.fetchall()
    return render_template('talento_humano.html', actividades3=actividades3)

@app.route('/agregar3', methods=['POST'])
def agregar_actividad():
    actividad = request.form['actividad']
    with closing(talento_humano_connection()) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO actividades3 (actividad, completada) VALUES (?, 0)', (actividad,))
        conn.commit()
    return redirect(url_for('talento_humano_page'))

@app.route('/completar3/<int:id>')
def completar_actividad(id):
    with closing(talento_humano_connection()) as conn:
        c = conn.cursor()
        c.execute('UPDATE actividades3 SET completada=1 WHERE id=?', (id,))
        conn.commit()
    return redirect(url_for('talento_humano_page'))


@app.route('/exportar_a_excel6')
def exportar_a_excel6():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('talento_humano.db') as conn:
        df = pd.read_sql_query("SELECT * FROM personal", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='personal')
    writer._save()

    # Asegurarse de que el archivo Excel se cierre correctamente
    writer.close()

    # Crear un objeto de respuesta Flask que envía el archivo Excel
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='personal activo.xlsx')

#-----------------------FINALIZA SESSION DE TALENTO HUMANO-------------------------

#------------------------INICIA SESSION DE NOMINA----------------------------------

# The above code is a Python script that defines routes for a Flask web application. Here is a summary of what each function does:

DATABASE = 'agenda.db'

def create_db(database_name):
    conn = sqlite3.connect(database_name)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS actividades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, actividad TEXT, completada INTEGER)''')
    conn.commit()
    conn.close()

@app.route('/nomina')
def nomina():
    create_db(DATABASE)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM actividades WHERE completada=0')
    actividades = c.fetchall()
    conn.close()
    return render_template('nomina.html', actividades=actividades)

@app.route('/show_data_of_the_day')
def show_data_of_the_day():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pacientes ORDER BY fecha_envio DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('data_of_the_day.html', rows=rows)

@app.route('/plantilla_nomina')
def plantilla_nomina():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('novedades.db')
    c = conn.cursor()
    c.execute("SELECT * FROM novedades ORDER BY fecha_envio DESC")
    novedades = c.fetchall()
    conn.close()
    return render_template('plantilla_nomina.html', novedades=novedades)

@app.route('/agregar', methods=['POST'])
def agregar():
    actividad = request.form['actividad']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO actividades (actividad, completada) VALUES (?, 0)', (actividad,))
    conn.commit()
    conn.close()
    return redirect('/nomina')

@app.route('/completar/<int:id>')
def completar(id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('UPDATE actividades SET completada=1 WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/nomina')


#-------------------------FINALIZA SESSION DE NOMINA----------------------

#-------------------------INICIA SESSION DE OPERACIONES------------------------------------

# The above code is a Python Flask application that defines several routes for handling operations related to tasks and support requests. Here is a summary of what each route does:

DATA_BASE = 'operaciones.db'
@app.route('/operaciones')
def operaciones():
    create_db(DATA_BASE)
    conn = sqlite3.connect(DATA_BASE)
    c = conn.cursor()
    c.execute('SELECT * FROM actividades WHERE completada=0')
    actividades = c.fetchall()
    conn.close()
    return render_template('operaciones.html', actividades=actividades)

@app.route('/agregar1', methods=['POST'])
def agregar1():
    actividad = request.form['actividad']
    conn = sqlite3.connect(DATA_BASE)
    c = conn.cursor()
    c.execute('INSERT INTO actividades (actividad, completada) VALUES (?, 0)', (actividad,))
    conn.commit()
    conn.close()
    return redirect('/operaciones')

@app.route('/completar1/<int:id>')
def completar1(id):
    conn = sqlite3.connect(DATA_BASE)
    c = conn.cursor()
    c.execute('UPDATE actividades SET completada=1 WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect('/operaciones')

@app.route('/estado_solicitud')
def estado_solicitud1():
    conn = sqlite3.connect('soporte.db')
    c = conn.cursor()
    c.execute("SELECT * FROM solicitar_soporte ORDER BY fecha_envio DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('estado_solicitud.html', rows=rows)

@app.route('/soporte_medicos')
def soporte_medicos():
    conn = sqlite3.connect('soporte.db')
    c = conn.cursor()
    c.execute("SELECT * FROM solicitar_soporte ORDER BY fecha_envio DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('soporte_medicos.html', rows=rows)

#--------------------------inventario milenio-------------------------------------------------
# Función para establecer la conexión con la base de datos
def inventario_milenio_connection():
    return sqlite3.connect('registro.db')

# Ruta para mostrar el inventario
@app.route('/inventario_milenio')
def inventario_milenio():
    with inventario_milenio_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM inventario_milenio ORDER BY id DESC")
        rowi = c.fetchall()
    return render_template('inventario_milenio.html', rowsi=rowi)

# Ruta para procesar el formulario de inserción
@app.route('/formulario_inv', methods=['POST'])
def procesar_formulario_inv():
    serial = request.form.get('serial')
    descripcionserial = request.form.get('descripcionserial')
    descripcionlineal = request.form.get('descripcionlineal')
    tarifa = request.form.get('tarifa')
    facturable = request.form.get('facturable')
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
    estado = 'vigente'

    with inventario_milenio_connection() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO inventario_milenio (serial, descripcionserial, descripcionlineal, tarifa, facturable, fecha_envio, estado) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (serial, descripcionserial, descripcionlineal, tarifa, facturable, fecha_envio, estado))
        conn.commit()

    return redirect(url_for('inventario_milenio'))
@app.route('/updateinv', methods=['POST'])
def updateinv():
    # Obtener los datos del formulario
    id_ = request.form.get('id')
    estado = request.form.get('estado')
    observaciones = request.form.get('observaciones')

    # Construir la consulta SQL para actualizar
    query = "UPDATE inventario_milenio SET estado=?, observaciones=?, fecha_fin=? WHERE id=?"

    # Preparar los parámetros para la consulta
    params = (estado, observaciones, datetime.now(), id_)

    with closing(inventario_milenio_connection()) as db:
        cursor = db.cursor()
        cursor.execute(query, params)
        db.commit()

    return redirect(url_for('inventario_milenio'))

@app.route('/exportar_a_excelinv')
def exportar_a_excelinv():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('registro.db') as conn:
        df = pd.read_sql_query("SELECT * FROM inventario_milenio", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='inventario_milenio')
    writer._save()

    # Asegurarse de que el archivo Excel se cierre correctamente
    writer.close()

    # Crear un objeto de respuesta Flask que envía el archivo Excel
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='inventario_milenio.xlsx')
#-------------------------------------inventario-----------------------------------
# The above code is a Python script that defines a Flask web application with routes for displaying inventory information and updating records in a SQLite database. Here is a breakdown of the main components:
registro = 'registro.db'

# Función para establecer una conexión a la base de datos
def connect_db5():
    return sqlite3.connect(registro)

@app.route('/inventario')
def inventario():
    with closing(connect_db5()) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM registro")
        asignacionesinventario = cursor.fetchall()
        cursor.execute("SELECT numero_puesto FROM registro")
        inventario_info = cursor.fetchall()
    return render_template('inventario.html', asignacionesinventario=asignacionesinventario, inventario_info=inventario_info)

# Ruta para actualizar un registro en la base de datos+
@app.route('/update5', methods=['POST'])
def update5():
    nombres_completos = request.form.get('nombres_completos')
    cedula = request.form.get('cedula')
    cargo = request.form.get('cargo')
    estado = request.form.get('estado')
    numero_puesto = request.form.get('numero_puesto')
    extension = request.form.get('extension')
    ml_pc = request.form.get('ml_pc')
    ml_pantalla = request.form.get('ml_pantalla')
    mause =  request.form.get('mause') 
    guaya =  request.form.get('guaya')
    cargador = request.form.get('cargador') 
    diadema = request.form.get('diadema') 
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    silla =  request.form.get('silla') 
    cubiculo =  request.form.get('cubiculo') 
    descansapies = request.form.get('descansapies') 
    observaciones = request.form.get('observaciones')

    with closing(connect_db5()) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE registro SET nombres_completos=?, cedula=?, cargo=?,estado=?, extension=?, ml_pc=?, ml_pantalla=?, mause=?, guaya=?, cargador=?, diadema=?, fecha_envio=?, silla=?, cubiculo=?, descansapies=?, observaciones=? WHERE numero_puesto=?", 
               (nombres_completos, cedula, cargo,estado, extension, ml_pc, ml_pantalla, mause, guaya, cargador, diadema, fecha_envio, silla, cubiculo, descansapies, observaciones, numero_puesto))

        db.commit()

    return redirect(url_for('inventario'))

#-------------------------------LINEAS-----------------------------------
# # The above code is a Python script that defines a Flask web application with several routes for interacting with a SQLite database. Here is a summary of what the code is doing:

BASE = 'lineas.db'

# Función para establecer una conexión a la base de datos
def connect_db2():
    return sqlite3.connect(BASE)

# Ruta para mostrar los registros de la base de datos
@app.route('/lineas')
def lineas():
    with closing(connect_db2()) as db:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM asignaciones")
        asignaciones = cursor.fetchall()
        cursor.execute("SELECT nombre, cargo FROM personal")
        personal_info = cursor.fetchall()

        data = {
        'cantidad_total': [100, 120, 150, 180],
        'cantidad_ocupadas': [50, 60, 70, 90],
        'cantidad_disponible': [50, 60, 80, 90],
        'fecha': ['2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01']
    }
    df = pd.DataFrame(data)
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Graficar
    # plt.figure(figsize=(10, 6))

    # plt.plot(df['fecha'], df['cantidad_total'], marker='o', label='Total de líneas')
    # plt.plot(df['fecha'], df['cantidad_ocupadas'], marker='o', label='Líneas ocupadas')
    # plt.plot(df['fecha'], df['cantidad_disponible'], marker='o', label='Líneas disponibles')

    # plt.title('Estado de líneas')
    # plt.xlabel('Fecha')
    # plt.ylabel('Cantidad de líneas')
    # plt.legend()
    # plt.grid(True)
    # plt.xticks(rotation=45)

    # plt.tight_layout()
    # plt.savefig('static/lineas_plot.png')  # Guardar la imagen del gráfico
    
    return render_template('lineas.html', asignaciones=asignaciones, personal_info=personal_info)
    return send_file('static/lineas_plot.png', mimetype='image/png')

# Ruta para actualizar un registro en la base de datos
@app.route('/update', methods=['POST'])
def update():
    # Obtener los datos del formulario
    data = {
        'linea': request.form.get('linea'),
        'imei': request.form.get('imei'),
        'nombre': request.form.get('nombre'),
        'estado': request.form.get('estado'),
        'cedula': request.form.get('cedula'),
        'detalle_entrega': request.form.get('detalle_entrega'),
        'fecha_entrega': request.form.get('fecha_entrega'),
        'observacion': request.form.get('observacion'),
        'id': request.form.get('id')
    }

    # Filtrar los campos que no son None
    data_to_update = {k: v for k, v in data.items() if v is not None}

    # Construir la consulta SQL dinámicamente
    set_clause = ', '.join(f"{key}=?" for key in data_to_update.keys())
    where_clause = f"WHERE id=?"
    query = f"UPDATE asignaciones SET {set_clause} {where_clause}"

    # Preparar los parámetros para la consulta
    params = list(data_to_update.values()) + [data['id']]

    with closing(connect_db2()) as db:
        cursor = db.cursor()
        cursor.execute(query, params)
        db.commit()

    return redirect(url_for('lineas'))


# Función para insertar un nuevo registro en la base de datos
@app.route('/insert2', methods=['POST'])
def insert2():
    # Obtener los datos del formulario
    data = {
        'linea': request.form.get('linea'),
        'imei': request.form.get('imei'),
        'nombre': request.form.get('nombre'),
        'estado': request.form.get('estado'),
        'cedula': request.form.get('cedula'),
        'detalle_entrega': request.form.get('detalle_entrega'),
        'fecha_entrega': request.form.get('fecha_entrega'),
        'observacion': request.form.get('observacion')
    }

    # Construir la consulta SQL para insertar
    columns = ', '.join(data.keys())
    placeholders = ', '.join('?' for _ in data)
    query = f"INSERT INTO asignaciones ({columns}) VALUES ({placeholders})"

    # Preparar los parámetros para la consulta
    params = list(data.values())

    with closing(connect_db2()) as db:
        cursor = db.cursor()
        cursor.execute(query, params)
        db.commit()

    return redirect(url_for('lineas'))

@app.route('/plano')
def plano():
    return render_template('plano.html')


@app.route('/exportar_a_excel5')
def exportar_a_excel5():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('lineas.db') as conn:
        df = pd.read_sql_query("SELECT * FROM asignaciones", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='asignaciones')
    writer._save()

    # Asegurarse de que el archivo Excel se cierre correctamente
    writer.close()

    # Crear un objeto de respuesta Flask que envía el archivo Excel
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='asignacion de lineas.xlsx')





#--------------------------FINALIZA SESSION OPERACIONES----------------------------------


#---------------------INICIA SESSION PRACTICANTES-----------------------------
# The above code is a Python Flask application that manages activities for apprentices. Here is a breakdown of the main functionalities:

@app.route('/gestionar_actividades', methods=['GET', 'POST'])
def gestionar_actividades():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        fecha_asignacion = request.form['fecha_asignacion']
        fecha_vencimiento = request.form['fecha_vencimiento']
        conn = sqlite3.connect('actividades_aprendices.db')
        c = conn.cursor()
        c.execute("INSERT INTO actividades_aprendices (nombre, descripcion, fecha_asignacion, fecha_vencimiento) VALUES (?, ?, ?, ?)",
                 (nombre, descripcion, fecha_asignacion, fecha_vencimiento))
        conn.commit()
        conn.close()
        flash('Actividad creada exitosamente.')
        return redirect(url_for('gestionar_actividades'))
    else:
        conn = sqlite3.connect('actividades_aprendices.db')
        c = conn.cursor()
        c.execute("SELECT * FROM actividades_aprendices")
        actividades = c.fetchall()
        conn.close()
        return render_template('gestionar_actividades.html', actividades=actividades)

@app.route('/asignar_actividad/<int:actividad_id>', methods=['POST'])
def asignar_actividad(actividad_id):
    usuario_id = request.form['usuario_id']
    observaciones = request.form['observaciones']
    conn = sqlite3.connect('actividades_aprendices.db')
    c = conn.cursor()
    c.execute("INSERT INTO asignaciones_aprendices (usuario_id, actividad_id, observaciones) VALUES (?, ?, ?)",
              (usuario_id, actividad_id, observaciones))
    conn.commit()
    conn.close()
    flash('Actividad asignada exitosamente.')
    return redirect(url_for('gestionar_actividades'))

@app.route('/modificar_actividad/<int:asignacion_id>', methods=['POST'])
def modificar_actividad(asignacion_id):
    observaciones = request.form['observaciones']
    conn = sqlite3.connect('actividades_aprendices.db')
    c = conn.cursor()
    c.execute("UPDATE asignaciones_aprendices SET observaciones=? WHERE id=?", (observaciones, asignacion_id))
    conn.commit()
    conn.close()
    flash('Observaciones actualizadas exitosamente.')
    return redirect(url_for('aprendices'))



#-------------------------FINALIZA SESSION PRACTICANTES--------------------------
#--------------------------INICIA SESSION DE CONTABILIDAD------------------------
 
# The code provided is a Python Flask application that handles the registration and management of incapacity records. Here is a breakdown of the main functionalities:
@app.route('/registrar_incapacidad')
def registrar_incapacidad():
    return render_template('registrar_incapacidad.html')
 
@app.route('/formulario5', methods=['POST'])
def procesar_formulario5():
    # Extraer datos del formulario
    lider_a_cargo = request.form['lider_a_cargo']
    nombre = request.form['nombre']
    cedula = request.form['cedula']
    cargo = request.form['cargo']
    eps = request.form['eps']
    eg_transito = request.form['eg_transito']
    nro_incapacidad = request.form['nro_incapacidad']
    prorroga = request.form['prorroga']
    fecha_inicio = request.form['fecha_inicio']
    fecha_final = request.form['fecha_final']
    diagnostico = request.form['diagnostico']
    profesional = request.form['profesional']
    observaciones = request.form['observaciones']
    archivo_pdf = request.files['archivo_pdf']
    fecha_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 

    # Calcular la diferencia de días entre las fechas de inicio y final
    fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')-  timedelta(days=1)
    fecha_final_obj = datetime.strptime(fecha_final, '%Y-%m-%d')
    dias_novedad = (fecha_final_obj - fecha_inicio_obj).days

    # Leer el archivo PDF y convertirlo en bytes
    pdf_data = archivo_pdf.read()

    # Conectar a la base de datos y guardar los datos
    conn = sqlite3.connect('incapacidades.db')
    c = conn.cursor()
    c.execute("INSERT INTO incapacidad ( lider_a_cargo,nombre,cedula,cargo,eps,eg_transito,nro_incapacidad,prorroga, fecha_inicio, fecha_final, dias_novedad, dias_novedad, diagnostico, profesional, observaciones, archivo_pdf, fecha_envio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              ( lider_a_cargo, nombre, cedula, cargo, eps, eg_transito, nro_incapacidad, prorroga, fecha_inicio, fecha_final, dias_novedad, dias_novedad, diagnostico, profesional, observaciones, sqlite3.Binary(pdf_data), fecha_envio))
    conn.commit()
    conn.close()
    
    flash('El formulario se guardó correctamente.', 'success')

    return redirect(url_for('admin'))

@app.route('/plantilla_incapacidades')
def plantilla_incapacidades():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('incapacidades.db')
    c = conn.cursor()
    c.execute("SELECT * FROM incapacidad ORDER BY fecha_envio DESC")
    novedades = c.fetchall()
    conn.close()
    return render_template('plantilla_incapacidades.html', novedades=novedades)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///incapacidades.db, usuarios.db'
db = SQLAlchemy(app)

def connect_db3():
    # Función para conectar a la base de datos
    return sqlite3.connect('incapacidades.db')

@app.route('/actualizar_incapacidad/<int:id>', methods=['POST'])
def actualizar_incapacidad(id):
    # Obtener el nuevo número de incapacidad del formulario
    nuevo_nro_incapacidad = request.form.get('nro_incapacidad')
    
    # Obtener la incapacidad de la base de datos por su ID
    with closing(connect_db3()) as db:
        cursor = db.cursor()
        cursor.execute("UPDATE incapacidad SET nro_incapacidad=? WHERE id=?", 
                       (nuevo_nro_incapacidad, id))
        db.commit()

    return redirect(url_for('plantilla_incapacidades'))

@app.route('/exportar_a_excel')
def exportar_a_excel():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('incapacidades.db') as conn:
        df = pd.read_sql_query("SELECT * FROM incapacidad", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Incapacidades')
    writer._save()

    # Asegurarse de que el archivo Excel se cierre correctamente
    writer.close()

    # Crear un objeto de respuesta Flask que envía el archivo Excel
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='incapacidades.xlsx')


#----------------------rips-------------------------------------
# Crear la tabla en la base de datos si no existe
def create_table():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rips (
                    Hora TEXT,
                    Orden TEXT,
                    IPS TEXT,
                    TipoIdentificacionPaciente TEXT,
                    IdentificacionPaciente TEXT,
                    PrimerNombrePaciente TEXT,
                    SegundoNombrePaciente TEXT,
                    PrimerApellidoPaciente TEXT,
                    SegundoApellidoPaciente TEXT,
                    Sexo TEXT,
                    FechaNacimiento TEXT,
                    EdadAnios INTEGER,
                    EdadMeses INTEGER,
                    EdadDias INTEGER,
                    CodigoTipoAfiliado TEXT,
                    TipoAfiliado TEXT,
                    CodigoDepartamento TEXT,
                    Departamento TEXT,
                    CodigoMunicipio TEXT,
                    Municipio TEXT,
                    Zona TEXT,
                    TipoIdentificacionMedico TEXT,
                    IdentificacionMedico TEXT,
                    NombresMedico TEXT,
                    CodigoSURACUP TEXT,
                    CodigoCUPS TEXT,
                    NombrePrestacion TEXT,
                    CodigoCausaExterna TEXT,
                    NombreCausaExterna TEXT,
                    FinalidadConsulta TEXT,
                    FinalidadProcedimiento TEXT,
                    DxPrincipal TEXT,
                    NombreDxPrincipal TEXT,
                    TipoDx TEXT,
                    NombreTipoDx TEXT,
                    DxAsociado1 TEXT,
                    DxAsociado2 TEXT,
                    DxAsociado3 TEXT,
                    DestinoAlta TEXT,
                    DestinoRemision TEXT,
                    DestinoHospitalizacion TEXT,
                    EstadoSalida TEXT,
                    HorasObservacion TEXT,
                    HoraSalida TEXT,
                    upload_date TEXT
                )''')
    conn.commit()
    conn.close()
# The above code is a Python Flask route that handles file uploads of a specific file type (specified in the URL). When a file is uploaded, it is saved to the 'uploads' directory. The code then processes the uploaded CSV file, reads its contents using the `csv.DictReader`, and inserts the data into a SQLite database table named 'rips' with multiple columns.
def leer_y_procesar_archivo(entrada, salida):
    """
    Lee el contenido de un archivo, procesa cada línea reemplazando None por cadenas vacías,
    y escribe el resultado en otro archivo.
    """
    try:
        # Abrir el archivo de entrada para lectura
        with open(entrada, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Procesar cada línea
        processed_lines = []
        for line in lines:
            # Reemplazar None por cadenas vacías
            processed_line = line.replace('None', '')
            processed_lines.append(processed_line)
        
        # Escribir el resultado en el archivo de salida
        with open(salida, 'w', encoding='utf-8') as file:
            file.writelines(processed_lines)
        
        print(f"Archivo procesado y escrito correctamente en {salida}.")
    
    except FileNotFoundError:
        print(f"El archivo {entrada} no se encontró.")
    except Exception as e:
        print(f"Ocurrió un error al procesar el archivo: {e}")

# Ruta para subir archivos CSV
def convert_row(row):
    """Convierte cada clave y valor a cadenas ASCII y maneja campos vacíos."""
    row_dict = {}
    for key, value in row.items():
        key_ascii = key.encode('ascii', 'ignore').decode()
        value_ascii = value.encode('ascii', 'ignore').decode() if value else ''  # Convertir None a cadena vacía
        row_dict[key_ascii] = value_ascii
    return row_dict


app.config['UPLOAD_FOLDER'] = 'uploads'
@app.route('/subir_rips/comfama', methods=['POST'])
def upload_file():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400

    file = request.files['archivo']
    if file.filename == '':
        return jsonify({'error': 'El nombre del archivo está vacío'}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Contador de datos guardados
        count = 0

        # Procesa el archivo CSV y almacena los datos en la base de datos
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                converted_row = convert_row(row)
                conn = sqlite3.connect('usuarios.db')
                c = conn.cursor()
                # Ejemplo de inserción de datos, ajusta según tus necesidades
                # Asegúrate de que los nombres de las columnas coincidan con los de tu base de datos
                c.execute("""
                    INSERT INTO rips_comfama (Hora, Orden, IPS, TipoIdentificacionPaciente, IdentificacionPaciente, PrimerNombrePaciente, SegundoNombrePaciente, PrimerApellidoPaciente, SegundoApellidoPaciente, Sexo, FechadeNacimiento, EdadAnos, EdadMeses, EdadDias, CodifoTipoAfiliado, TipoAfiliado, CodigoDepartamento, Departamento, CodigoMunicipio, Municipio, Zona, TipoIdentificacionMedico, IdentificacionMedico, NombresMedico, CodigoSURACUP, CodigoCUPS, NombrePrestacion, CodigoCausaExterna, NombreCausaExterna, FinalidadConsulta, FinalidadProcedimiento, DxPrincipal, NombreDxPrincipal, TipoDx, NombreTipoDx, DxAsociado1, DxAsociado2, DxAsociado3, DestinoAlta, DestinoRemision, DestinoHospitalizacion, EstadoSalida, HorasObservacion, HoraSalida, datetime) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    converted_row.get('Hora'), converted_row.get('Orden'), converted_row.get('IPS'),
                    converted_row.get('TipoIdentificacionPaciente'), converted_row.get('IdentificacionPaciente'),
                    converted_row.get('PrimerNombrePaciente'), converted_row.get('SegundoNombrePaciente'),
                    converted_row.get('PrimerApellidoPaciente'), converted_row.get('SegundoApellidoPaciente'),
                    converted_row.get('Sexo'), converted_row.get('FechadeNacimiento'), converted_row.get('EdadAnos'),
                    converted_row.get('EdadMeses'), converted_row.get('EdadDias'), converted_row.get('CodifoTipoAfiliado'),
                    converted_row.get('TipoAfiliado'), converted_row.get('CodigoDepartamento'), converted_row.get('Departamento'),
                    converted_row.get('CodigoMunicipio'), converted_row.get('Municipio'), converted_row.get('Zona'),
                    converted_row.get('TipoIdentificacionMedico'), converted_row.get('IdentificacionMedico'),
                    converted_row.get('NombresMedico'), converted_row.get('CodigoSURACUP'), converted_row.get('CodigoCUPS'),
                    converted_row.get('NombrePrestacion'), converted_row.get('CodigoCausaExterna'),
                    converted_row.get('NombreCausaExterna'), converted_row.get('FinalidadConsulta'),
                    converted_row.get('FinalidadProcedimiento'), converted_row.get('DxPrincipal'),
                    converted_row.get('NombreDxPrincipal'), converted_row.get('TipoDx'), converted_row.get('NombreTipoDx'),
                    converted_row.get('DxAsociado1'), converted_row.get('DxAsociado2'), converted_row.get('DxAsociado3'),
                    converted_row.get('DestinoAlta'), converted_row.get('DestinoRemision'), converted_row.get('DestinoHospitalizacion'),
                    converted_row.get('EstadoSalida'), converted_row.get('HorasObservacion'), converted_row.get('HoraSalida'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Insertar la fecha y hora actual
                ))
                conn.commit()
                count += 1
                conn.close()

        # Muestra la cantidad de datos guardados en un modal
        return render_template('modal.html', count=count)

@app.route('/subir_rips/sura', methods=['POST'])
def upload_file2():
    if 'archivo' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400

    file = request.files['archivo']
    if file.filename == '':
        return jsonify({'error': 'El nombre del archivo está vacío'}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Contador de datos guardados
        count = 0

        # Procesa el archivo CSV y almacena los datos en la base de datos
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                converted_row = convert_row(row)
                conn = sqlite3.connect('usuarios.db')
                c = conn.cursor()
                # Ejemplo de inserción de datos, ajusta según tus necesidades
                # Asegúrate de que los nombres de las columnas coincidan con los de tu base de datos
                c.execute("""
                    INSERT INTO rips_sura (Hora, Orden, IPS, TipoIdentificacionPaciente, IdentificacionPaciente, PrimerNombrePaciente, SegundoNombrePaciente, PrimerApellidoPaciente, SegundoApellidoPaciente, Sexo, FechadeNacimiento, EdadAnos, EdadMeses, EdadDias, CodifoTipoAfiliado, TipoAfiliado, CodigoDepartamento, Departamento, CodigoMunicipio, Municipio, Zona, TipoIdentificacionMedico, IdentificacionMedico, NombresMedico, CodigoSURACUP, CodigoCUPS, NombrePrestacion, CodigoCausaExterna, NombreCausaExterna, FinalidadConsulta, FinalidadProcedimiento, DxPrincipal, NombreDxPrincipal, TipoDx, NombreTipoDx, DxAsociado1, DxAsociado2, DxAsociado3, DestinoAlta, DestinoRemision, DestinoHospitalizacion, EstadoSalida, HorasObservacion, HoraSalida, datetime) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    converted_row.get('Hora'), converted_row.get('Orden'), converted_row.get('IPS'),
                    converted_row.get('TipoIdentificacionPaciente'), converted_row.get('IdentificacionPaciente'),
                    converted_row.get('PrimerNombrePaciente'), converted_row.get('SegundoNombrePaciente'),
                    converted_row.get('PrimerApellidoPaciente'), converted_row.get('SegundoApellidoPaciente'),
                    converted_row.get('Sexo'), converted_row.get('FechadeNacimiento'), converted_row.get('EdadAnos'),
                    converted_row.get('EdadMeses'), converted_row.get('EdadDias'), converted_row.get('CodifoTipoAfiliado'),
                    converted_row.get('TipoAfiliado'), converted_row.get('CodigoDepartamento'), converted_row.get('Departamento'),
                    converted_row.get('CodigoMunicipio'), converted_row.get('Municipio'), converted_row.get('Zona'),
                    converted_row.get('TipoIdentificacionMedico'), converted_row.get('IdentificacionMedico'),
                    converted_row.get('NombresMedico'), converted_row.get('CodigoSURACUP'), converted_row.get('CodigoCUPS'),
                    converted_row.get('NombrePrestacion'), converted_row.get('CodigoCausaExterna'),
                    converted_row.get('NombreCausaExterna'), converted_row.get('FinalidadConsulta'),
                    converted_row.get('FinalidadProcedimiento'), converted_row.get('DxPrincipal'),
                    converted_row.get('NombreDxPrincipal'), converted_row.get('TipoDx'), converted_row.get('NombreTipoDx'),
                    converted_row.get('DxAsociado1'), converted_row.get('DxAsociado2'), converted_row.get('DxAsociado3'),
                    converted_row.get('DestinoAlta'), converted_row.get('DestinoRemision'), converted_row.get('DestinoHospitalizacion'),
                    converted_row.get('EstadoSalida'), converted_row.get('HorasObservacion'), converted_row.get('HoraSalida'),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Insertar la fecha y hora actual
                ))
                conn.commit()
                count += 1
                conn.close()

        # Muestra la cantidad de datos guardados en un modal
        return render_template('modal.html', count=count)
    

@app.route('/rips_comfama')
def rips_comfama():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("SELECT * FROM rips_comfama ORDER BY datetime DESC")
    novedadesc = c.fetchall()
    conn.close()
    return render_template('rips_comfama.html', novedadesc=novedadesc)

@app.route('/exportar_a_excelcomfama')
def exportar_a_excelcomfama():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('usuarios.db') as conn:
        df = pd.read_sql_query("SELECT * FROM rips_comfama", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='comfama')
    writer._save()

    # Asegurarse de que el archivo Excel se cierre correctamente
    writer.close()

    # Crear un objeto de respuesta Flask que envía el archivo Excel
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='consolidadoripscomfama.xlsx')

@app.route('/rips_sura')
def rips_sura():
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect('usuarios.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM rips_sura ORDER BY datetime DESC")
            novedadess = c.fetchall()
        return render_template('rips_sura.html', novedadess=novedadess)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return "Error interno del servidor", 500
    
@app.route('/crips_sura')
def crips_sura():
    try:
        # Obtener el primer y último día del mes actual
        primer_dia_mes = date(datetime.now().year, datetime.now().month, 1)
        ultimo_dia_mes = primer_dia_mes + timedelta(days=31)
        
        # Ajustar el último día del mes si es febrero
        if primer_dia_mes.month == 2:
            ultimo_dia_mes = ultimo_dia_mes - timedelta(days=1)
        
        with sqlite3.connect('usuarios.db') as conn:
            c = conn.cursor()
            # Filtrar registros por fecha entre el primer y último día del mes actual
            c.execute("SELECT * FROM rips_sura WHERE datetime BETWEEN ? AND ? ORDER BY datetime DESC", (primer_dia_mes, ultimo_dia_mes))
            novedadess = c.fetchall()
        return render_template('rips_sura.html', novedadess=novedadess)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return "Error interno del servidor", 500

@app.route('/exportar_a_excelsura')
def exportar_a_excelsura():
    # Conectar a la base de datos y obtener los datos
    with sqlite3.connect('usuarios.db') as conn:
        df = pd.read_sql_query("SELECT * FROM rips_sura", conn)

    # Crear un archivo Excel en memoria
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='sura')
    writer._save()

    # Asegurarse de que el archivo Excel se cierre correctamente
    writer.close()

    # Crear un objeto de respuesta Flask que envía el archivo Excel
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='consolidadoripssura.xlsx')


#------------------agenda-----------------------------

contabilidad = 'contabilidad.db'

@app.route('/contabilidad')
def contabilidad_view():
    create_db(contabilidad)
    conn = sqlite3.connect(contabilidad)
    c = conn.cursor()
    c.execute('SELECT * FROM agenda WHERE completada=0')
    actividades4 = c.fetchall()
    conn.close()
    return render_template('contabilidad.html', actividades4=actividades4)

@app.route('/agregar4', methods=['POST'])
def agregar_actividad4():
    actividad = request.form['actividad']
    conn = sqlite3.connect(contabilidad)
    c = conn.cursor()
    c.execute('INSERT INTO agenda (actividad, completada) VALUES (?, 0)', (actividad,))
    conn.commit()
    conn.close()
    return redirect(url_for('contabilidad_view'))

@app.route('/completar4/<int:id>')
def completar_actividad4(id):
    conn = sqlite3.connect(contabilidad)
    c = conn.cursor()
    c.execute('UPDATE agenda SET completada=1 WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('contabilidad_view'))

#--------------------------FINALIZA SESSION DE CONTABILIDAD----------------------
if __name__ == '__main__':
    app.run(debug=True,  host='0.0.0.0', port=5000)
    
    