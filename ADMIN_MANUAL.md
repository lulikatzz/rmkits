# 🔐 Panel de Administración - RM KITS

## Acceso al Panel

**URL**: `http://tudominio.com/admin/login`

**Credenciales por defecto**:
- Usuario: `admin`
- Contraseña: `rmkits2024`

⚠️ **IMPORTANTE**: Cambiar las credenciales en producción editando `config.py` o usando variables de entorno.

## Funcionalidades

### 📊 Dashboard
- Resumen de estadísticas
- Total de productos
- Productos con/sin stock
- Stock total

### 📦 Gestión de Productos

#### ➕ Crear Producto
1. Click en "Nuevo Producto"
2. Completar formulario:
   - **Código**: Identificador único (requerido)
   - **Título**: Nombre del producto (requerido)
   - **Descripción**: Descripción opcional
   - **Precio**: Precio unitario (requerido)
   - **Mínimo**: Cantidad mínima de compra (requerido)
   - **Múltiplo**: Se vende de a X unidades (requerido)
   - **Stock**: Cantidad disponible (requerido)
   - **Imagen**: Subir foto del producto
   - **Categoría**: Librería o Juguetería/Cotillón
3. Click en "Crear Producto"

#### ✏️ Editar Producto
1. En la lista de productos, click en el botón ✏️
2. Modificar los campos necesarios
3. Para cambiar la imagen, seleccionar nuevo archivo
4. Click en "Guardar Cambios"

#### 🗑️ Eliminar Producto
1. En la lista de productos, click en el botón 🗑️
2. Confirmar la eliminación

### 🔍 Buscar Productos
- Usar la barra de búsqueda en la lista de productos
- Busca en todos los campos (código, título, categoría, etc.)
- Actualización en tiempo real

### 📸 Gestión de Imágenes

**Formatos aceptados**: JPG, PNG, GIF, WEBP  
**Tamaño máximo**: 5MB

Las imágenes se guardan en: `static/img/`

## Validaciones Automáticas

✅ El sistema valida automáticamente:
- Mínimo debe ser ≥ Múltiplo
- Mínimo debe ser múltiplo del valor "Múltiplo"
- Tamaño y formato de imágenes
- Campos requeridos

## Seguridad

### Protección de Rutas
- Todas las rutas admin requieren login
- Sesión con timeout automático
- CSRF protection habilitado

### Cambiar Credenciales

#### Opción 1: Variables de Entorno (Recomendado)
```bash
# Linux/Mac
export ADMIN_USERNAME=tu_usuario
export ADMIN_PASSWORD=tu_contraseña_segura

# Windows PowerShell
$env:ADMIN_USERNAME="tu_usuario"
$env:ADMIN_PASSWORD="tu_contraseña_segura"
```

#### Opción 2: Archivo .env
Crear archivo `.env` en la raíz:
```
ADMIN_USERNAME=tu_usuario
ADMIN_PASSWORD=tu_contraseña_segura
SECRET_KEY=tu_clave_secreta_muy_larga_y_segura
```

#### Opción 3: Editar config.py
```python
ADMIN_USERNAME = 'tu_usuario'
ADMIN_PASSWORD = 'tu_contraseña_segura'
```

## Tips y Mejores Prácticas

### Productos
- Usar códigos descriptivos (ej: LIB001, JUG023)
- Mantener imágenes optimizadas (peso bajo)
- Actualizar stock regularmente
- Usar categorías para mejor organización

### Imágenes
- Usar fondo blanco o transparente
- Tamaño recomendado: 800x800px
- Formato WEBP para mejor rendimiento
- Nombres descriptivos sin espacios

### Stock
- Si stock = 0, el producto no aparece en la tienda
- Configurar mínimos realistas según tus packs
- El múltiplo indica la unidad de venta (ej: caja de 12)

## Atajos de Teclado

En formularios:
- `Tab`: Navegar entre campos
- `Enter`: Enviar formulario (si está en el último campo)
- `Esc`: Volver atrás (con confirmación si hay cambios)

## Preguntas Frecuentes

### ¿Cómo subo múltiples productos?
Usa el script `importar_excel.py` con un archivo Excel.

### ¿Puedo editar varios productos a la vez?
Por ahora no, pero puedes usar el Excel para cambios masivos.

### ¿Qué pasa si borro una imagen?
La imagen se mantiene en el servidor pero no se mostrará en el producto.

### ¿Cómo desactivo un producto sin borrarlo?
Pon el stock en 0, el producto no aparecerá en la tienda.

### ¿Puedo tener varios administradores?
Actualmente hay un solo usuario admin. Para múltiples usuarios, contactar desarrollo.

## Soporte

Para problemas o consultas:
- Revisar logs de la aplicación
- Verificar permisos de carpeta `static/img/`
- Consultar documentación de Flask

## Próximas Funcionalidades

🔜 Planeadas:
- [ ] Importar/Exportar productos desde el panel
- [ ] Edición masiva de precios
- [ ] Historial de cambios
- [ ] Múltiples usuarios admin
- [ ] Categorías personalizadas
- [ ] Gestión de pedidos desde el panel

---

**Versión**: 1.0  
**Última actualización**: Diciembre 2025
