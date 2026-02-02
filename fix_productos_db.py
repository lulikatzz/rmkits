import sqlite3

conn = sqlite3.connect('productos.db')
cursor = conn.cursor()

print("=== ESTADO ACTUAL DE productos.db ===")
# Ver todos los pedidos
cursor.execute('SELECT id, cliente_nombre, fecha FROM pedido ORDER BY id')
pedidos = cursor.fetchall()
print(f'Pedidos existentes: {len(pedidos)}')
for p in pedidos[:10]:  # Mostrar máximo 10
    print(f'  ID: {p[0]} - {p[1]}')

# Ver secuencia
cursor.execute('SELECT seq FROM sqlite_sequence WHERE name = "pedido"')
result = cursor.fetchone()
print(f'Secuencia actual: {result[0] if result else "No existe"}')

print("\n=== ACTUALIZANDO SECUENCIA ===")
# Actualizar la secuencia para que el próximo ID sea 1200
cursor.execute("UPDATE sqlite_sequence SET seq = 1199 WHERE name = 'pedido'")
conn.commit()
print("✓ Secuencia actualizada a 1199")

# Verificar
cursor.execute('SELECT seq FROM sqlite_sequence WHERE name = "pedido"')
result = cursor.fetchone()
print(f'\nSecuencia final: {result[0]}')
print("\n✅ El próximo pedido será el #1200")
print("📝 Los pedidos anteriores (1-7) se mantendrán en la base de datos")
print("   pero los nuevos empezarán desde 1200")

conn.close()
