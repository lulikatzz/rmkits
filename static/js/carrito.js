/**
 * Script para la página del carrito - RM KITS
 */

// Constantes
const STORAGE_KEY = "rmkits_carrito";
const WHATSAPP_NUMERO = "5491158573906";

// Estado
let carrito = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");

// Precios actualizados desde el servidor (se inicializa desde el template)
window.productosActualizados = window.productosActualizados || {};

// =============================================================================
// UTILIDADES
// =============================================================================

/**
 * Muestra alerta con SweetAlert2
 */
function alertBox({ title = "", text = "", icon = "info", confirmText = "Aceptar" } = {}) {
  return Swal.fire({
    title,
    text,
    icon,
    confirmButtonText: confirmText,
    confirmButtonColor: "#6a1b9a"
  });
}

/**
 * Muestra toast notification
 */
function toast(title, icon = "success") {
  return Swal.fire({
    toast: true,
    position: "top-end",
    showConfirmButton: false,
    timer: 2000,
    timerProgressBar: true,
    title,
    icon
  });
}

/**
 * Formatea número como moneda argentina
 */
function formatearMoneda(n) {
  return `$${n.toLocaleString("es-AR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  })}`;
}

/**
 * Calcula el total del carrito
 */
function calcularTotal() {
  return carrito.reduce((sum, p) => sum + p.precio * p.cantidad, 0);
}

/**
 * Formatea el total como string
 */
function formatearTotal() {
  return calcularTotal().toLocaleString("es-AR");
}

/**
 * Guarda el carrito en localStorage
 */
function guardar() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(carrito));
}

// =============================================================================
// VALIDACIÓN Y CORRECCIÓN DE CANTIDADES
// =============================================================================

/**
 * Corrige un valor según mínimo, máximo y múltiplo
 */
function corregirValor(raw, min, step, max) {
  min = Math.max(1, parseInt(min, 10) || 1);
  step = Math.max(1, parseInt(step, 10) || 1);
  max = (parseInt(max, 10) > 0) ? parseInt(max, 10) : Infinity;

  let v = parseInt(raw, 10);
  if (isNaN(v)) return min;
  if (v < min) return min;
  if (v > max) return max;
  if (step === 1) return v;

  // Redondeo hacia arriba al múltiplo desde 'min'
  let k = Math.ceil((v - min) / step);
  if (k < 0) k = 0;
  let w = min + k * step;
  if (w > max) w = max;

  return w;
}

/**
 * Normaliza un item del carrito
 */
function normalizarItem(p) {
  const multiplo = Math.max(1, parseInt(p.multiplo, 10) || 1);
  const minimo = Math.max(multiplo, parseInt(p.minimo, 10) || multiplo);
  const maximo = (Number.isFinite(parseInt(p.maximo, 10)) && parseInt(p.maximo, 10) > 0) 
    ? parseInt(p.maximo, 10) 
    : null;

  const cantOk = corregirValor(p.cantidad, minimo, multiplo, maximo ?? Infinity);
  return { ...p, multiplo, minimo, maximo, cantidad: cantOk };
}

// =============================================================================
// MIGRACIÓN Y VALIDACIÓN DEL CARRITO
// =============================================================================

/**
 * Migración defensiva: asegurar multiplo, minimo y maximo válidos
 */
function migrarCarrito() {
  let huboMigracion = false;
  
  carrito = carrito.map(p => {
    const nuevo = { ...p };

    if (nuevo.multiplo == null || isNaN(parseInt(nuevo.multiplo, 10))) {
      nuevo.multiplo = 1;
      huboMigracion = true;
    }
    
    if (nuevo.minimo == null || isNaN(parseInt(nuevo.minimo, 10))) {
      nuevo.minimo = 1;
      huboMigracion = true;
    }

    const rawMax = (nuevo.maximo ?? nuevo.stock ?? null);
    if (rawMax == null || !(parseInt(rawMax, 10) > 0)) {
      nuevo.maximo = null;
    } else {
      nuevo.maximo = parseInt(rawMax, 10);
    }

    nuevo.multiplo = parseInt(nuevo.multiplo, 10);
    nuevo.minimo = parseInt(nuevo.minimo, 10);
    return nuevo;
  });
  
  if (huboMigracion) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(carrito));
  }
}

// =============================================================================
// RENDERIZADO DEL CARRITO
// =============================================================================

/**
 * Actualiza el resumen del carrito
 */
function updateResumen() {
  document.getElementById("total").textContent = formatearMoneda(calcularTotal());
  document.getElementById("alerta").style.display = calcularTotal() < 200000 ? "block" : "none";
}

