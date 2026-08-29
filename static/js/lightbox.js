/**
 * Lightbox de imágenes - RM KITS
 *
 * Al tocar/clickear una imagen de producto (catálogo o carrito) se abre una
 * vista ampliada para ver mejor de qué producto se trata.
 * Funciona con delegación de eventos, así que cubre productos que se renderizan
 * dinámicamente (grid del catálogo y filas del carrito).
 */
(function () {
  // Selectores de imágenes que se pueden ampliar
  const SELECTOR_IMAGENES = ".card .img, .cart-item-imagen img";

  let overlay, overlayImg;

  function crearOverlay() {
    overlay = document.createElement("div");
    overlay.className = "lightbox-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.innerHTML = `
      <button type="button" class="lightbox-cerrar" aria-label="Cerrar">&times;</button>
      <img class="lightbox-img" src="" alt="">
    `;
    document.body.appendChild(overlay);
    overlayImg = overlay.querySelector(".lightbox-img");

    // Cerrar al tocar el fondo o el botón (no al tocar la imagen)
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay || e.target.classList.contains("lightbox-cerrar")) {
        cerrar();
      }
    });
  }

  function abrir(src, alt) {
    if (!src) return;
    if (!overlay) crearOverlay();
    overlayImg.src = src;
    overlayImg.alt = alt || "";
    overlay.classList.add("visible");
    document.body.classList.add("lightbox-abierto");
  }

  function cerrar() {
    if (!overlay) return;
    overlay.classList.remove("visible");
    document.body.classList.remove("lightbox-abierto");
    // Liberar la imagen luego de la transición
    setTimeout(() => { if (!overlay.classList.contains("visible")) overlayImg.src = ""; }, 200);
  }

  // Delegación: cualquier click sobre una imagen que matchee el selector
  document.addEventListener("click", (e) => {
    const img = e.target.closest(SELECTOR_IMAGENES);
    if (!img) return;
    // Ignorar imágenes que no cargaron
    if (img.complete && img.naturalWidth === 0) return;
    e.preventDefault();
    abrir(img.currentSrc || img.src, img.alt);
  });

  // Cerrar con Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") cerrar();
  });
})();
