import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Ver todos los pedidos actuales
cursor.execute('SELECT id FROM pedido ORDER BY id')
pedidos = cursor.fetchall()
print(f'Pedidos actuales: {[p[0] for p in pedidos]}')

# Ver max ID
cursor.execute('SELECT MAX(id) FROM pedido')
max_id = cursor.fetchone()[0]
print(f'Max ID actual: {max_id}')

# Ver secuencia actual
cursor.execute('SELECT seq FROM sqlite_sequence WHERE name = "pedido"')
result = cursor.fetchone()
print(f'Secuencia actual: {result[0] if result else "No existe"}')

# Forzar actualización de la secuencia
if max_id and max_id >= 1199:
    print(f'\n⚠️ Ya hay pedidos con ID >= 1200. No se puede cambiar.')
else:
    # Actualizar la secuencia para que el próximo sea 1200
    cursor.execute('DELETE FROM sqlite_sequence WHERE name = "pedido"')
    cursor.execute('INSERT INTO sqlite_sequence (name, seq) VALUES ("pedido", 1199)')
    conn.commit()
    
    print('\n✓ Secuencia actualizada a 1199')
    print('El próximo pedido será el #1200')

# Verificar la secuencia final
cursor.execute('SELECT seq FROM sqlite_sequence WHERE name = "pedido"')
result = cursor.fetchone()
print(f'\nSecuencia final: {result[0] if result else "No existe"}')

conn.close()
