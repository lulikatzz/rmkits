import requests
import json

# URL del endpoint (asegúrate de que la app esté corriendo)
url = "http://127.0.0.1:5000/admin/cargar-pedido-manual"

# Datos del pedido
pedido = {
    "cliente_nombre": "Florencia gens",
    "cliente_telefono": "2267452365",
    "cliente_email": "",
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

# Primero necesitamos hacer login para obtener la sesión
session = requests.Session()

# Login (usa las credenciales de tu admin)
login_data = {
    "username": "admin",  # Cambia esto por tu usuario
    "password": "admin"   # Cambia esto por tu contraseña
}

login_response = session.post("http://127.0.0.1:5000/admin/login", data=login_data)

if login_response.status_code == 200:
    # Ahora enviar el pedido
    response = session.post(url, json=pedido)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Pedido cargado exitosamente! ID: {result.get('pedido_id')}")
    else:
        print(f"❌ Error al cargar pedido: {response.text}")
else:
    print("❌ Error al hacer login")