/**
 * Sincroniza precios del carrito con los precios actuales de la BD
 */
function sincronizarPrecios() {
  let huboActualizacion = false;
  let productosEliminados = 0;
  const productosActualizados = window.productosActualizados || {};
  
  console.log("🔄 Sincronizando precios...");
  console.log("Productos en carrito:", carrito.length);
  console.log("Productos actualizados desde BD:", Object.keys(productosActualizados).length);
  
  if (Object.keys(productosActualizados).length === 0) {
    console.warn("⚠️ No hay productos actualizados desde la BD");
    return;
  }
  
  // Filtrar productos desactivados y actualizar los activos
  carrito = carrito.filter(item => {
    // Buscar por código (más confiable que ID porque no cambia al reimportar)
    const actualizado = productosActualizados[item.codigo];
    if (actualizado) {
      const idAnterior = item.id;
      const precioAnterior = item.precio;
      const imagenAnterior = item.imagen;
      
      // Siempre actualizar todos los campos desde la BD
      Object.assign(item, {
        id: actualizado.id,  // Actualizar ID en caso de reimportación
        precio: actualizado.precio,
        stock: actualizado.stock,
        minimo: actualizado.minimo,
        multiplo: actualizado.multiplo,
        imagen: actualizado.imagen
      });
      
      // Detectar cambios
      if (idAnterior !== actualizado.id) {
        console.log(`🆔 ID actualizado - ${item.titulo}: ${idAnterior} → ${actualizado.id}`);
        huboActualizacion = true;
      }
      if (precioAnterior !== actualizado.precio) {
        console.log(`💰 Precio actualizado - ${item.titulo}: $${precioAnterior} → $${actualizado.precio}`);
        huboActualizacion = true;
      }
      if (imagenAnterior !== actualizado.imagen) {
        console.log(`🖼️ Imagen actualizada - ${item.titulo}: ${imagenAnterior} → ${actualizado.imagen}`);
      }
      
      return true; // Mantener el producto en el carrito
    } else {
      console.log(`🗑️ Producto eliminado del carrito (desactivado o no disponible) - ${item.titulo} (${item.codigo})`);
      productosEliminados++;
      return false; // Eliminar del carrito
    }
  });
  
  // Siempre guardar para asegurar que los cambios persisten
  guardar();
  
  if (productosEliminados > 0) {
    toast(`${productosEliminados} producto(s) eliminado(s) del carrito (ya no disponibles)`, "info");
  } else if (huboActualizacion) {
    toast("Productos actualizados", "info");
  }
  
  console.log("✅ Sincronización completada");
}

/**
 * Renderiza los items del carrito
 */
function renderCarrito() {
  const cont = document.getElementById("lista-carrito");
  cont.innerHTML = "";

  if (carrito.length === 0) {
    cont.innerHTML = `
      <div class="carrito-vacio">
        <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="9" cy="21" r="1"/>
          <circle cx="20" cy="21" r="1"/>
          <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
        </svg>
        <h3>Tu carrito está vacío</h3>
        <p>Agrega productos desde el catálogo para comenzar tu pedido</p>
        <a href="/" class="btn-volver-tienda">Ver productos</a>
      </div>
    `;
    updateResumen();
    return;
  }

  carrito.forEach((p, idx) => {
    const step = p.multiplo || 1;
    const min = p.minimo || step || 1;
    const max = (p.maximo ?? null);

    const fila = document.createElement("div");
    fila.className = "cart-item";
    
    // Detectar si el precio fue actualizado
    const productosActualizados = window.productosActualizados || {};
    const actualizado = productosActualizados[p.id];
    const precioActualizado = actualizado && actualizado.precio !== p.precio;
    
    fila.innerHTML = `
      <div class="cart-item-imagen">
        ${p.imagen ? `<img src="/static/img/${p.imagen}" alt="${p.titulo}" onerror="this.parentElement.innerHTML='<div class=\\'sin-imagen\\'>Sin imagen</div>'">` : '<div class="sin-imagen">Sin imagen</div>'}
      </div>
      <div class="cart-item-info">
        <h3 class="cart-item-titulo">${p.titulo}</h3>
        <p class="cart-item-codigo">Código: ${p.codigo}</p>
        ${p.descripcion ? `<p class="cart-item-descripcion">${p.descripcion}</p>` : ''}
      </div>
      <div class="cart-item-precio">
        <span class="label">Precio unitario</span>
        <span class="valor ${precioActualizado ? 'precio-actualizado' : ''}">${formatearMoneda(p.precio)}</span>
        ${precioActualizado ? '<span class="badge-actualizado">Actualizado</span>' : ''}
      </div>
      <div class="cart-item-cantidad">
        <span class="label">Cantidad</span>
        <div class="cantidad-controls">
          <button class="btn-cantidad" data-idx="${idx}" data-action="decrease">−</button>
          <input type="number"
                 inputmode="numeric" pattern="[0-9]*"
                 min="${min}"
                 ${max != null ? `max="${max}"` : ""}
                 step="${step}"
                 value="${p.cantidad}"
                 data-idx="${idx}"
                 class="cantidad-input">
          <button class="btn-cantidad" data-idx="${idx}" data-action="increase">+</button>
        </div>
        <small class="cantidad-info">Mín: ${min} | Múltiplo: ${step}${p.stock ? ` | Stock: ${p.stock}` : ''}</small>
      </div>
      <div class="cart-item-subtotal">
        <span class="label">Subtotal</span>
        <span class="valor">${formatearMoneda(p.precio * p.cantidad)}</span>
      </div>
      <div class="cart-item-acciones">
        <button data-idx="${idx}" class="btn-eliminar" title="Eliminar producto">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
    `;
    cont.appendChild(fila);
  });

  updateResumen();
  configurarEventListeners();
}

