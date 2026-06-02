import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mi_clave_secreta_super_segura_unfv')

CORS(app)

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def inicializar_base_datos_auto():
    """Crea las tablas requeridas y los registros de prueba de manera automática."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # TABLA DE LOS USUARIOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL
        )
    ''')
    
    # TABLA DE LOS PRODUCTOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL,
            categoria TEXT
        )
    ''')
    
    # INSERSIÓN DE DATOS INICIALES PARA LA TABLA 
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, password, nombre) VALUES (?, ?, ?)", 
                       ('admin', '1234', 'Fabio Ormeño'))
    
    # INSERSIÓN DE DATOS A LA TABLA DE LOS PRODUCTOS
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        productos_prueba = [
            ('P001', 'Laptop ASUS ROG', 'Laptop Gamer AMD Ryzen 7, 16GB RAM, 512GB SSD', 4500.0, 10, 'Tecnología'),
            ('P002', 'Mouse Logi Master 3S', 'Mouse inalámbrico ergonómico avanzado para desarrolladores', 420.0, 25, 'Accesorios'),
            ('P003', 'Teclado Mecánico Keychron Q1', 'Teclado mecánico custom 75% con switches Gateron Pro', 750.0, 5, 'Accesorios'),
            ('P004', 'Monitor Dell UltraSharp 27"', 'Monitor 4K ideal para diseño y visualización de código', 1850.0, 8, 'Tecnología')
        ]
        cursor.executemany(
            "INSERT INTO productos (codigo, nombre, descripcion, precio, stock, categoria) VALUES (?, ?, ?, ?, ?, ?)", 
            productos_prueba
        )
            
    conn.commit()
    conn.close()

# ENRUTAMIENTO Y DIRECCIONAMIENTO 
#LOGIN
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        usuario = conn.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?',
                               (username, password)).fetchone()
        conn.close()
        
        if usuario:
            session['logged_in'] = True
            session['username'] = usuario['username']
            session['nombre'] = usuario['nombre']
            return redirect(url_for('principal'))
        else:
            error = 'Credenciales incorrectas. Intente nuevamente.'
            
    return render_template('login.html', error=error)

#PRINCIPAL
@app.route('/principal')
def principal():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('principal.html', nombre=session.get('nombre'))

#BUSCADOR
@app.route('/buscador')
def buscador():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('buscador.html')

@app.route('/api/buscar_producto', methods=['POST'])
def buscar_producto():
    data = request.get_json() if request.is_json else request.form
    codigo = data.get('codigo', '').strip()
    
    if not codigo:
        return jsonify({'status': 'error', 'message': 'Código no proporcionado'}), 400
        
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM productos WHERE codigo = ?', (codigo,)).fetchone()
    conn.close()
    
    if producto:
        return jsonify({
            'status': 'success',
            'data': {
                'codigo': producto['codigo'],
                'nombre': producto['nombre'],
                'descripcion': producto['descripcion'],
                'precio': producto['precio'],
                'stock': producto['stock'],
                'categoria': producto['categoria']
            }
        })
    else:
        return jsonify({'status': 'error', 'message': 'Producto no encontrado'}), 404

#LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# EJECUCIÓN 
inicializar_base_datos_auto()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)