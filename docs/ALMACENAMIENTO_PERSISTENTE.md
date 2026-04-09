# Configuración de Almacenamiento Persistente en Render

## Resumen

Este proyecto ahora utiliza almacenamiento persistente separado del código fuente para la base de datos y las imágenes de productos, evitando que se pierdan en reinicios o redeploys.

## Cambios Realizados

### 1. Estructura de Archivos Persistentes

**Antes:**
```
web_carrito/
  ├── productos.db          # ❌ Se borraba en redeploy
  └── static/
      └── img/              # ❌ Se borraba en redeploy
          └── A0001.jpg
```

**Ahora:**
```
/data/                      # ✅ Disco persistente de Render
  ├── productos.db          # ✅ Persiste entre deploys
  └── img/                  # ✅ Persiste entre deploys
      └── A0001.jpg

web_carrito/                # Código fuente (efímero)
  ├── app.py
  ├── config.py
  └── static/
      ├── css/
      ├── js/
      └── img/
          ├── logo.PNG      # Archivos estáticos del proyecto
          └── iconorm.ico
```

### 2. Configuración Actualizada

#### config.py
- `PERSISTENT_DATA_PATH`: Carpeta raíz para datos persistentes (`/data` en producción)
- `DATABASE_PATH`: Base de datos en `/data/productos.db`
- `UPLOAD_FOLDER`: Imágenes en `/data/img`

#### app.py
- Inicialización automática de carpetas persistentes
- Nueva ruta `/uploads/<filename>` para servir imágenes
- Migración automática en desarrollo

### 3. Archivos Modificados

**Backend:**
- `config.py` - Rutas de almacenamiento persistente
- `app.py` - Inicialización y servicio de imágenes

**Frontend:**
- `templates/admin/*.html` - Rutas de imágenes actualizadas
- `static/js/index.js` - Rutas de imágenes actualizadas
- `static/js/carrito.js` - Rutas de imágenes actualizadas

## Configuración en Render

### 1. Crear Disco Persistente

1. Ve a tu servicio en Render Dashboard
2. Click en "Disks" o "Almacenamiento"
3. Crear nuevo disco:
   - **Nombre**: `rmkits-data` (o el que prefieras)
   - **Mount Path**: `/data`
   - **Tamaño**: 1GB (o más según necesites)

### 2. Variables de Entorno

Agregar en Render:
```bash
PERSISTENT_DATA_PATH=/data
```

### 3. Redeploy

1. Guardar cambios
2. Hacer redeploy del servicio
3. La aplicación automáticamente:
   - Creará las carpetas `/data` y `/data/img`
   - Moverá la base de datos si existe
   - Comenzará a usar el almacenamiento persistente

## Desarrollo Local

### Configuración Automática

En desarrollo local (sin la variable de entorno), el sistema usa una carpeta local `data/` en el proyecto:

```bash
# Automático - no requiere configuración
python app.py
```

Las carpetas `data/` y `data/img/` se crean automáticamente.

### Configuración Manual (Opcional)

Si quieres usar una ubicación específica:

```bash
# Linux/Mac
export PERSISTENT_DATA_PATH=/ruta/personalizada

# Windows PowerShell
$env:PERSISTENT_DATA_PATH="C:\ruta\personalizada"

python app.py
```

## Migración de Datos Existentes

Si ya tenías la aplicación funcionando:

### En Desarrollo Local

Las imágenes de `static/img` se copian automáticamente a `data/img` al iniciar la app.

### En Producción (Render)

1. **Primera vez configurando el disco:**
   - El sistema creará la estructura de carpetas
   - Sube manualmente la base de datos y las imágenes iniciales vía SFTP/SCP

2. **Backup de la base de datos:**
   ```bash
   # Descargar backup desde Render
   curl https://tu-app.onrender.com/admin/backup > backup.zip
   ```

3. **Subir imágenes:**
   - Usa SFTP para conectarte al servidor de Render
   - Copia las imágenes a `/data/img/`

## Rutas de Imágenes

### Cliente (Frontend)

**Antes:**
```html
<img src="/static/img/A0001.jpg">
```

**Ahora:**
```html
<img src="/uploads/A0001.jpg">
```

### Servidor (Backend)

**Subir imagen:**
```python
filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
file.save(filepath)
```

**Servir imagen:**
```
GET /uploads/A0001.jpg  →  /data/img/A0001.jpg
```

## Verificación

### Comprobar Configuración

```python
from config import Config
print(f"Datos persistentes: {Config.PERSISTENT_DATA_PATH}")
print(f"Base de datos: {Config.DATABASE_PATH}")
print(f"Imágenes: {Config.UPLOAD_FOLDER}")
```

### En Desarrollo
```
Datos persistentes: /data
Base de datos: /data/productos.db
Imágenes: /data/img
```

### Logs de Inicio

Al iniciar la aplicación, verás:
```
✓ Carpeta persistente verificada: /data
✓ Carpeta de imágenes verificada: /data/img
✓ Imágenes migradas desde static/img
✓ Base de datos movida a: /data/productos.db
```

## Solución de Problemas

### Error: "No such file or directory: /data"

**Causa:** Disco persistente no configurado en Render

**Solución:** 
1. Configurar disco en Render Dashboard
2. Verificar que el mount path sea `/data`
3. Redeploy

### Error: "Permission denied"

**Causa:** Permisos incorrectos en el disco

**Solución:**
```bash
# En Render Shell
chmod -R 755 /data
```

### Las imágenes no se muestran

**Causa:** Rutas incorrectas en el código

**Verificar:**
1. Las imágenes usan `/uploads/` no `/static/img/`
2. Los archivos existen en `/data/img/`
3. La ruta `/uploads/` está registrada en Flask

### La base de datos se borra en redeploy

**Causa:** Disco persistente no montado correctamente

**Verificar:**
1. El disco está creado en Render
2. La variable `PERSISTENT_DATA_PATH=/data` está configurada
3. El código está usando `Config.DATABASE_PATH`

## Notas Importantes

1. **Archivos estáticos del proyecto** (logo, favicon, CSS, JS) siguen en `/static/`
2. **Archivos dinámicos** (productos, imágenes subidas) van en `/data/`
3. **Backups regulares:** Usa la función de backup del admin para descargar todo
4. **Tamaño del disco:** Monitorea el uso y aumenta si es necesario

## Contacto

Para soporte técnico, consultar la documentación de Render:
https://render.com/docs/disks
