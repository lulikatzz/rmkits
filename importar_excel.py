"""
Script para importar productos desde Excel a SQLite
Uso: python importar_excel.py
"""
import pandas as pd
import sqlite3
import unicodedata
import sys
import os
from pathlib import Path


def buscar_imagen_para_codigo(codigo, img_folder='static/img'):
    """
    Busca si existe una imagen para el código dado.
    Retorna el nombre del archivo si existe, o string vacío si no.
    """
    extensiones = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    
    for ext in extensiones:
        img_path = os.path.join(img_folder, f"{codigo}{ext}")
        if os.path.exists(img_path):
            return f"{codigo}{ext}"
    
    return ""


def normalizar_categoria(s):
    """
    Normaliza el nombre de la categoría a un formato estándar
    """
    if pd.isna(s):
        return ""
    
    txt = str(s).strip().lower()
    # Remover acentos
    txt = "".join(
        c for c in unicodedata.normalize("NFD", txt) 
        if unicodedata.category(c) != "Mn"
    )
    
    # Categorías conocidas
    if "jugueteria" in txt or "cotillon" in txt:
        return "jugueteria/cotillon"
    if "libreria" in txt:
        return "libreria"
    
    return txt


def to_int(value, default=0):
    """Convierte un valor a entero con manejo seguro de errores"""
    if pd.isna(value):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def to_float(value, default=0.0):
    """Convierte un valor a float con manejo seguro de errores"""
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def crear_tabla(cursor):
    """Crea la tabla de productos si no existe"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL DEFAULT 0,
            minimo INTEGER NOT NULL DEFAULT 1,
            multiplo INTEGER NOT NULL DEFAULT 1,
            stock INTEGER NOT NULL DEFAULT 0,
            imagen TEXT,
            categoria TEXT
        )
    """)
    
    # Intentar agregar columna categoria si no existe (migración)
    try:
        cursor.execute("ALTER TABLE producto ADD COLUMN categoria TEXT")
    except sqlite3.OperationalError:
        pass  # La columna ya existe
    
    # Intentar agregar columna activo si no existe (migración)
    try:
        cursor.execute("ALTER TABLE producto ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # La columna ya existe


def crear_tabla_pedidos(cursor):
    """Crea la tabla de pedidos si no existe"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre TEXT NOT NULL,
            cliente_cuit TEXT,
            cliente_telefono TEXT,
            cliente_email TEXT,
            cliente_direccion TEXT,
            metodo_entrega TEXT,
            productos TEXT NOT NULL,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'pendiente'
        )
    """)


def crear_tabla_productos_nuevos(cursor):
    """Crea la tabla de productos nuevos si no existe"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producto_nuevo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES producto(id)
        )
    """)


def importar_productos(archivo_excel="productos.xlsx", archivo_db="productos.db"):
    """
    Importa productos desde un archivo Excel a la base de datos SQLite
    """
    # Verificar que el archivo Excel existe
    if not Path(archivo_excel).exists():
        print(f"❌ Error: No se encuentra el archivo '{archivo_excel}'")
        return False
    
    try:
        # Leer Excel
        print(f"📖 Leyendo archivo '{archivo_excel}'...")
        df = pd.read_excel(archivo_excel)
        
        if df.empty:
            print("⚠️  Advertencia: El archivo Excel está vacío")
            return False
        
        print(f"✓ Se encontraron {len(df)} productos en el archivo")
        
        # Conectar a la base de datos
        print(f"💾 Conectando a la base de datos '{archivo_db}'...")
        conn = sqlite3.connect(archivo_db)
        cursor = conn.cursor()
        
        # Crear tablas
        crear_tabla(cursor)
        crear_tabla_pedidos(cursor)
        crear_tabla_productos_nuevos(cursor)
        
        # Limpiar datos anteriores
        cursor.execute("DELETE FROM producto")
        print("✓ Tabla limpiada")
        
        # Importar productos
        productos_importados = 0
        errores = 0
        
        for idx, row in df.iterrows():
            try:
                codigo = str(row.get("codigo", "")).strip()
                titulo = str(row.get("titulo", "")).strip()
                
                if not codigo or not titulo:
                    print(f"⚠️  Fila {idx + 2}: Saltada (sin código o título)")
                    continue
                
                # Obtener imagen del Excel o buscarla automáticamente
                imagen_excel = str(row.get("imagen", "")).strip()
                if not imagen_excel:
                    # Si no hay imagen en el Excel, buscar por código
                    imagen_excel = buscar_imagen_para_codigo(codigo)
                
                cursor.execute("""
                    INSERT INTO producto 
                    (codigo, titulo, descripcion, precio, minimo, multiplo, stock, imagen, categoria)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    codigo,
                    titulo,
                    str(row.get("descripcion", "")).strip(),
                    to_float(row.get("precio"), 0),
                    max(1, to_int(row.get("minimo"), 1)),
                    max(1, to_int(row.get("multiplo"), 1)),
                    to_int(row.get("stock"), 0),
                    imagen_excel,
                    normalizar_categoria(row.get("categoria", ""))
                ))
                productos_importados += 1
                
            except Exception as e:
                errores += 1
                print(f"❌ Error en fila {idx + 2}: {e}")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        # Resumen
        print("\n" + "="*50)
        print("✅ IMPORTACIÓN COMPLETADA")
        print(f"   Productos importados: {productos_importados}")
        if errores > 0:
            print(f"   Errores: {errores}")
        print("="*50 + "\n")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra el archivo '{archivo_excel}'")
        return False
    except pd.errors.EmptyDataError:
        print("❌ Error: El archivo Excel está vacío o es inválido")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


if __name__ == "__main__":
    # Permitir especificar archivo desde línea de comandos
    archivo = sys.argv[1] if len(sys.argv) > 1 else "productos.xlsx"
    
    success = importar_productos(archivo)
    sys.exit(0 if success else 1)
