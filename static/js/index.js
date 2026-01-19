/**
 * Script principal para la página de productos - RM KITS
 */

// Constantes
const PRODUCTOS_POR_PAGINA = 24;
const STORAGE_KEY = "rmkits_carrito";

// Estado de la aplicación
let carrito = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
let productosRaw = [];
let productosFiltrados = [];
let paginaActual = 1;
let textoBusqueda = "";
let filtroCategoria = "";

// Elementos del DOM
const cont = document.getElementById("productos");

// =============================================================================
// UTILIDADES
// =============================================================================

/**
 * Normaliza texto removiendo acentos y convirtiendo a minúsculas
 */
function normalizarTexto(s) {
  return (s || "").toString().trim().toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

/**
 * Normaliza el valor de categoría
 */
function normalizarCategoriaValor(sRaw) {
  const s = normalizarTexto(sRaw);
  if (!s) return "";
  if (s.includes("jugueteria") || s.includes("cotillon")) return "jugueteria/cotillon";
  if (s.includes("libreria")) return "libreria";
  return s;
}

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

// =============================================================================
// MANEJO DEL CARRITO
// =============================================================================

/**
 * Actualiza el badge del carrito
 */
function actualizarBadge() {
  const cantidadTotal = carrito.reduce((s, p) => s + p.cantidad, 0);
  document.getElementById("badge").textContent = cantidadTotal;
}

/**
 * Guarda el carrito en localStorage
 */
function guardarCarrito() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(carrito));
  actualizarBadge();
}

/**
 * Agrega un producto al carrito
 */
function agregarAlCarrito(producto, cantidad) {
  const existente = carrito.find(c => c.id === producto.id);
  
  if (existente) {
    if ((existente.cantidad + cantidad) > producto.stock) {
      alertBox({
        icon: "warning",
        title: "Stock limitado",
        text: `Para esa cantidad, contáctanos directamente por WhatsApp y te confirmamos la disponibilidad. WhatsApp: 11 5857 3906`
      });
      return false;
    }
    existente.cantidad += cantidad;
  } else {
    carrito.push({
      id: producto.id,
      codigo: producto.codigo,
      titulo: producto.titulo,
      precio: producto.precio,
      multiplo: producto.multiplo,
      minimo: producto.minimo,
      maximo: producto.stock,
      cantidad
    });
  }
  
  guardarCarrito();
  toast("Agregado al carrito");
  return true;
}

// =============================================================================
// FILTROS Y BÚSQUEDA
// =============================================================================

/**
 * Lee la categoría desde la URL
 */
function leerCategoriaDeURL() {
  const params = new URLSearchParams(window.location.search);
  filtroCategoria = normalizarCategoriaValor(params.get("cat") || "");
}

/**
 * Aplica los filtros de búsqueda y categoría
 */
function aplicarFiltro() {
  const q = textoBusqueda.trim().toLowerCase();
  const catFiltro = normalizarCategoriaValor(filtroCategoria);
  
  productosFiltrados = productosRaw.filter(p => {
    const coincideTexto = !q || (p.titulo || "").toLowerCase().includes(q);
    const catProd = normalizarCategoriaValor(p.categoria);
    const coincideCat = !catFiltro || catProd === catFiltro;
    const tieneStock = p.stock > 0;
    return coincideTexto && coincideCat && tieneStock;
  });
  
  paginaActual = 1;
  renderProductos();
}

// =============================================================================
// RENDERIZADO DE PRODUCTOS
// =============================================================================

/**
 * Calcula el máximo válido por stock
 */
function maxValidoPorStock(producto) {
  const k = Math.floor(producto.stock / producto.multiplo);
  return Math.max(0, k * producto.multiplo);
}

/**
 * Ajusta la cantidad al múltiplo válido más cercano
 */
function snapCantidad(n, producto) {
  if (isNaN(n)) n = producto.minimo;
  
  // Redondear al múltiplo más cercano
  n = Math.round(n / producto.multiplo) * producto.multiplo;
  
  // Respetar mínimo
  if (n < producto.minimo) n = producto.minimo;
  
  // Respetar tope por stock
  const topo = maxValidoPorStock(producto);
  if (topo > 0) n = Math.min(n, topo);
  else n = 0;
  
  return n;
}

/**
 * Renderiza los productos en el grid
 */
