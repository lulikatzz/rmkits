"""
Aplicación web de carrito de compras mayorista - RM KITS
"""
from flask import Flask, render_template, request, jsonify, redirect, session, flash, url_for, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import urllib.parse
import logging
import os
from contextlib import contextmanager
from functools import wraps
from datetime import datetime
from config import Config
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl import load_workbook
from io import BytesIO
import zipfile
import shutil

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
app.config.from_object(Config)


# Context manager para manejo seguro de base de datos
@contextmanager
def get_db_connection():
    """Context manager para conexiones a la base de datos"""
    conn = None
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Error de base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()


@app.before_request
def before_request():
    """Forzar HTTPS en producción"""
    if request.headers.get("X-Forwarded-Proto") == "http":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)


def get_productos():
    """Obtiene todos los productos activos de la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM producto WHERE stock > 0 AND activo = 1")
            filas = cursor.fetchall()
            productos = [dict(fila) for fila in filas]
            return productos
    except Exception as e:
        logger.error(f"Error al obtener productos: {e}")
        return []


@app.route("/")
def index():
    """Página principal con lista de productos"""
    try:
        productos = get_productos()
        return render_template(
            "index.html",
            productos=productos,
            config={
                'pedido_minimo': Config.PEDIDO_MINIMO,
                'whatsapp': Config.WHATSAPP_NUMBER
            }
        )
    except Exception as e:
        logger.error(f"Error en página principal: {e}")
        return render_template("error.html", mensaje="Error al cargar productos"), 500


@app.route("/carrito")
def carrito_view():
    """Página del carrito de compras"""
    try:
        # Obtener productos actualizados de la BD para sincronizar precios, stock e imágenes
        # Usar código como clave porque los IDs cambian al reimportar Excel
        productos_actualizados = {}
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, codigo, precio, stock, minimo, multiplo, imagen FROM producto WHERE activo = 1")
                for row in cursor.fetchall():
                    productos_actualizados[row['codigo']] = {
                        'id': row['id'],
                        'precio': row['precio'],
                        'stock': row['stock'],
                        'minimo': row['minimo'],
                        'multiplo': row['multiplo'],
                        'imagen': row['imagen']
                    }
        except Exception as db_error:
            logger.warning(f"Error al obtener precios actualizados: {db_error}")
        
        return render_template(
            "carrito.html",
            productos_actualizados=productos_actualizados,
            config={
                'pedido_minimo': Config.PEDIDO_MINIMO,
                'whatsapp': Config.WHATSAPP_NUMBER,
                'local_direccion': Config.LOCAL_DIRECCION,
                'local_horarios': Config.LOCAL_HORARIOS,
                'envio_caba': Config.ENVIO_CABA,
                'envio_gba': Config.ENVIO_GBA
            }
        )
    except Exception as e:
        logger.error(f"Error en página de carrito: {e}")
        return render_template("error.html", mensaje="Error al cargar carrito"), 500


@app.route("/enviar_pedido", methods=["POST"])
def enviar_pedido():
    """
    API endpoint para procesar pedidos
    (Actualmente no se usa, pero se mantiene por compatibilidad)
    """
    try:
        datos = request.json
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
        
        total = datos.get("total", 0)
        items = datos.get("items", [])

        if total < Config.PEDIDO_MINIMO:
            return jsonify({
                "error": f"El pedido debe superar los ${Config.PEDIDO_MINIMO:,.0f}"
            }), 400

        # Construir mensaje
        lines = ["Pedido mayorista RM KITS:"]
        for item in items:
            codigo = item.get('codigo', '')
            titulo = item.get('titulo', '')
            cantidad = item.get('cantidad', 0)
            precio = item.get('precio', 0)
            lines.append(f"{codigo} - {titulo} - Cantidad: {cantidad} - Precio unitario: ${precio}")
        lines.append(f"TOTAL: ${total}")

        mensaje = "\n".join(lines)
        encoded = urllib.parse.quote(mensaje)
        url = f"https://wa.me/{Config.WHATSAPP_NUMBER}?text={encoded}"

        return jsonify({"url": url})
    
    except Exception as e:
        logger.error(f"Error al enviar pedido: {e}")
        return jsonify({"error": "Error al procesar el pedido"}), 500


@app.errorhandler(404)
def page_not_found(e):
    """Página no encontrada"""
    return render_template("error.html", mensaje="Página no encontrada"), 404


@app.errorhandler(500)
def internal_error(e):
    """Error interno del servidor"""
    logger.error(f"Error 500: {e}")
    return render_template("error.html", mensaje="Error interno del servidor"), 500


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def generar_codigo_producto():
    """Genera el siguiente código de producto automáticamente (formato A0XXX)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Obtener el último código que empiece con 'A0'
            cursor.execute("""
                SELECT codigo FROM producto 
                WHERE codigo LIKE 'A0%' 
                ORDER BY CAST(SUBSTR(codigo, 2) AS INTEGER) DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                ultimo_codigo = result['codigo']
                # Extraer el número del código (A0222 -> 222)
                numero = int(ultimo_codigo[1:])
                nuevo_numero = numero + 1
            else:
                # Si no hay códigos, empezar desde 1
                nuevo_numero = 1
            
            # Formatear el nuevo código (A0001, A0222, etc)
            nuevo_codigo = f"A{nuevo_numero:04d}"
            return nuevo_codigo
    except Exception as e:
        logger.error(f"Error al generar código: {e}")
        return "A0001"


def init_database():
    """Inicializa las tablas necesarias en la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Crear tabla productos_nuevos si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS producto_nuevo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (producto_id) REFERENCES producto(id)
                )
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"Error al inicializar base de datos: {e}")


