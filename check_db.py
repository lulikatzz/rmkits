import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Verificar si la tabla existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pedido'")
exists = cursor.fetchone()

if not exists:
    print('La tabla pedido no existe. Creándola...')
    cursor.execute("""
        CREATE TABLE pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente_nombre TEXT NOT NULL,
            cliente_cuit TEXT,
            cliente_telefono TEXT,
            cliente_email TEXT,
            cliente_direccion TEXT,
            metodo_entrega TEXT,
            envio_direccion TEXT,
            envio_localidad TEXT,
            envio_provincia TEXT,
            envio_cp TEXT,
            envio_nombre_destinatario TEXT,
            envio_referencias TEXT,
            productos TEXT NOT NULL,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'pendiente'
        )
    """)
    conn.commit()
    print('✓ Tabla pedido creada')

# Ver max ID actual
cursor.execute('SELECT MAX(id) FROM pedido')
max_id_result = cursor.fetchone()[0]
print(f'Max ID actual: {max_id_result if max_id_result else "Sin pedidos"}')

# Ver secuencia
cursor.execute('SELECT name, seq FROM sqlite_sequence WHERE name = "pedido"')
result = cursor.fetchone()
print(f'Secuencia actual: {result if result else "No existe"}')

# Actualizar secuencia a 1199
cursor.execute('INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES ("pedido", 1199)')
conn.commit()

print('\n✓ Secuencia actualizada a 1199')
print('El próximo pedido será el #1200')

conn.close()
