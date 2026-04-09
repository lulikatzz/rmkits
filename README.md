# RM KITS - Carrito de Compras Mayorista

Aplicación web de carrito de compras para ventas mayoristas con catálogo de productos, gestión de pedidos y panel de administración.

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## 📚 Documentación

Toda la documentación del proyecto está organizada en la carpeta [`docs/`](docs/):

- **[README.md](docs/README.md)** - Documentación completa del proyecto
- **[ADMIN_MANUAL.md](docs/ADMIN_MANUAL.md)** - Manual del panel de administración
- **[ALMACENAMIENTO_PERSISTENTE.md](docs/ALMACENAMIENTO_PERSISTENTE.md)** - Configuración de almacenamiento en Render
- **[PANEL_ADMIN_README.md](docs/PANEL_ADMIN_README.md)** - Guía del panel admin
- **[PRODUCTOS_NUEVOS_README.md](docs/PRODUCTOS_NUEVOS_README.md)** - Gestión de productos nuevos
- **[ACTUALIZACION_CARRITO.md](docs/ACTUALIZACION_CARRITO.md)** - Changelog del carrito
- **[MEJORAS.md](docs/MEJORAS.md)** - Mejoras y futuras funcionalidades

## 🛠️ Tecnologías

- **Backend**: Flask (Python)
- **Base de datos**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Render

## 📦 Estructura del Proyecto

```
web_carrito/
├── app.py              # Aplicación principal Flask
├── config.py           # Configuración
├── data/               # Base de datos e imágenes (persistente)
├── static/             # CSS, JS, imágenes estáticas
├── templates/          # Plantillas HTML
├── docs/               # Documentación
├── requirements.txt    # Dependencias
└── runtime.txt         # Versión de Python
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Desarrollo local (opcional)
PERSISTENT_DATA_PATH=data

# Producción en Render
PERSISTENT_DATA_PATH=/data
SECRET_KEY=tu-clave-secreta
```

### Almacenamiento Persistente

El proyecto utiliza almacenamiento persistente para la base de datos y las imágenes. Ver [ALMACENAMIENTO_PERSISTENTE.md](docs/ALMACENAMIENTO_PERSISTENTE.md) para más detalles.

## 👤 Acceso Admin

- **URL**: `/admin`
- **Usuario**: admin
- **Contraseña**: rmkits2024

## 📝 Licencia

Proyecto privado - RM KITS © 2026
