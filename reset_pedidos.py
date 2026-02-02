import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print("=== ESTADO ACTUAL ===")
# Ver todos los pedidos
cursor.execute('SELECT id, cliente_nombre, fecha FROM pedido ORDER BY id')
pedidos = cursor.fetchall()
print(f'Pedidos existentes: {len(pedidos)}')
for p in pedidos:
    print(f'  ID: {p[0]} - {p[1]} - {p[2]}')

# Ver secuencia
cursor.execute('SELECT seq FROM sqlite_sequence WHERE name = "pedido"')
result = cursor.fetchone()
print(f'Secuencia actual: {result[0] if result else "No existe"}')

print("\n=== RECREANDO TABLA ===")
# Eliminar tabla y secuencia
cursor.execute("DROP TABLE IF EXISTS pedido")
cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'pedido'")
conn.commit()

# Recrear tabla
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
print("✓ Tabla recreada")

# Insertar secuencia para que empiece en 1200
cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('pedido', 1199)")
conn.commit()
print("✓ Secuencia configurada a 1199")

# Verificar
cursor.execute('SELECT seq FROM sqlite_sequence WHERE name = "pedido"')
result = cursor.fetchone()
print(f'\nSecuencia final: {result[0] if result else "No existe"}')
print("\n✅ El próximo pedido será el #1200")

conn.close()
