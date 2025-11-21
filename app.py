from flask import Flask, render_template, request, jsonify, redirect
import sqlite3
import urllib.parse



app = Flask(__name__)

@app.before_request
def before_request():
    if request.headers.get("X-Forwarded-Proto") == "http":
        return redirect(request.url.replace("http://", "https://", 1), code=301)


def get_productos():
    conn = sqlite3.connect("productos.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM producto")  # incluye 'categoria'
    filas = cursor.fetchall()
    conn.close()
    productos = [dict(f) for f in filas]
    return productos

@app.route("/")
def index():
    productos = get_productos()
    return render_template("index.html", productos=productos)

@app.route("/enviar_pedido", methods=["POST"])
def enviar_pedido():
    datos = request.json
    total = datos.get("total", 0)
    items = datos.get("items", [])

    if total < 200000:
        return jsonify({"error": "El pedido debe superar los $200.000"}), 400

    lines = []
    lines.append("Pedido mayorista RM KITS:")
    for item in items:
        lines.append(f"{item['codigo']} - {item['titulo']} - Cantidad: {item['cantidad']} - Precio unitario: ${item['precio']}")
    lines.append(f"TOTAL: ${total}")

    mensaje = "\n".join(lines)
    encoded = urllib.parse.quote(mensaje)

    numero_whatsapp = "58573906"  # reemplazar por el correcto completo si hace falta
    url = f"https://wa.me/{numero_whatsapp}?text={encoded}"

    return jsonify({"url": url})

@app.route("/carrito")
def carrito_view():
    return render_template("carrito.html")

if __name__ == "__main__":
    app.run(debug=True)
