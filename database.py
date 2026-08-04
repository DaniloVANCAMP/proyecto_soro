import sqlite3
import hashlib
import os

# Ruta donde se guardará el archivo de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_fitness.db')

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Tabla de Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    
    # 2. Tabla de Perfiles
    c.execute('''CREATE TABLE IF NOT EXISTS perfiles (
                    user_id INTEGER PRIMARY KEY,
                    nombre TEXT, edad INTEGER, genero TEXT, nivel TEXT,
                    estatura REAL, peso REAL, pecho REAL, cintura REAL,
                    piernas REAL, brazos REAL, cadera REAL, pantorrillas REAL,
                    FOREIGN KEY(user_id) REFERENCES usuarios(id)
                )''')
    conn.commit()
    conn.close()

def crear_usuario(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", 
                  (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verificar_usuario(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE username=? AND password=?", 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    
    if user:
        return user[0]
    return None

def guardar_perfil(user_id, datos):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT user_id FROM perfiles WHERE user_id=?", (user_id,))
    existe = c.fetchone()
    
    medidas = datos.get('medidas', {})
    
    if existe:
        c.execute('''UPDATE perfiles SET 
                     nombre=?, edad=?, genero=?, nivel=?, estatura=?, peso=?,
                     pecho=?, cintura=?, piernas=?, brazos=?, cadera=?, pantorrillas=?
                     WHERE user_id=?''',
                  (datos.get('nombre'), datos.get('edad'), datos.get('genero'), datos.get('nivel'),
                   datos.get('estatura'), datos.get('peso'),
                   medidas.get('pecho', 0), medidas.get('cintura', 0), medidas.get('pierna', 0), 
                   medidas.get('brazo', 0), medidas.get('cadera', 0), medidas.get('pantorrilla', 0),
                   user_id))
    else:
        c.execute('''INSERT INTO perfiles 
                     (user_id, nombre, edad, genero, nivel, estatura, peso, 
                      pecho, cintura, piernas, brazos, cadera, pantorrillas)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, datos.get('nombre'), datos.get('edad'), datos.get('genero'), datos.get('nivel'),
                   datos.get('estatura'), datos.get('peso'),
                   medidas.get('pecho', 0), medidas.get('cintura', 0), medidas.get('pierna', 0), 
                   medidas.get('brazo', 0), medidas.get('cadera', 0), medidas.get('pantorrilla', 0)))
    
    conn.commit()
    conn.close()

def obtener_perfil(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM perfiles WHERE user_id=?", (user_id,))
    fila = c.fetchone()
    conn.close()
    
    if fila:
        return {
            "nombre": fila["nombre"],
            "edad": fila["edad"],
            "genero": fila["genero"],
            "nivel": fila["nivel"],
            "estatura": fila["estatura"],
            "peso": fila["peso"],
            "medidas": {
                "pecho": fila["pecho"],
                "cintura": fila["cintura"],
                "pierna": fila["piernas"],
                "brazo": fila["brazos"],
                "cadera": fila["cadera"],
                "pantorrilla": fila["pantorrillas"]
            }
        }
    return None

init_db()