function renderProductos() {
  cont.innerHTML = "";
  const inicio = (paginaActual - 1) * PRODUCTOS_POR_PAGINA;
  const slice = productosFiltrados.slice(inicio, inicio + PRODUCTOS_POR_PAGINA);
  const tpl = document.getElementById("producto-template");

  if (slice.length === 0) {
    cont.innerHTML = `<p style="padding:8px;">No se encontraron productos.</p>`;
    actualizarPaginacion();
    return;
  }

  slice.forEach(p => {
    const node = tpl.content.cloneNode(true);
    const card = node.querySelector(".card");
    
    // Configurar elementos básicos
    card.dataset.categoria = normalizarCategoriaValor(p.categoria);
    node.querySelector(".img").src = `/static/img/${p.imagen}`;
    node.querySelector(".img").alt = p.titulo;
    node.querySelector(".titulo").textContent = p.titulo;
    node.querySelector(".titulo").title = p.titulo;
    node.querySelector(".precio").innerHTML = `<strong>$${p.precio}</strong>`;
    node.querySelector(".minimo").textContent = `Mínimo de compra: ${p.minimo}`;
    node.querySelector(".multiplo").textContent = `Se vende ${p.multiplo > 1 ? ` de a ${p.multiplo} unidades` : "de a 1 unidad"}`;

    // Configurar input de cantidad
    const input = node.querySelector(".cantidad");
    input.min = p.minimo;
    input.step = p.multiplo;
    input.value = p.minimo;

    const btnMenos = node.querySelector(".menos");
    const btnMas = node.querySelector(".mas");
    const btnAdd = node.querySelector(".add-btn");

    // Función para ajustar cantidad
    function ajustar(delta) {
      let n = parseInt(input.value, 10);
      if (isNaN(n)) n = p.minimo;
      n += delta * p.multiplo;
      input.value = snapCantidad(n, p);
    }

    // Eventos de botones + y -
    btnMenos.addEventListener("click", () => ajustar(-1));
    btnMas.addEventListener("click", () => ajustar(1));

    // Evento del botón agregar al carrito
    btnAdd.addEventListener("click", () => {
      const cantidad = parseInt(input.value, 10);

      // Validaciones
      if (!cantidad || cantidad < p.minimo) {
        alertBox({
          icon: "warning",
          title: "Mínimo de compra",
          text: `La cantidad mínima es ${p.minimo}.`
        });
        return;
      }

      if (cantidad % p.multiplo !== 0) {
        alertBox({
          icon: "warning",
          title: "Cantidad inválida",
          text: `Este producto se vende en packs o cajas cerradas de a ${p.multiplo} unidades. Tenés que seleccionar un múltiplo de ese valor. O también, podés ajustar la cantidad con los botones + y -`
        });
        return;
      }

      if (cantidad > p.stock) {
        alertBox({
          icon: "warning",
          title: "Stock limitado",
          text: `Para esa cantidad, contáctanos directamente por WhatsApp y te confirmamos la disponibilidad. WhatsApp: 11 5857 3906`
        });
        const nuevo = snapCantidad(parseInt(input.value, 10), p);
        input.value = nuevo;
        return;
      }

      // Agregar al carrito
      agregarAlCarrito(p, cantidad);
    });

    cont.appendChild(node);
  });

  actualizarPaginacion();
}

/**
 * Actualiza los controles de paginación
 */
function actualizarPaginacion() {
  const totalPags = Math.ceil(productosFiltrados.length / PRODUCTOS_POR_PAGINA) || 1;
  document.getElementById("pagina-info").textContent = `Página ${paginaActual} de ${totalPags}`;
  document.getElementById("prev-btn").disabled = paginaActual === 1;
  document.getElementById("next-btn").disabled = paginaActual >= totalPags;
}

/**
 * Navega al carrito
 */
function irCarrito() {
  window.location.href = "/carrito";
}

// =============================================================================
// INICIALIZACIÓN
// =============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Cargar productos del dataset
  try {
    productosRaw = JSON.parse(cont.dataset.productos);
  } catch (e) {
    console.error("Error parseando productos:", e);
    productosRaw = [];
  }

  // Leer categoría de la URL
  leerCategoriaDeURL();

  // Marcar botón de categoría activo
  document.querySelectorAll(".filtro-btn").forEach(b => {
    if (normalizarCategoriaValor(b.dataset.cat) === filtroCategoria) {
      document.querySelectorAll(".filtro-btn").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
    }
  });

  // Renderizar productos iniciales
  aplicarFiltro();
  actualizarBadge();

  // Event listeners
  document.getElementById("filtro").addEventListener("input", e => {
    textoBusqueda = e.target.value;
    aplicarFiltro();
  });

  document.querySelectorAll(".filtro-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filtro-btn").forEach(x => x.classList.remove("active"));
      btn.classList.add("active");
      filtroCategoria = btn.dataset.cat || "";
      aplicarFiltro();
      
      // Actualizar URL
      const url = new URL(window.location.href);
      if (filtroCategoria) {
        url.searchParams.set("cat", filtroCategoria);
      } else {
        url.searchParams.delete("cat");
      }
      window.history.replaceState({}, "", url);
    });
  });

  document.getElementById("prev-btn").addEventListener("click", () => {
    if (paginaActual > 1) {
      paginaActual--;
      renderProductos();
    }
  });

  document.getElementById("next-btn").addEventListener("click", () => {
    const totalPags = Math.ceil(productosFiltrados.length / PRODUCTOS_POR_PAGINA);
    if (paginaActual < totalPags) {
      paginaActual++;
      renderProductos();
    }
  });

  document.getElementById("finalizar-pedido-btn").addEventListener("click", irCarrito);

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