/**
 * Configura los event listeners para los inputs de cantidad y botones
 */
function configurarEventListeners() {
  // Botones de incrementar/decrementar cantidad
  document.querySelectorAll(".btn-cantidad").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const idx = parseInt(e.currentTarget.dataset.idx, 10);
      const action = e.currentTarget.dataset.action;
      const input = document.querySelector(`input.cantidad-input[data-idx="${idx}"]`);
      
      const step = carrito[idx].multiplo || 1;
      const min = carrito[idx].minimo || step || 1;
      const max = (carrito[idx].maximo ?? Infinity);
      
      let nuevaCantidad = carrito[idx].cantidad;
      
      if (action === "increase") {
        nuevaCantidad = Math.min(nuevaCantidad + step, max);
      } else if (action === "decrease") {
        nuevaCantidad = Math.max(nuevaCantidad - step, min);
      }
      
      carrito[idx].cantidad = nuevaCantidad;
      input.value = nuevaCantidad;
      guardar();
      
      // Actualizar subtotal del item
      input.closest(".cart-item").querySelector(".cart-item-subtotal .valor").textContent =
        formatearMoneda(carrito[idx].precio * nuevaCantidad);
      updateResumen();
    });
  });
  
  // Listeners de cantidad
  document.querySelectorAll(".cantidad-input").forEach(input => {
    const idx = parseInt(input.dataset.idx, 10);

    // Mientras escribe: solo limpiar a dígitos
    input.addEventListener("input", (e) => {
      const s = e.target.value.replace(/[^\d]/g, "");
      if (s !== e.target.value) e.target.value = s;
    });

    // Al salir o confirmar: corregir min/max/múltiplo
    const finalizar = () => {
      const step = carrito[idx].multiplo || 1;
      const min = carrito[idx].minimo || step || 1;
      const max = (carrito[idx].maximo ?? Infinity);

      const antes = carrito[idx].cantidad;
      const nuevo = corregirValor(input.value === "" ? min : input.value, min, step, max);

      // Persistir solo si cambió
      if (nuevo !== antes) {
        carrito[idx].cantidad = nuevo;
        guardar();
        toast("Cantidad actualizada", "info");
      }

      // Refrescar UI
      input.value = nuevo;
      input.closest(".cart-item").querySelector(".cart-item-subtotal .valor").textContent =
        formatearMoneda(carrito[idx].precio * nuevo);
      updateResumen();
    };

    input.addEventListener("blur", finalizar);
    input.addEventListener("change", finalizar);
    input.addEventListener("keydown", (e) => {
      if (["e", "E", "+", "-", ".", ","].includes(e.key)) e.preventDefault();
      if (e.key === "Enter") {
        e.preventDefault();
        input.blur();
      }
    });
  });

  // Botones de eliminar
  document.querySelectorAll(".btn-eliminar").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const idx = parseInt(e.currentTarget.dataset.idx, 10);
      const res = await Swal.fire({
        title: "Eliminar producto",
        text: "¿Querés quitar este producto del carrito?",
        icon: "question",
        showCancelButton: true,
        confirmButtonText: "Quitar",
        cancelButtonText: "Cancelar",
        confirmButtonColor: "#6a1b9a",
        cancelButtonColor: "#9e9e9e"
      });
      
      if (res.isConfirmed) {
        carrito.splice(idx, 1);
        guardar();
        renderCarrito();
        toast("Producto eliminado", "info");
      }
    });
  });
}

