"""
Configuración centralizada de la aplicación RM KITS
"""
import os

class Config:
    """Configuración base de la aplicación"""
    
    # Base de datos
    DATABASE_PATH = "productos.db"
    
    # WhatsApp
    WHATSAPP_NUMBER = "5491158573906"
    
    # Compras
    PEDIDO_MINIMO = 200000
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-rmkits-2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Productos por página
    PRODUCTOS_POR_PAGINA = 24
    
    # Dirección del local
    LOCAL_DIRECCION = "Av. Rivadavia 2768, CABA"
    LOCAL_HORARIOS = "Lun a Vie 9 a 18 hs. Sáb 9 a 15 hs."
    
    # Costos de envío
    ENVIO_CABA = 6000
    ENVIO_GBA = 10000
    
    # Admin - Usuarios autorizados (username: password)
    ADMIN_USERS = {
        'admin': 'rmkits2024',
        'nicolas': '123'
    }
    
    # Backwards compatibility
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'rmkits2024'
    
    # Uploads
    UPLOAD_FOLDER = os.path.join('static', 'img')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB máximo
