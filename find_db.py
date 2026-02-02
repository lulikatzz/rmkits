import sqlite3
import os

# Buscar todas las bases de datos .db en el directorio
print("=== BUSCANDO BASES DE DATOS ===")
for file in os.listdir('.'):
    if file.endswith('.db'):
        print(f"\n📁 Archivo: {file}")
        try:
            conn = sqlite3.connect(file)
            cursor = conn.cursor()
            
            # Verificar si tiene tabla pedido
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pedido'")
            if cursor.fetchone():
                print("  ✓ Tiene tabla 'pedido'")
                
                # Contar pedidos
                cursor.execute('SELECT COUNT(*) FROM pedido')
                count = cursor.fetchone()[0]
                print(f"  Total pedidos: {count}")
                
                # Ver últimos 5 pedidos
                cursor.execute('SELECT id, cliente_nombre FROM pedido ORDER BY id DESC LIMIT 5')
                pedidos = cursor.fetchall()
                if pedidos:
                    print("  Últimos pedidos:")
                    for p in pedidos:
                        print(f"    ID: {p[0]} - {p[1]}")
                
                # Ver secuencia
                cursor.execute('SELECT seq FROM sqlite_sequence WHERE name = "pedido"')
                result = cursor.fetchone()
                if result:
                    print(f"  Secuencia: {result[0]}")
                else:
                    print("  Secuencia: No configurada")
            else:
                print("  ✗ No tiene tabla 'pedido'")
            
            conn.close()
        except Exception as e:
            print(f"  Error: {e}")

print("\n=== VERIFICANDO Config.DATABASE_PATH ===")
# Leer el config.py para ver qué base de datos usa
try:
    with open('config.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'DATABASE_PATH' in content:
            # Extraer la línea
            for line in content.split('\n'):
                if 'DATABASE_PATH' in line and not line.strip().startswith('#'):
                    print(f"config.py: {line.strip()}")
except Exception as e:
    print(f"Error leyendo config.py: {e}")