// =============================================================================
// VALIDACIÓN DEL FORMULARIO
// =============================================================================

/**
 * Valida formato de email
 */
function emailValido(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
}

/**
 * Obtiene la opción de entrega seleccionada
 */
function obtenerEntregaSeleccionada() {
  const r = document.querySelector('input[name="entrega"]:checked');
  return r ? r.value : "retiro";
}

/**
 * Valida el formulario completo
 */
function validarFormulario() {
  const total = calcularTotal();
  
  if (total < 200000) {
    alertBox({
      icon: "warning",
      title: "Pedido mínimo",
      text: "El pedido debe ser de al menos $200.000 para enviarse."
    });
    return false;
  }

  const nombre = document.getElementById("contacto-nombre").value.trim();
  const telefono = document.getElementById("contacto-telefono").value.trim();
  const email = document.getElementById("contacto-email").value.trim();

  if (!nombre) {
    alertBox({
      icon: "error",
      title: "Falta información",
      text: "Ingresá tu nombre completo."
    });
    return false;
  }

  if (!telefono) {
    alertBox({
      icon: "error",
      title: "Falta información",
      text: "Ingresá tu número de teléfono."
    });
    return false;
  }

  if (!email || !emailValido(email)) {
    alertBox({
      icon: "error",
      title: "Email inválido",
      text: "Revisá el formato de tu email."
    });
    return false;
  }

  const entrega = obtenerEntregaSeleccionada();
  if (entrega === "envio") {
    const dir = document.getElementById("envio-direccion").value.trim();
    const loc = document.getElementById("envio-localidad").value.trim();
    const prov = document.getElementById("envio-provincia").value.trim();
    const cp = document.getElementById("envio-cp").value.trim();
    const nombreDest = document.getElementById("envio-nombre-destinatario").value.trim();

    if (!dir || !loc || !prov || !cp || !nombreDest) {
      alertBox({
        icon: "error",
        title: "Datos de envío incompletos",
        text: "Completá todos los campos requeridos de envío."
      });
      return false;
    }
  }

  return true;
}

// =============================================================================
// MENSAJE DE WHATSAPP
// =============================================================================

/**
 * Arma el mensaje para WhatsApp
 */
function armarMensajeWhatsApp() {
  const entrega = obtenerEntregaSeleccionada();
  const nombre = document.getElementById("contacto-nombre").value.trim();
  const telefono = document.getElementById("contacto-telefono").value.trim();
  const email = document.getElementById("contacto-email").value.trim();

  const lines = [];
  lines.push("Pedido mayorista RM KITS:");
  carrito.forEach(p => {
    lines.push(`${p.titulo} - Cantidad: ${p.cantidad} - Precio unitario: $${p.precio}`);
  });
  lines.push(`TOTAL: $${formatearTotal()}`);
  lines.push("");
  lines.push("Datos de contacto:");
  lines.push(`- Nombre: ${nombre}`);
  lines.push(`- Teléfono: ${telefono}`);
  lines.push(`- Email: ${email}`);

  if (entrega === "retiro") {
    lines.push("");
    lines.push("Entrega: Retira en el local");
  } else {
    const dir = document.getElementById("envio-direccion").value.trim();
    const loc = document.getElementById("envio-localidad").value.trim();
    const prov = document.getElementById("envio-provincia").value.trim();
    const cp = document.getElementById("envio-cp").value.trim();
    const nombreDest = document.getElementById("envio-nombre-destinatario").value.trim();
    const ref = document.getElementById("envio-referencias").value.trim();
    
    lines.push("");
    lines.push("Entrega: Con envío");
    lines.push(`- Dirección: ${dir}`);
    lines.push(`- Localidad: ${loc}`);
    lines.push(`- Provincia: ${prov}`);
    lines.push(`- Código Postal: ${cp}`);
    lines.push(`- Nombre del destinatario: ${nombreDest}`);
    if (ref) lines.push(`- Referencias: ${ref}`);
  }

  return encodeURIComponent(lines.join("\n"));
}

// =============================================================================
// INFORMACIÓN DE ENTREGA
// =============================================================================

const INFO_RETIRO_HTML = `
  <p><strong>Retiro en el local</strong></p>
  <p><strong>Dirección:</strong> Av. Rivadavia 2768, CABA.</p>
  <p><strong>Horarios:</strong> Lun a Vie 9 a 18 hs. Sáb 9 a 15 hs.</p>
  <p><strong>Método de pago:</strong> Aceptamos todos los medios de pago.</p>
`;

