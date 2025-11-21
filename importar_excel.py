import pandas as pd
import sqlite3
import unicodedata

def normalizar_categoria(s):
    if pd.isna(s):
        return ""
    txt = str(s).strip().lower()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")
    if "jugueteria" in txt or "cotillon" in txt:
        return "jugueteria/cotillon"
    if "libreria" in txt:
        return "libreria"
    return txt

def to_int(value, default=0):
    if pd.isna(value):
        return default
    try:
        return int(value)
    except:
        return default

df = pd.read_excel("productos.xlsx")

conn = sqlite3.connect("productos.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS producto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        titulo TEXT,
        descripcion TEXT,
        precio REAL,
        minimo INTEGER,
        multiplo INTEGER,
        stock INTEGER,
        imagen TEXT,
        categoria TEXT
    )
""")

try:
    cursor.execute("ALTER TABLE producto ADD COLUMN categoria TEXT")
except:
    pass

cursor.execute("DELETE FROM producto")

for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO producto (codigo, titulo, descripcion, precio, minimo, multiplo, stock, imagen, categoria)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row.get("codigo", ""),
        row.get("titulo", ""),
        row.get("descripcion", ""),
        float(row.get("precio", 0)),
        to_int(row.get("minimo"), 0),
        to_int(row.get("multiplo"), 0),
        to_int(row.get("stock"), 0),
        row.get("imagen", ""),
        normalizar_categoria(row.get("categoria", ""))
    ))

conn.commit()
conn.close()

print("✅ Productos importados correctamente con categoría normalizada.")
