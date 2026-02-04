import sqlite3
import json
from datetime import datetime

# Conectar a la base de datos correcta
conn = sqlite3.connect('productos.db')
cursor = conn.cursor()

# Datos del pedido
pedido = {
    "cliente_nombre": "Florencia gens",
    "cliente_telefono": "2267452365",
    "cliente_email": "florgens@hotmail.com.ar",
    "metodo_entrega": "envio",
    "envio_direccion": "Intermedanos 1091",
    "envio_localidad": "Pinamar",
    "envio_provincia": "Buenos aires",
    "envio_cp": "7167",
    "envio_nombre_destinatario": "Florencia gens",
    "productos": [
        {"codigo": "A001", "titulo": "Lapiz negro grafito Filgo HB", "cantidad": 24, "precio": 60},
        {"codigo": "A002", "titulo": "Corrector liquido Filgo 012", "cantidad": 24, "precio": 250},
        {"codigo": "A006", "titulo": "Boligrafo Stick 1.0mm color AZUL", "cantidad": 50, "precio": 80},
        {"codigo": "A0010", "titulo": "Lápices de colores largos Filgo x12 colores", "cantidad": 12, "precio": 750},
        {"codigo": "A0011", "titulo": "Lápices de colores largos Filgo x24 colores", "cantidad": 6, "precio": 2400},
        {"codigo": "A0017", "titulo": "Marcadores Pinto 2210 Filgo x10 colores", "cantidad": 12, "precio": 850},
        {"codigo": "A0042", "titulo": "Compás Filgo con repuesto", "cantidad": 12, "precio": 2700},
        {"codigo": "A0133", "titulo": "Adhesivo Sintético Filgo 30ml", "cantidad": 12, "precio": 400},
        {"codigo": "A0222", "titulo": "Repuesto de hojas exito cuadriculado x96", "cantidad": 5, "precio": 3500},
        {"codigo": "A0223", "titulo": "Repuesto de hojas exito rayado x96", "cantidad": 5, "precio": 3500},
        {"codigo": "A0040", "titulo": "Tijera Filgo Pinto", "cantidad": 24, "precio": 600},
        {"codigo": "A0039", "titulo": "Sacapuntas Filgo Pinto Circus", "cantidad": 12, "precio": 350},
        {"codigo": "A0035", "titulo": "Goma de borrar Filgo Duo Tek 4021", "cantidad": 36, "precio": 250},
        {"codigo": "A0033", "titulo": "Crayones Filgo x12 colores", "cantidad": 24, "precio": 750},
        {"codigo": "A0127", "titulo": "Repuesto Canson N°5 Blanco x8 hojas Triunfante", "cantidad": 25, "precio": 800},
        {"codigo": "A0125", "titulo": "Repuesto Canson N°3 Blanco x8 hojas Triunfante", "cantidad": 25, "precio": 500},
        {"codigo": "A0116", "titulo": "Tempera Tintoretto x10 pomos", "cantidad": 12, "precio": 1280},
        {"codigo": "A0099", "titulo": "Cuaderno A4 Universitario Potosi t/flex Rayado x80 hojas", "cantidad": 5, "precio": 1800}
    ],
    "total": 219700,
    "estado": "pendiente"
}

# Convertir productos a JSON
productos_json = json.dumps(pedido['productos'])

# Insertar el pedido
try:
    cursor.execute("""
        INSERT INTO pedido (cliente_nombre, cliente_telefono, cliente_email,
                           metodo_entrega, envio_direccion, envio_localidad,
                           envio_provincia, envio_cp, envio_nombre_destinatario,
                           productos, total, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pedido['cliente_nombre'],
        pedido['cliente_telefono'],
        pedido['cliente_email'],
        pedido['metodo_entrega'],
        pedido['envio_direccion'],
        pedido['envio_localidad'],
        pedido['envio_provincia'],
        pedido['envio_cp'],
        pedido['envio_nombre_destinatario'],
        productos_json,
        pedido['total'],
        pedido['estado']
    ))
    
    pedido_id = cursor.lastrowid
    conn.commit()
    
    print(f"✅ Pedido cargado exitosamente! ID: {pedido_id}")
    print(f"Cliente: {pedido['cliente_nombre']}")
    print(f"Total: ${pedido['total']:,.0f}")
    print(f"Productos: {len(pedido['productos'])}")
    
except Exception as e:
    print(f"❌ Error al cargar pedido: {e}")
    conn.rollback()
finally:
    conn.close()
