# Nuevas Funcionalidades - Sistema de Productos

## 1. Código Automático de Productos

### Descripción
Cuando creas un nuevo producto desde el panel de administración, el código se genera automáticamente siguiendo el formato `A0XXX`.

### Funcionamiento
- Si tienes 221 productos, el próximo código será **A0222**
- El código se genera automáticamente al crear un producto
- **No puedes modificar el código** al crear un producto nuevo (el campo está deshabilitado)
- Solo puedes editar el código de productos existentes

### Ejemplo
```
Productos existentes: A0001, A0002, ..., A0221
Nuevo producto → Código automático: A0222
```

---

## 2. Tabla de Productos Nuevos

### Descripción
Una nueva sección en el panel de administración que muestra únicamente los productos que han sido creados manualmente (no importados desde Excel).

### Acceso
- **Ubicación:** Panel Admin → Productos Nuevos (🆕)
- **URL:** `/admin/productos-nuevos`

### Características

#### Vista de Tabla
La tabla muestra:
- ✅ Imagen del producto
- ✅ Código automático generado
- ✅ Título y descripción
- ✅ Precio actual
- ✅ Stock disponible
- ✅ Categoría
- ✅ Fecha en que fue agregado
- ✅ Acciones (Editar / Quitar de lista)

#### Botón "Descargar Imágenes"
- 📥 Descarga un archivo **ZIP** con todas las imágenes de productos nuevos
- Las imágenes se nombran con el formato: `{CODIGO}_{nombre_original}`
- Ejemplo: `A0222_producto.jpg`, `A0223_articulo.png`
- El archivo ZIP se descarga con fecha y hora: `imagenes_productos_nuevos_20260121_143025.zip`

#### Quitar de la Lista
- Puedes quitar productos de la tabla de "Productos Nuevos"
- El producto NO se elimina de la base de datos, solo de esta vista especial
- Útil para mantener solo los productos realmente nuevos que necesitas revisar

---

## 3. Flujo de Trabajo

### Crear Nuevo Producto
1. Ve a **Productos** → **Nuevo Producto**
2. El código se muestra automáticamente (ej: A0222)
3. Completa los demás campos (título, precio, stock, etc.)
4. Sube una imagen (opcional)
5. Guarda el producto
6. El producto aparecerá automáticamente en "Productos Nuevos"

### Descargar Imágenes de Productos Nuevos
1. Ve a **Productos Nuevos**
2. Haz clic en **📥 Descargar Imágenes**
3. Se descargará un ZIP con todas las imágenes
4. Las imágenes están nombradas por código de producto

### Gestionar Productos Nuevos
- **Editar:** Modifica cualquier campo del producto
- **Quitar:** Remueve de la lista de nuevos (no elimina el producto)
- Los productos importados desde Excel NO aparecen en esta tabla

---

## 4. Detalles Técnicos

### Base de Datos
Nueva tabla: `producto_nuevo`
```sql
CREATE TABLE producto_nuevo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES producto(id)
)
```

### Rutas Nuevas
- `GET /admin/productos-nuevos` - Vista de productos nuevos
- `GET /admin/productos-nuevos/descargar-imagenes` - Descarga ZIP de imágenes
- `POST /admin/productos-nuevos/<id>/quitar` - Quita producto de la lista

### Funciones Nuevas en app.py
- `generar_codigo_producto()` - Genera el siguiente código automáticamente
- `init_database()` - Inicializa las tablas necesarias

---

## 5. Notas Importantes

⚠️ **El código solo se genera automáticamente para productos NUEVOS**
- Los productos existentes mantienen su código original
- Solo al editar un producto existente puedes modificar su código

⚠️ **Productos importados vs. Productos creados manualmente**
- Los productos importados desde Excel NO aparecen en "Productos Nuevos"
- Solo los productos creados desde el panel admin se registran como nuevos

✅ **Beneficios**
- Evita códigos duplicados
- Mantiene un orden secuencial automático
- Facilita la gestión de productos recién agregados
- Permite descargar imágenes en lote

---

**Fecha de implementación:** 21 de Enero, 2026
**Versión:** 2.0
