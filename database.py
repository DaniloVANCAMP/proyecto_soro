import sqlite3
import hashlib
import os
import json

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
                    password TEXT,
                    correo TEXT
                )''')
    
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN correo TEXT")
    except sqlite3.OperationalError:
        pass
    
    # 2. Tabla de Perfiles
    c.execute('''CREATE TABLE IF NOT EXISTS perfiles (
                    user_id INTEGER PRIMARY KEY,
                    nombre TEXT, edad INTEGER, genero TEXT, nivel TEXT,
                    estatura REAL, peso REAL, pecho REAL, cintura REAL,
                    piernas REAL, brazos REAL, cadera REAL, pantorrillas REAL,
                    limitaciones TEXT, equipo TEXT,
                    FOREIGN KEY(user_id) REFERENCES usuarios(id)
                )''')

    # 3. Tabla de Planificación Semanal
    c.execute('''CREATE TABLE IF NOT EXISTS planificacion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    fecha TEXT,
                    ejercicio_id TEXT,
                    nombre TEXT,
                    musculo TEXT,
                    equipo TEXT,
                    series INTEGER,
                    reps INTEGER,
                    gif_url TEXT,
                    instrucciones TEXT,
                    FOREIGN KEY(user_id) REFERENCES usuarios(id)
                )''')
                
    conn.commit()
    conn.close()

def crear_usuario(username, password, correo=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO usuarios (username, password, correo) VALUES (?, ?, ?)", 
                  (username, hash_password(password), correo))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verificar_usuario(identificador, password):
    # Ahora permite iniciar sesión con Correo O Usuario
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username FROM usuarios WHERE (correo=? OR username=?) AND password=?", 
              (identificador, identificador, hash_password(password)))
    user = c.fetchone()
    conn.close()
    
    if user:
        return user[0], user[1] # Retorna (ID, NombreUsuario)
    return None, None

def guardar_perfil(user_id, datos):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT user_id FROM perfiles WHERE user_id=?", (user_id,))
    existe = c.fetchone()
    
    medidas = datos.get('medidas', {})
    limitaciones_str = ",".join(datos.get('limitaciones', []))
    equipo_str = ",".join(datos.get('equipo', []))
    
    if existe:
        c.execute('''UPDATE perfiles SET 
                     nombre=?, edad=?, genero=?, nivel=?, estatura=?, peso=?,
                     pecho=?, cintura=?, piernas=?, brazos=?, cadera=?, pantorrillas=?,
                     limitaciones=?, equipo=?
                     WHERE user_id=?''',
                  (datos.get('nombre'), datos.get('edad'), datos.get('genero'), datos.get('nivel'),
                   datos.get('estatura'), datos.get('peso'),
                   medidas.get('pecho', 0), medidas.get('cintura', 0), medidas.get('pierna', 0), 
                   medidas.get('brazo', 0), medidas.get('cadera', 0), medidas.get('pantorrilla', 0),
                   limitaciones_str, equipo_str, user_id))
    else:
        c.execute('''INSERT INTO perfiles 
                     (user_id, nombre, edad, genero, nivel, estatura, peso, 
                      pecho, cintura, piernas, brazos, cadera, pantorrillas,
                      limitaciones, equipo)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, datos.get('nombre'), datos.get('edad'), datos.get('genero'), datos.get('nivel'),
                   datos.get('estatura'), datos.get('peso'),
                   medidas.get('pecho', 0), medidas.get('cintura', 0), medidas.get('pierna', 0), 
                   medidas.get('brazo', 0), medidas.get('cadera', 0), medidas.get('pantorrilla', 0),
                   limitaciones_str, equipo_str))
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
            "nombre": fila["nombre"], "edad": fila["edad"], "genero": fila["genero"],
            "nivel": fila["nivel"], "estatura": fila["estatura"], "peso": fila["peso"],
            "limitaciones": fila["limitaciones"].split(",") if fila["limitaciones"] else [],
            "equipo": fila["equipo"].split(",") if fila["equipo"] else [],
            "medidas": {
                "pecho": fila["pecho"], "cintura": fila["cintura"], "pierna": fila["piernas"],
                "brazo": fila["brazos"], "cadera": fila["cadera"], "pantorrilla": fila["pantorrillas"]
            }
        }
    return None

def guardar_plan_dia(user_id, fecha, rutina):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM planificacion WHERE user_id=? AND fecha=?", (user_id, fecha))
    for item in rutina:
        inst_str = json.dumps(item.get("instrucciones", []))
        c.execute('''INSERT INTO planificacion 
                     (user_id, fecha, ejercicio_id, nombre, musculo, equipo, series, reps, gif_url, instrucciones)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, fecha, item.get("id_unico", ""), item.get("nombre", ""), 
                   item.get("musculo", ""), item.get("equipo", ""), item.get("series", 3), 
                   item.get("reps", 10), item.get("gif_url", ""), inst_str))
    conn.commit()
    conn.close()

def obtener_plan_dia(user_id, fecha):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM planificacion WHERE user_id=? AND fecha=?", (user_id, fecha))
    filas = c.fetchall()
    conn.close()
    rutina = []
    for fila in filas:
        rutina.append({
            "id_unico": fila["ejercicio_id"], "nombre": fila["nombre"], "musculo": fila["musculo"],
            "equipo": fila["equipo"], "series": fila["series"], "reps": fila["reps"],
            "gif_url": fila["gif_url"], "instrucciones": json.loads(fila["instrucciones"]) if fila["instrucciones"] else []
        })
    return rutina

init_db()