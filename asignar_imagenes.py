import sqlite3
import os

def asignar_imagenes_automaticamente():
    """
    Busca automáticamente imágenes para productos sin imagen,
    basándose en el código del producto.
    """
    conn = sqlite3.connect('productos.db')
    cursor = conn.cursor()
    
    # Obtener todos los productos
    cursor.execute("SELECT id, codigo, imagen FROM producto")
    productos = cursor.fetchall()
    
    img_folder = 'static/img'
    actualizados = 0
    
    print("\n" + "="*60)
    print("🔍 ASIGNANDO IMÁGENES AUTOMÁTICAMENTE")
    print("="*60 + "\n")
    
    for producto_id, codigo, imagen_actual in productos:
        # Si ya tiene imagen, saltar
        if imagen_actual and imagen_actual.strip():
            continue
        
        # Buscar imagen con el mismo código
        extensiones = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        imagen_encontrada = None
        
        for ext in extensiones:
            img_path = os.path.join(img_folder, f"{codigo}{ext}")
            if os.path.exists(img_path):
                imagen_encontrada = f"{codigo}{ext}"
                break
        
        if imagen_encontrada:
            cursor.execute(
                "UPDATE producto SET imagen = ? WHERE id = ?",
                (imagen_encontrada, producto_id)
            )
            print(f"✅ {codigo}: {imagen_encontrada}")
            actualizados += 1
        else:
            print(f"⚠️  {codigo}: No se encontró imagen")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print(f"✅ COMPLETADO: {actualizados} productos actualizados")
    print("="*60 + "\n")

if __name__ == "__main__":
    asignar_imagenes_automaticamente()