# Inicializar base de datos al arrancar la app
init_database()

# =============================================================================
# PANEL DE ADMINISTRACIÓN
# =============================================================================

def login_required(f):
    """Decorador para requerir login en rutas de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Debes iniciar sesión para acceder al panel de administración', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Login del administrador"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Verificar si el usuario existe y la contraseña es correcta
        if username in Config.ADMIN_USERS and Config.ADMIN_USERS[username] == password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    """Cerrar sesión del administrador"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('admin_login'))


@app.route("/admin")
@login_required
def admin_dashboard():
    """Dashboard principal del admin"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Estadísticas
            cursor.execute("SELECT COUNT(*) FROM producto")
            total_productos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM producto WHERE stock > 0")
            productos_con_stock = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM producto WHERE stock = 0")
            productos_sin_stock = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(stock) FROM producto")
            stock_total = cursor.fetchone()[0] or 0
            
            return render_template("admin/dashboard.html",
                                 total_productos=total_productos,
                                 productos_con_stock=productos_con_stock,
                                 productos_sin_stock=productos_sin_stock,
                                 stock_total=stock_total)
    except Exception as e:
        logger.error(f"Error en dashboard: {e}")
        flash('Error al cargar el dashboard', 'error')
        return redirect(url_for('admin_login'))


@app.route("/admin/productos")
@login_required
def admin_productos():
    """Lista de productos en el admin"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM producto ORDER BY id DESC")
            productos = [dict(row) for row in cursor.fetchall()]
            
            # Obtener categorías únicas
            cursor.execute("SELECT DISTINCT categoria FROM producto WHERE categoria IS NOT NULL AND categoria != '' ORDER BY categoria")
            categorias = [row['categoria'] for row in cursor.fetchall()]
            
            return render_template("admin/productos.html", productos=productos, categorias=categorias)
    except Exception as e:
        logger.error(f"Error al obtener productos: {e}")
        flash('Error al cargar productos', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route("/admin/descargar-excel")
@login_required
def admin_descargar_excel():
    """Descargar lista de productos como Excel"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM producto ORDER BY categoria, titulo")
            productos = [dict(row) for row in cursor.fetchall()]
        
        # Crear workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Productos"
        
        # Estilos
        header_fill = PatternFill(start_color="6a1b9a", end_color="6a1b9a", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Encabezados
        headers = ["ID", "Código", "Título", "Descripción", "Precio", "Mínimo", "Múltiplo", "Stock", "Categoría", "Activo"]
        ws.append(headers)
        
        # Aplicar estilos a encabezados
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Agregar datos
        for producto in productos:
            ws.append([
                producto.get('id', ''),
                producto.get('codigo', ''),
                producto.get('titulo', ''),
                producto.get('descripcion', ''),
                producto.get('precio', 0),
                producto.get('minimo', 1),
                producto.get('multiplo', 1),
                producto.get('stock', 0),
                producto.get('categoria', ''),
                'Sí' if producto.get('activo', 1) == 1 else 'No'
            ])
        
        # Ajustar ancho de columnas
        column_widths = [8, 15, 40, 50, 12, 10, 10, 10, 20, 10]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[chr(64 + i)].width = width
        
        # Guardar en memoria
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generar nombre de archivo con fecha
        filename = f"productos_rmkits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error al generar Excel: {e}")
        flash('Error al generar archivo Excel', 'error')
        return redirect(url_for('admin_productos'))


@app.route("/admin/subir-excel", methods=["POST"])
@login_required
def admin_subir_excel():
    """Subir archivo Excel para actualizar productos"""
    try:
        if 'archivo' not in request.files:
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('admin_productos'))
        
        file = request.files['archivo']
        
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'error')
            return redirect(url_for('admin_productos'))
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('El archivo debe ser un Excel (.xlsx o .xls)', 'error')
            return redirect(url_for('admin_productos'))
        
        # Leer el archivo Excel
        wb = load_workbook(file)
        ws = wb.active
        
        # Verificar encabezados
        headers = [cell.value for cell in ws[1]]
        expected_headers = ["ID", "Código", "Título", "Descripción", "Precio", "Mínimo", "Múltiplo", "Stock", "Categoría", "Activo"]
        
        if headers != expected_headers:
            flash(f'El formato del archivo no es correcto. Se esperan las columnas: {", ".join(expected_headers)}', 'error')
            return redirect(url_for('admin_productos'))
        
        # Procesar filas
        productos_actualizados = 0
        productos_creados = 0
        errores = []
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    id_producto = row[0]
                    codigo = row[1]
                    titulo = row[2]
                    descripcion = row[3] or ''
                    precio = float(row[4]) if row[4] else 0
                    minimo = int(row[5]) if row[5] else 1
                    multiplo = int(row[6]) if row[6] else 1
                    stock = int(row[7]) if row[7] else 0
                    categoria = row[8] or ''
                    activo = 1 if row[9] in ['Sí', 'Si', 'SI', 'SÍ', 1, '1', True] else 0
                    
                    # Verificar si el producto existe por ID o código
                    if id_producto:
                        cursor.execute("SELECT id FROM producto WHERE id = ?", (id_producto,))
                        existe = cursor.fetchone()
                        
                        if existe:
                            # Actualizar producto existente
                            cursor.execute("""
                                UPDATE producto 
                                SET codigo=?, titulo=?, descripcion=?, precio=?, minimo=?, multiplo=?, stock=?, categoria=?, activo=?
                                WHERE id=?
                            """, (codigo, titulo, descripcion, precio, minimo, multiplo, stock, categoria, activo, id_producto))
                            productos_actualizados += 1
                        else:
                            # Crear nuevo producto con ID específico
                            cursor.execute("""
                                INSERT INTO producto (id, codigo, titulo, descripcion, precio, minimo, multiplo, stock, imagen, categoria, activo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?)
                            """, (id_producto, codigo, titulo, descripcion, precio, minimo, multiplo, stock, categoria, activo))
                            productos_creados += 1
                    else:
                        # Buscar por código si no hay ID
                        cursor.execute("SELECT id FROM producto WHERE codigo = ?", (codigo,))
                        existe = cursor.fetchone()
                        
                        if existe:
                            # Actualizar producto existente
                            cursor.execute("""
                                UPDATE producto 
                                SET titulo=?, descripcion=?, precio=?, minimo=?, multiplo=?, stock=?, categoria=?, activo=?
                                WHERE codigo=?
                            """, (titulo, descripcion, precio, minimo, multiplo, stock, categoria, activo, codigo))
                            productos_actualizados += 1
                        else:
                            # Crear nuevo producto
                            cursor.execute("""
                                INSERT INTO producto (codigo, titulo, descripcion, precio, minimo, multiplo, stock, imagen, categoria, activo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, '', ?, ?)
                            """, (codigo, titulo, descripcion, precio, minimo, multiplo, stock, categoria, activo))
                            productos_creados += 1
                
                except Exception as e:
                    errores.append(f"Fila {row_idx}: {str(e)}")
            
            conn.commit()
        
        # Mensaje de resultado
        mensaje = f'✅ Procesamiento completado: {productos_actualizados} actualizados, {productos_creados} creados'
        if errores:
            mensaje += f'. ⚠️ {len(errores)} errores encontrados'
            logger.warning(f"Errores al importar Excel: {errores}")
        
        flash(mensaje, 'success' if not errores else 'warning')
        return redirect(url_for('admin_productos'))
    
    except Exception as e:
        logger.error(f"Error al procesar Excel: {e}")
        flash(f'Error al procesar archivo: {str(e)}', 'error')
        return redirect(url_for('admin_productos'))


@app.route("/admin/pedidos")
@login_required
def admin_pedidos():
    """Ver lista de pedidos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pedido ORDER BY fecha DESC")
            pedidos = [dict(row) for row in cursor.fetchall()]
            
            return render_template("admin/pedidos.html", pedidos=pedidos)
    except Exception as e:
        logger.error(f"Error al obtener pedidos: {e}")
        flash('Error al cargar pedidos', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route("/admin/pedido/<int:id>/estado", methods=["POST"])
@login_required
def admin_pedido_estado(id):
    """Cambiar estado de un pedido"""
    try:
        data = request.get_json()
        nuevo_estado = data.get('estado')
        
        estados_validos = ['pendiente', 'procesando', 'completado', 'cancelado']
        if nuevo_estado not in estados_validos:
            return jsonify({'success': False, 'error': 'Estado inválido'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE pedido SET estado = ? WHERE id = ?", (nuevo_estado, id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error al cambiar estado del pedido: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/admin/pedidos/limpiar", methods=["POST"])
@login_required
def admin_limpiar_pedidos():
    """Eliminar todos los pedidos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pedido")
            conn.commit()
            cantidad = cursor.rowcount
        
        flash(f'{cantidad} pedido(s) eliminado(s)', 'success')
        return jsonify({'success': True, 'cantidad': cantidad})
    
    except Exception as e:
        logger.error(f"Error al limpiar pedidos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/guardar-pedido", methods=["POST"])
def guardar_pedido():
    """Guardar pedido en la base de datos"""
    try:
        data = request.get_json()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si la tabla existe y tiene todas las columnas necesarias
            try:
                cursor.execute("SELECT envio_direccion FROM pedido LIMIT 1")
            except sqlite3.OperationalError:
                # La tabla no existe o no tiene las columnas nuevas, recrearla
                logger.info("Recreando tabla de pedidos con nuevas columnas")
                cursor.execute("DROP TABLE IF EXISTS pedido")
                cursor.execute("""
                    CREATE TABLE pedido (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cliente_nombre TEXT NOT NULL,
                        cliente_cuit TEXT,
                        cliente_telefono TEXT,
                        cliente_email TEXT,
                        cliente_direccion TEXT,
                        metodo_entrega TEXT,
                        envio_direccion TEXT,
                        envio_localidad TEXT,
                        envio_provincia TEXT,
                        envio_cp TEXT,
                        envio_nombre_destinatario TEXT,
                        envio_referencias TEXT,
                        productos TEXT NOT NULL,
                        total REAL NOT NULL,
                        estado TEXT DEFAULT 'pendiente'
                    )
                """)
            
            # Insertar pedido
            cursor.execute("""
                INSERT INTO pedido (cliente_nombre, cliente_cuit, cliente_telefono, cliente_email, 
                                   cliente_direccion, metodo_entrega, envio_direccion, envio_localidad,
                                   envio_provincia, envio_cp, envio_nombre_destinatario, envio_referencias,
                                   productos, total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('nombre'),
                data.get('cuit'),
                data.get('telefono'),
                data.get('email'),
                data.get('direccion'),
                data.get('metodo_entrega'),
                data.get('envio_direccion'),
                data.get('envio_localidad'),
                data.get('envio_provincia'),
                data.get('envio_cp'),
                data.get('envio_nombre_destinatario'),
                data.get('envio_referencias'),
                data.get('productos'),  # JSON string con los productos
                data.get('total')
            ))
            
            pedido_id = cursor.lastrowid
            conn.commit()
        
        return jsonify({'success': True, 'pedido_id': pedido_id})
    
    except Exception as e:
        logger.error(f"Error al guardar pedido: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/admin/lista-precios")
@login_required
def admin_lista_precios():
    """Lista de precios para imprimir"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM producto WHERE stock > 0 ORDER BY categoria, titulo")
            productos = [dict(row) for row in cursor.fetchall()]
            
            # Obtener categorías únicas
            cursor.execute("SELECT DISTINCT categoria FROM producto WHERE categoria IS NOT NULL AND categoria != '' ORDER BY categoria")
            categorias = [row['categoria'] for row in cursor.fetchall()]
            
            return render_template("admin/lista_precios.html", productos=productos, categorias=categorias, now=datetime.now())
    except Exception as e:
        logger.error(f"Error al obtener lista de precios: {e}")
        flash('Error al cargar lista de precios', 'error')
        return redirect(url_for('admin_productos'))



@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
@login_required
def admin_producto_nuevo():
    """Crear nuevo producto"""
    if request.method == "POST":
        try:
            # Generar código automáticamente primero
            codigo_automatico = generar_codigo_producto()
            
            # Manejar imagen
            imagen_filename = ""
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file and file.filename and allowed_file(file.filename):
                    # Obtener la extensión del archivo original
                    extension = os.path.splitext(file.filename)[1].lower()
                    # Renombrar con el código del producto
                    imagen_filename = f"{codigo_automatico}{extension}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename)
                    file.save(filepath)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO producto (codigo, titulo, descripcion, precio, minimo, multiplo, stock, imagen, categoria, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    codigo_automatico,  # Usar código generado automáticamente
                    request.form.get('titulo'),
                    request.form.get('descripcion', ''),
                    float(request.form.get('precio', 0)),
                    int(request.form.get('minimo', 1)),
                    int(request.form.get('multiplo', 1)),
                    int(request.form.get('stock', 0)),
                    imagen_filename,
                    request.form.get('categoria', ''),
                    1  # Por defecto activo
                ))
                
                # Obtener el ID del producto recién insertado
                producto_id = cursor.lastrowid
                
                # Agregar a la tabla de productos nuevos
                cursor.execute("""
                    INSERT INTO producto_nuevo (producto_id)
                    VALUES (?)
                """, (producto_id,))
                
                conn.commit()
            
            flash(f'Producto creado exitosamente con código {codigo_automatico}', 'success')
            return redirect(url_for('admin_productos'))
        except Exception as e:
            logger.error(f"Error al crear producto: {e}")
            flash(f'Error al crear producto: {str(e)}', 'error')
    
    # Generar el código que se usará para el nuevo producto
    nuevo_codigo = generar_codigo_producto()
    return render_template("admin/producto_form.html", producto=None, action="Crear", nuevo_codigo=nuevo_codigo)


@app.route("/admin/producto/<int:id>/editar", methods=["GET", "POST"])
@login_required
def admin_producto_editar(id):
    """Editar producto existente"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if request.method == "POST":
                # Obtener el código del producto
                codigo_producto = request.form.get('codigo')
                
                # Manejar imagen
                imagen_filename = request.form.get('imagen_actual', '')
                if 'imagen' in request.files:
                    file = request.files['imagen']
                    if file and file.filename and allowed_file(file.filename):
                        # Obtener la extensión del archivo original
                        extension = os.path.splitext(file.filename)[1].lower()
                        # Renombrar con el código del producto
                        imagen_filename = f"{codigo_producto}{extension}"
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename)
                        file.save(filepath)
                        
                        # Eliminar imagen anterior si existe y es diferente
                        imagen_anterior = request.form.get('imagen_actual', '')
                        if imagen_anterior and imagen_anterior != imagen_filename:
                            ruta_anterior = os.path.join(app.config['UPLOAD_FOLDER'], imagen_anterior)
                            if os.path.exists(ruta_anterior):
                                try:
                                    os.remove(ruta_anterior)
                                except Exception as e:
                                    logger.warning(f"No se pudo eliminar la imagen anterior: {e}")
                
                cursor.execute("""
                    UPDATE producto 
                    SET codigo=?, titulo=?, descripcion=?, precio=?, minimo=?, multiplo=?, stock=?, imagen=?, categoria=?
                    WHERE id=?
                """, (
                    request.form.get('codigo'),
                    request.form.get('titulo'),
                    request.form.get('descripcion', ''),
                    float(request.form.get('precio', 0)),
                    int(request.form.get('minimo', 1)),
                    int(request.form.get('multiplo', 1)),
                    int(request.form.get('stock', 0)),
                    imagen_filename,
                    request.form.get('categoria', ''),
                    id
                ))
                conn.commit()
                
                flash('Producto actualizado exitosamente', 'success')
                return redirect(url_for('admin_productos'))
            
            # GET - mostrar formulario
            cursor.execute("SELECT * FROM producto WHERE id=?", (id,))
            producto = dict(cursor.fetchone())
            return render_template("admin/producto_form.html", producto=producto, action="Editar")
    
    except Exception as e:
        logger.error(f"Error al editar producto: {e}")
        flash(f'Error al editar producto: {str(e)}', 'error')
        return redirect(url_for('admin_productos'))


@app.route("/admin/producto/actualizar-precio", methods=["POST"])
@login_required
def admin_producto_actualizar_precio():
    """Actualizar precio de un producto vía AJAX"""
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        nuevo_precio = data.get('precio')
        
        if not producto_id or nuevo_precio is None:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        if nuevo_precio < 0:
            return jsonify({'success': False, 'error': 'El precio no puede ser negativo'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE producto SET precio = ? WHERE id = ?", (nuevo_precio, producto_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        return jsonify({'success': True, 'precio': nuevo_precio})
    
    except Exception as e:
        logger.error(f"Error al actualizar precio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/admin/producto/toggle-activo", methods=["POST"])
@login_required
def admin_producto_toggle_activo():
    """Activar/desactivar un producto vía AJAX"""
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        activo = data.get('activo')
        
        if not producto_id or activo is None:
            return jsonify({'success': False, 'error': 'Datos incompletos'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE producto SET activo = ? WHERE id = ?", (activo, producto_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        return jsonify({'success': True, 'activo': activo})
    
    except Exception as e:
        logger.error(f"Error al actualizar estado del producto: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/admin/producto/<int:id>/eliminar", methods=["POST"])
@login_required
def admin_producto_eliminar(id):
    """Eliminar producto"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM producto WHERE id=?", (id,))
            conn.commit()
        
        flash('Producto eliminado exitosamente', 'success')
    except Exception as e:
        logger.error(f"Error al eliminar producto: {e}")
        flash(f'Error al eliminar producto: {str(e)}', 'error')
    
    return redirect(url_for('admin_productos'))


@app.route("/admin/api/productos")
@login_required
def admin_api_productos():
    """API para obtener productos (para tablas dinámicas)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM producto ORDER BY id DESC")
            productos = [dict(row) for row in cursor.fetchall()]
            return jsonify(productos)
    except Exception as e:
        logger.error(f"Error en API productos: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/productos-nuevos")
@login_required
def admin_productos_nuevos():
    """Muestra la tabla de productos nuevos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, pn.fecha_agregado 
                FROM producto p
                INNER JOIN producto_nuevo pn ON p.id = pn.producto_id
                ORDER BY pn.fecha_agregado DESC
            """)
            productos_nuevos = [dict(row) for row in cursor.fetchall()]
            
            return render_template("admin/productos_nuevos.html", productos=productos_nuevos)
    except Exception as e:
        logger.error(f"Error al obtener productos nuevos: {e}")
        flash('Error al cargar productos nuevos', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route("/admin/productos-nuevos/descargar-imagenes")
@login_required
def admin_descargar_imagenes_nuevos():
    """Descarga un ZIP con todas las imágenes de productos nuevos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.codigo, p.imagen 
                FROM producto p
                INNER JOIN producto_nuevo pn ON p.id = pn.producto_id
                WHERE p.imagen IS NOT NULL AND p.imagen != ''
            """)
            productos = cursor.fetchall()
        
        if not productos:
            flash('No hay productos nuevos con imágenes', 'warning')
            return redirect(url_for('admin_productos_nuevos'))
        
        # Crear un archivo ZIP en memoria
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for producto in productos:
                codigo = producto['codigo']
                imagen = producto['imagen']
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], imagen)
                
                if os.path.exists(imagen_path):
                    # Obtener la extensión del archivo
                    extension = os.path.splitext(imagen)[1].lower()
                    # Agregar archivo al ZIP con el código del producto como nombre
                    nombre_archivo = f"{codigo}{extension}"
                    zipf.write(imagen_path, nombre_archivo)
        
        memory_file.seek(0)
        
        # Generar nombre del archivo con fecha
        fecha_actual = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_zip = f"imagenes_productos_nuevos_{fecha_actual}.zip"
        
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=nombre_zip
        )
    
    except Exception as e:
        logger.error(f"Error al descargar imágenes: {e}")
        flash(f'Error al descargar imágenes: {str(e)}', 'error')
        return redirect(url_for('admin_productos_nuevos'))


@app.route("/admin/productos-nuevos/<int:id>/quitar", methods=["POST"])
@login_required
def admin_quitar_producto_nuevo(id):
    """Quita un producto de la tabla de productos nuevos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM producto_nuevo WHERE producto_id = ?", (id,))
            conn.commit()
        
        flash('Producto quitado de la lista de nuevos', 'success')
    except Exception as e:
        logger.error(f"Error al quitar producto nuevo: {e}")
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_productos_nuevos'))


if __name__ == "__main__":
    app.run(debug=Config.DEBUG)