const INFO_ENVIO_HTML = `
  <p><strong>Envíos</strong></p>
  <p><strong>CABA:</strong> $6.000</p>
  <p><strong>Gran Buenos Aires:</strong> $10.000</p>
  <p><strong>Interior del País:</strong> Vía ViaCargo (se abona al recibir).</p>
  <p><strong>Plazo:</strong> Se despacha entre 1 y 2 días hábiles luego de recibir el pago.</p>
  <p><strong>Método de pago:</strong> Transferencia bancaria.</p>
`;

/**
 * Muestra/oculta el formulario de envío según la selección
 */
function toggleEnvioForm() {
  const entrega = obtenerEntregaSeleccionada();
  const panel = document.getElementById("envio-form");
  const infoBox = document.getElementById("info-box");
  const envioFields = document.getElementById("envio-fields");

  panel.style.display = "grid";

  if (entrega === "envio") {
    infoBox.innerHTML = INFO_ENVIO_HTML;
    envioFields.style.display = "block";
  } else {
    infoBox.innerHTML = INFO_RETIRO_HTML;
    envioFields.style.display = "none";
  }
}

// =============================================================================
// INICIALIZACIÓN
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Migrar y normalizar carrito
  migrarCarrito();
  carrito = carrito.map(normalizarItem);
  guardar();

  // Sincronizar precios con la base de datos
  sincronizarPrecios();

  // Renderizar carrito
  renderCarrito();

  // Configurar toggle de entrega
  document.querySelectorAll('input[name="entrega"]').forEach(r => {
    r.addEventListener("change", toggleEnvioForm);
  });
  toggleEnvioForm();

  // Botón de enviar a WhatsApp
  document.getElementById("enviar-whatsapp-btn").addEventListener("click", async () => {
    if (!validarFormulario()) return;
    
    // Función para abrir WhatsApp
    const abrirWhatsApp = () => {
      const mensaje = armarMensajeWhatsApp();
      const url = `https://wa.me/${WHATSAPP_NUMERO}?text=${mensaje}`;
      window.open(url, "_blank");
    };
    
    // Intentar guardar el pedido en la base de datos primero
    const getNombre = () => {
      const el = document.getElementById("contacto-nombre");
      return el ? el.value : '';
    };
    const getTelefono = () => {
      const el = document.getElementById("contacto-telefono");
      return el ? el.value : '';
    };
    const getEmail = () => {
      const el = document.getElementById("contacto-email");
      return el ? el.value : '';
    };
    const getMetodoEntrega = () => {
      const el = document.querySelector('input[name="entrega"]:checked');
      return el ? el.value : 'retiro';
    };
    
    // Preparar datos del cliente
    const datosCliente = {
      nombre: getNombre(),
      telefono: getTelefono(),
      email: getEmail(),
      metodo_entrega: getMetodoEntrega(),
      productos: JSON.stringify(carrito),
      total: calcularTotal()
    };
    
    // Si es envío, agregar datos de envío
    if (getMetodoEntrega() === 'envio') {
      datosCliente.envio_direccion = document.getElementById('envio-direccion')?.value.trim() || '';
      datosCliente.envio_localidad = document.getElementById('envio-localidad')?.value.trim() || '';
      datosCliente.envio_provincia = document.getElementById('envio-provincia')?.value.trim() || '';
      datosCliente.envio_cp = document.getElementById('envio-cp')?.value.trim() || '';
      datosCliente.envio_nombre_destinatario = document.getElementById('envio-nombre-destinatario')?.value.trim() || '';
      datosCliente.envio_referencias = document.getElementById('envio-referencias')?.value.trim() || '';
    }
    
    try {
      const response = await fetch('/guardar-pedido', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(datosCliente)
      });
      
      const result = await response.json();
      
      if (result.success) {
        console.log('✅ Pedido guardado con ID:', result.pedido_id);
      } else {
        console.warn('⚠️ Error al guardar pedido:', result.error);
      }
    } catch (error) {
      console.error('❌ Error al guardar pedido:', error);
    }
    
    // Siempre abrir WhatsApp, independientemente de si se guardó o no
    abrirWhatsApp();
  });

  // Prevenir zoom con doble tap en móviles
  let lastTouchEnd = 0;
  document.addEventListener('touchend', function (event) {
    const now = (new Date()).getTime();
    if (now - lastTouchEnd <= 300) {
      event.preventDefault();
    }
    lastTouchEnd = now;
  }, false);
});
