/**
 * JavaScript para el Panel de Administración - RM KITS
 */

// Auto-cerrar alertas después de 5 segundos
document.addEventListener('DOMContentLoaded', function() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });
});

// Animación de salida para alertas
const style = document.createElement('style');
style.textContent = `
  @keyframes slideOut {
    from {
      transform: translateY(0);
      opacity: 1;
    }
    to {
      transform: translateY(-10px);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Confirmar antes de salir del formulario con cambios
let formChanged = false;
const forms = document.querySelectorAll('form');
forms.forEach(form => {
  const inputs = form.querySelectorAll('input, select, textarea');
  inputs.forEach(input => {
    input.addEventListener('change', () => {
      formChanged = true;
    });
  });
  
  form.addEventListener('submit', () => {
    formChanged = false;
  });
});

window.addEventListener('beforeunload', (e) => {
  if (formChanged) {
    e.preventDefault();
    e.returnValue = '';
    return '';
  }
});

// Formato de números en inputs de precio
const priceInputs = document.querySelectorAll('input[name="precio"]');
priceInputs.forEach(input => {
  input.addEventListener('blur', function() {
    const value = parseFloat(this.value);
    if (!isNaN(value)) {
      this.value = value.toFixed(2);
    }
  });
});

// Preview de archivo con validación de tamaño
function previewImage(input) {
  const preview = document.getElementById('imagePreview');
  if (!preview) return;
  
  preview.innerHTML = '';
  
  if (input.files && input.files[0]) {
    const file = input.files[0];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    // Validar tamaño
    if (file.size > maxSize) {
      alert('El archivo es demasiado grande. Máximo 5MB.');
      input.value = '';
      return;
    }
    
    // Validar tipo
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      alert('Formato no válido. Use JPG, PNG, GIF o WEBP.');
      input.value = '';
      return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
      const img = document.createElement('img');
      img.src = e.target.result;
      preview.appendChild(img);
      preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }
}

// Hacer la función global
window.previewImage = previewImage;

// Función para eliminar producto (global)
window.eliminarProducto = function(id, titulo) {
  if (confirm(`¿Estás seguro de eliminar "${titulo}"?\n\nEsta acción no se puede deshacer.`)) {
    const form = document.getElementById('deleteForm');
    if (form) {
      form.action = `/admin/producto/${id}/eliminar`;
      form.submit();
    }
  }
};

// Validación de formulario de producto
document.addEventListener('DOMContentLoaded', function() {
  const productForm = document.querySelector('.product-form');
  if (productForm) {
    productForm.addEventListener('submit', function(e) {
      const minimo = parseInt(document.getElementById('minimo')?.value || 0);
      const multiplo = parseInt(document.getElementById('multiplo')?.value || 0);
      const stock = parseInt(document.getElementById('stock')?.value || 0);
      
      // Validar mínimo >= múltiplo
      if (minimo < multiplo) {
        alert('El mínimo de compra debe ser mayor o igual al múltiplo');
        e.preventDefault();
        return false;
      }
      
      // Validar que el mínimo sea múltiplo del múltiplo
      if (multiplo > 0 && minimo % multiplo !== 0) {
        alert('El mínimo debe ser un múltiplo del valor "Múltiplo"');
        e.preventDefault();
        return false;
      }
      
      // Advertir si stock < mínimo
      if (stock > 0 && stock < minimo) {
        if (!confirm('El stock es menor que el mínimo de compra. ¿Continuar de todos modos?')) {
          e.preventDefault();
          return false;
        }
      }
    });
  }
});

// Filtros combinados: búsqueda, categoría y stock
function aplicarFiltros() {
  const searchInput = document.getElementById('searchInput');
  const categoryFilter = document.getElementById('categoryFilter');
  const stockFilter = document.getElementById('stockFilter');
  const table = document.querySelector('.data-table');
  
  if (!table) return;
  
  const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
  const categorySelected = categoryFilter ? categoryFilter.value : '';
  const stockSelected = stockFilter ? stockFilter.value : '';
  
  // Guardar filtros en sessionStorage para mantenerlos al volver
  sessionStorage.setItem('admin_search', searchTerm);
  sessionStorage.setItem('admin_category', categorySelected);
  sessionStorage.setItem('admin_stock', stockSelected);
  
  const rows = table.querySelectorAll('tbody tr');
  let visibleCount = 0;
  
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    
    // Obtener la categoría de la fila (columna 10 - índice 9)
    const categoryCell = row.cells[9];
    const categoryText = categoryCell ? categoryCell.textContent.trim() : '';
    
    // Obtener el stock de la fila (columna 9 - índice 8)
    const stockCell = row.cells[8];
    const stockText = stockCell ? stockCell.textContent.trim() : '0';
    const stockValue = parseInt(stockText) || 0;
    
    // Aplicar filtros
    const matchesSearch = searchTerm === '' || text.includes(searchTerm);
    const matchesCategory = categorySelected === '' || categoryText === categorySelected;
    
    let matchesStock = true;
    if (stockSelected === 'sin-stock') {
      matchesStock = stockValue === 0;
    } else if (stockSelected === 'stock-bajo') {
      matchesStock = stockValue > 0 && stockValue <= 10;
    } else if (stockSelected === 'con-stock') {
      matchesStock = stockValue > 0;
    }
    
    if (matchesSearch && matchesCategory && matchesStock) {
      row.style.display = '';
      visibleCount++;
    } else {
      row.style.display = 'none';
    }
  });
  
  // Actualizar contadores
  const visibleCountEl = document.getElementById('visibleCount');
  if (visibleCountEl) {
    visibleCountEl.textContent = visibleCount;
  }
}

// Restaurar filtros guardados al cargar la página
function restaurarFiltros() {
  const searchInput = document.getElementById('searchInput');
  const categoryFilter = document.getElementById('categoryFilter');
  const stockFilter = document.getElementById('stockFilter');
  
  // Restaurar valores desde sessionStorage
  if (searchInput && sessionStorage.getItem('admin_search')) {
    searchInput.value = sessionStorage.getItem('admin_search');
  }
  
  if (categoryFilter && sessionStorage.getItem('admin_category')) {
    categoryFilter.value = sessionStorage.getItem('admin_category');
  }
  
  if (stockFilter && sessionStorage.getItem('admin_stock')) {
    stockFilter.value = sessionStorage.getItem('admin_stock');
  }
  
  // Aplicar filtros restaurados
  if (searchInput || categoryFilter || stockFilter) {
    aplicarFiltros();
  }
}

// Ejecutar restauración al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  // Restaurar filtros si estamos en la página de productos
  if (document.getElementById('searchInput')) {
    restaurarFiltros();
  }
});

// Búsqueda en tablas
const searchInput = document.getElementById('searchInput');
if (searchInput) {
  let searchTimeout;
  searchInput.addEventListener('input', function(e) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(aplicarFiltros, 300);
  });
}

// Filtro de categoría
const categoryFilter = document.getElementById('categoryFilter');
if (categoryFilter) {
  categoryFilter.addEventListener('change', aplicarFiltros);
}

// Filtro de stock
const stockFilter = document.getElementById('stockFilter');
if (stockFilter) {
  stockFilter.addEventListener('change', aplicarFiltros);
}

// Botón limpiar filtros
const clearFiltersBtn = document.getElementById('clearFilters');
if (clearFiltersBtn) {
  clearFiltersBtn.addEventListener('click', function() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const stockFilter = document.getElementById('stockFilter');
    
    if (searchInput) searchInput.value = '';
    if (categoryFilter) categoryFilter.value = '';
    if (stockFilter) stockFilter.value = '';
    
    // Limpiar sessionStorage
    sessionStorage.removeItem('admin_search');
    sessionStorage.removeItem('admin_category');
    sessionStorage.removeItem('admin_stock');
    
    aplicarFiltros();
  });
}

// Highlight en la fila al pasar el mouse
document.addEventListener('DOMContentLoaded', function() {
  const tableRows = document.querySelectorAll('.data-table tbody tr');
  tableRows.forEach(row => {
    row.addEventListener('mouseenter', function() {
      this.style.backgroundColor = '#f0e6f5';
    });
    row.addEventListener('mouseleave', function() {
      this.style.backgroundColor = '';
    });
  });
});

// Actualización rápida de precios
document.addEventListener('DOMContentLoaded', function() {
  const priceInputs = document.querySelectorAll('.price-input');
  
  priceInputs.forEach(input => {
    let timeoutId;
    let originalValue = input.value;
    
    input.addEventListener('focus', function() {
      originalValue = this.value;
    });
    
    input.addEventListener('input', function() {
      clearTimeout(timeoutId);
      const inputElement = this;
      
      // Esperar 1 segundo después de que el usuario deje de escribir
      timeoutId = setTimeout(() => {
        actualizarPrecio(inputElement, originalValue);
      }, 1000);
    });
    
    input.addEventListener('blur', function() {
      clearTimeout(timeoutId);
      if (this.value !== originalValue) {
        actualizarPrecio(this, originalValue);
      }
    });
    
    input.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        clearTimeout(timeoutId);
        this.blur();
      }
    });
  });
});

function actualizarPrecio(inputElement, originalValue) {
  const productoId = inputElement.dataset.productoId;
  const nuevoPrecio = inputElement.value;
  
  // Validar que sea un número positivo
  if (!nuevoPrecio || parseFloat(nuevoPrecio) < 0) {
    inputElement.value = originalValue;
    return;
  }
  
  // Mostrar estado de guardando
  inputElement.classList.add('saving');
  
  fetch('/admin/producto/actualizar-precio', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      producto_id: productoId,
      precio: parseFloat(nuevoPrecio)
    })
  })
  .then(response => response.json())
  .then(data => {
    inputElement.classList.remove('saving');
    
    if (data.success) {
      // Mostrar feedback de éxito
      inputElement.classList.add('success');
      setTimeout(() => {
        inputElement.classList.remove('success');
      }, 1000);
      
      // Actualizar el valor original
      originalValue = nuevoPrecio;
    } else {
      // Mostrar error y restaurar valor original
      inputElement.classList.add('error');
      inputElement.value = originalValue;
      setTimeout(() => {
        inputElement.classList.remove('error');
      }, 2000);
      
      alert('Error: ' + (data.error || 'No se pudo actualizar el precio'));
    }
  })
  .catch(error => {
    inputElement.classList.remove('saving');
    inputElement.classList.add('error');
    inputElement.value = originalValue;
    setTimeout(() => {
      inputElement.classList.remove('error');
    }, 2000);
    
    console.error('Error:', error);
    alert('Error al actualizar el precio. Intenta nuevamente.');
  });
}

// Toggle activar/desactivar productos
document.addEventListener('DOMContentLoaded', function() {
  const toggles = document.querySelectorAll('.toggle-activo');
  
  toggles.forEach(toggle => {
    toggle.addEventListener('change', function() {
      const productoId = this.dataset.productoId;
      const activo = this.checked ? 1 : 0;
      const row = this.closest('tr');
      
      fetch('/admin/producto/toggle-activo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          producto_id: productoId,
          activo: activo
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Actualizar clase visual de la fila
          if (activo) {
            row.classList.remove('producto-inactivo');
          } else {
            row.classList.add('producto-inactivo');
          }
        } else {
          // Revertir toggle si falla
          this.checked = !this.checked;
          alert('Error: ' + (data.error || 'No se pudo actualizar el estado'));
        }
      })
      .catch(error => {
        console.error('Error:', error);
        // Revertir toggle si falla
        this.checked = !this.checked;
        alert('Error al actualizar el estado del producto. Intenta nuevamente.');
      });
    });
  });
});

console.log('✅ Admin panel loaded successfully');
