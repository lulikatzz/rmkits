/**
 * Visor de imágenes ampliadas (lightbox) - RM KITS
 *
 * Al tocar/clickear la imagen de un producto se abre una vista grande para
 * poder verla en detalle. Dentro del visor se puede acercar todavía más
 * (tocando la imagen) y desplazarse para recorrerla.
 *
 * No requiere configuración: se engancha por delegación de eventos a las
 * imágenes de producto del catálogo y del carrito.
 */
(function () {
  "use strict";

  // Recuadros de imagen de producto que abren el visor. Se escucha el marco y
  // no la imagen para que también funcione al tocar el borde del recuadro.
  const SELECTOR_RECUADROS = ".card .img-wrapper, .cart-item-imagen";

  // Cuánto se agranda respecto del tamaño "ajustado a pantalla" al hacer zoom
  const FACTOR_ZOOM = 2.5;

  // Topes de ampliación sobre el tamaño real de la imagen. Estirar de más no
  // agrega detalle, solo borronea, así que se limita en ambos modos.
  const MAX_ESCALA_AJUSTADA = 2;
  const MAX_ESCALA_AMPLIADA = 3;

  /**
   * En celular/tablet el navegador ya permite acercar con los dedos (pinch),
   * así que ahí el visor solo agranda la imagen a pantalla completa y tocarla
   * no hace nada más. El zoom por click queda solo para computadora.
   */
  function esTactil() {
    return window.matchMedia("(hover: none) and (pointer: coarse)").matches;
  }

  let overlay = null;
  let viewport = null;
  let imgGrande = null;
  let leyenda = null;
  let ayuda = null;
  let btnCerrar = null;

  let ampliada = false;      // estado de zoom extra dentro del visor
  let focoAnterior = null;   // elemento que tenía el foco antes de abrir

  // Estado del arrastre con mouse (en touch alcanza el scroll nativo)
  let arrastrando = false;
  let xInicio = 0, yInicio = 0, scrollXInicio = 0, scrollYInicio = 0, huboArrastre = false;

  // ===========================================================================
  // CONSTRUCCIÓN DEL VISOR
  // ===========================================================================

  function crearVisor() {
    overlay = document.createElement("div");
    overlay.className = "lightbox";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.setAttribute("aria-label", "Imagen del producto");
    overlay.innerHTML = `
      <button class="lightbox-cerrar" type="button" aria-label="Cerrar imagen">&times;</button>
      <div class="lightbox-viewport">
        <img class="lightbox-img" src="" alt="">
      </div>
      <div class="lightbox-pie">
        <div class="lightbox-leyenda"></div>
        <div class="lightbox-ayuda"></div>
      </div>
    `;
    document.body.appendChild(overlay);

    viewport = overlay.querySelector(".lightbox-viewport");
    imgGrande = overlay.querySelector(".lightbox-img");
    leyenda = overlay.querySelector(".lightbox-leyenda");
    ayuda = overlay.querySelector(".lightbox-ayuda");
    btnCerrar = overlay.querySelector(".lightbox-cerrar");

    btnCerrar.addEventListener("click", cerrar);

    // Tocar fuera de la imagen (en cualquier parte del fondo) cierra el visor
    overlay.addEventListener("click", (e) => {
      if (huboArrastre) return; // veníamos recorriendo la imagen, no es un toque
      if (e.target.closest(".lightbox-img, .lightbox-cerrar, .lightbox-pie")) return;
      cerrar();
    });

    // Click sobre la imagen: alterna el zoom extra (solo en computadora)
    imgGrande.addEventListener("click", (e) => {
      e.stopPropagation();
      if (huboArrastre) return; // fue un arrastre, no un click
      if (esTactil()) return;   // en celular se usa el pinch del navegador
      alternarZoom(e.clientX, e.clientY);
    });

    // Arrastrar con el mouse para recorrer la imagen ampliada
    viewport.addEventListener("pointerdown", (e) => {
      if (e.pointerType !== "mouse" || !ampliada) return;
      arrastrando = true;
      huboArrastre = false;
      xInicio = e.clientX;
      yInicio = e.clientY;
      scrollXInicio = viewport.scrollLeft;
      scrollYInicio = viewport.scrollTop;
      viewport.classList.add("arrastrando");
    });

    viewport.addEventListener("pointermove", (e) => {
      if (!arrastrando) return;
      const dx = e.clientX - xInicio;
      const dy = e.clientY - yInicio;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) huboArrastre = true;
      viewport.scrollLeft = scrollXInicio - dx;
      viewport.scrollTop = scrollYInicio - dy;
    });

    // Recalcular el tamaño ajustado cuando la imagen termina de cargar
    imgGrande.addEventListener("load", ajustarAPantalla);

    // ...y cuando cambia el tamaño de la ventana (rotar el teléfono, etc.)
    window.addEventListener("resize", () => {
      if (overlay.classList.contains("abierto")) ajustarAPantalla();
    });

    ["pointerup", "pointercancel", "pointerleave"].forEach(evt => {
      viewport.addEventListener(evt, () => {
        arrastrando = false;
        viewport.classList.remove("arrastrando");
        // Se limpia en el próximo tick para que el click posterior lo vea
        setTimeout(() => { huboArrastre = false; }, 0);
      });
    });
  }

  // ===========================================================================
  // ABRIR / CERRAR
  // ===========================================================================

  function abrir(src, titulo) {
    if (!overlay) crearVisor();

    focoAnterior = document.activeElement;

    resetearZoom();
    imgGrande.src = src;
    imgGrande.style.width = "";           // el tamaño real se calcula al cargar
    if (imgGrande.complete) ajustarAPantalla();  // imagen ya cacheada
    imgGrande.alt = titulo || "Imagen del producto";
    leyenda.textContent = titulo || "";
    leyenda.style.display = titulo ? "" : "none";

    ayuda.textContent = esTactil()
      ? "Tocá afuera de la imagen para cerrar"
      : "Hacé click en la imagen para acercarla · Click afuera para cerrar";

    overlay.classList.add("abierto");
    document.body.classList.add("lightbox-abierto");

    // Foco al botón cerrar para que Escape/tab funcionen de entrada
    btnCerrar.focus({ preventScroll: true });
  }

  function cerrar() {
    if (!overlay || !overlay.classList.contains("abierto")) return;

    overlay.classList.remove("abierto");
    document.body.classList.remove("lightbox-abierto");
    resetearZoom();
    imgGrande.removeAttribute("src");

    if (focoAnterior && typeof focoAnterior.focus === "function") {
      focoAnterior.focus({ preventScroll: true });
    }
    focoAnterior = null;
  }

  // ===========================================================================
  // ZOOM DENTRO DEL VISOR
  // ===========================================================================

  function resetearZoom() {
    ampliada = false;
    if (!imgGrande) return;
    overlay.classList.remove("ampliada");
    viewport.scrollTop = 0;
    viewport.scrollLeft = 0;
    ajustarAPantalla();
  }

  /**
   * Modo "ajustado": la imagen ocupa lo más posible de la pantalla.
   * Si la imagen original es chica igual se agranda (hasta MAX_ESCALA_AJUSTADA)
   * para que no se vea casi como la miniatura.
   */
  function ajustarAPantalla() {
    if (!imgGrande || ampliada) return;

    imgGrande.style.width = "";
    const anchoReal = imgGrande.naturalWidth;
    const altoReal = imgGrande.naturalHeight;
    if (!anchoReal || !altoReal) return;

    const escala = Math.min(
      viewport.clientWidth / anchoReal,
      viewport.clientHeight / altoReal,
      MAX_ESCALA_AJUSTADA
    );
    imgGrande.style.width = Math.round(anchoReal * escala) + "px";
  }

  function alternarZoom(clientX, clientY) {
    if (ampliada) {
      resetearZoom();
      return;
    }

    const rect = imgGrande.getBoundingClientRect();
    if (!rect.width) return;

    // Nunca achicar: se toma el mayor entre el tamaño real de la imagen y el
    // ajustado a pantalla por el factor de zoom, sin pasar el tope de escala.
    const anchoNatural = imgGrande.naturalWidth || 0;
    const anchoAmpliado = Math.min(
      Math.max(anchoNatural, rect.width * FACTOR_ZOOM),
      anchoNatural * MAX_ESCALA_AMPLIADA
    );

    // Si no hay nada que ganar (imagen chica ya vista completa), no hacemos zoom
    if (anchoAmpliado <= rect.width + 1) return;

    // Punto de la imagen que estaba bajo el dedo/cursor, en proporción 0..1
    const propX = (clientX - rect.left) / rect.width;
    const propY = (clientY - rect.top) / rect.height;

    ampliada = true;
    overlay.classList.add("ampliada");
    imgGrande.style.width = anchoAmpliado + "px";

    // Centrar el visor en el punto tocado
    const nuevo = imgGrande.getBoundingClientRect();
    viewport.scrollLeft = (propX * nuevo.width) - (viewport.clientWidth / 2);
    viewport.scrollTop = (propY * nuevo.height) - (viewport.clientHeight / 2);
  }

  // ===========================================================================
  // ENGANCHE CON LA PÁGINA
  // ===========================================================================

  document.addEventListener("click", (e) => {
    const recuadro = e.target.closest ? e.target.closest(SELECTOR_RECUADROS) : null;
    if (!recuadro) return;

    const img = recuadro.querySelector("img");
    if (!img) return; // productos sin imagen

    // Si la miniatura no cargó, no tiene sentido abrir el visor
    if (img.complete && img.naturalWidth === 0) return;

    e.preventDefault();
    e.stopPropagation();

    const titulo = img.getAttribute("alt") || "";
    abrir(img.currentSrc || img.src, titulo);
  });

  document.addEventListener("keydown", (e) => {
    if (!overlay || !overlay.classList.contains("abierto")) return;
    if (e.key === "Escape") {
      e.preventDefault();
      cerrar();
    }
  });

  // Por si algún flujo necesita abrirlo a mano
  window.RMLightbox = { abrir, cerrar };
})();
