# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

RM KITS is a wholesale ("mayorista") shopping cart built with Flask, raw `sqlite3` and vanilla JS. It is deployed on Render (`procfile` runs `gunicorn app:app`; `runtime.txt` pins Python 3.11.9). Customers browse the catalog and build a cart in `localStorage`. At checkout the order is saved to SQLite, then handed off to WhatsApp as a prefilled message. `/admin` is the back office: products, categories, orders, "productos nuevos", clientes destacados, a price list, and Excel/backup import and export.

The codebase is written in Spanish: identifiers, comments, commit messages and UI copy. UI copy uses Argentine voseo ("Ingresá", "Revisá") and formats prices in ARS with `es-AR`. Keep new code in the same style.

## Commands

There are no tests, linters, formatters or build step.

```bash
python3.11 -m venv venv && source venv/bin/activate   # or: uv venv --python 3.11 venv
pip install -r requirements.txt   # needs Python 3.11–3.13: the pinned pandas has no wheels for 3.14+ (pandas isn't imported anywhere)
python app.py        # dev server on :5000; set FLASK_DEBUG=true for debug/reload
```

### Running locally

`config.py` hardcodes `PERSISTENT_DATA_PATH = "/data"`, the Render persistent disk. Production depends on that value, so don't commit a different one. README and `docs/` describe a `PERSISTENT_DATA_PATH` env var, but the code no longer reads it. `RENDER` is read but unused. If `/data` isn't writable, the app still boots and only logs errors: the catalog renders empty and `/admin` bounces back to the login page.

To run against a local folder without editing `config.py`, patch `Config` before importing the app (`data/` is gitignored):

```bash
python -c "
from config import Config as C
C.PERSISTENT_DATA_PATH='data'; C.DATABASE_PATH='data/productos.db'; C.UPLOAD_FOLDER='data/img'
import app; app.app.run(debug=True)"
```

If the data path isn't `/data`, `init_persistent_storage()` also runs a legacy migration at startup. It copies `static/img/*` into the upload folder and moves a repo-root `productos.db` into the data folder.

The database must already contain a `producto` table, because the code never creates one. To bootstrap an empty DB:

1. Create `producto` with the columns listed under Database below.
2. Start the app.
3. Restore a backup ZIP from the dashboard ("importar todo").

## Architecture

### Backend: one file

All routes and logic live in `app.py` (~2600 lines). There are no blueprints, models or ORM, and `config.py` holds the `Config` class.

- DB access always goes through `with get_db_connection() as conn:`. Rows are `sqlite3.Row` (callers use `dict(row)`), and callers must call `conn.commit()` themselves.
- `init_persistent_storage()`, `init_database()` and `migrar_categorias_existentes()` run at import time, including under gunicorn.
- Admin routes use `@login_required`, which checks the session flag `admin_logged_in`. Admin users come from the plaintext `Config.ADMIN_USERS` dict; the `ADMIN_USERNAME`/`ADMIN_PASSWORD` env vars are read but unused.
- AJAX endpoints return `{"success": bool, "error": str}`. Form endpoints `flash()` and redirect.
- Some leftovers aren't wired into anything:
  - `/enviar_pedido`
  - `/gracias` (checkout never navigates there)
  - `templates/admin/edicion_rapida.html` (no route renders it, and it calls endpoints that don't exist)

### Database (`/data/productos.db`)

- **`producto` table:** columns are `id, codigo, titulo, descripcion, precio, minimo, multiplo, stock, imagen, categoria, activo`. The code never creates this table. If it's missing, `init_database()` skips all setup and only logs a warning. Only `categoria`, `producto_nuevo` and `pedido` are auto-created.
- **Migrations:** these are ad hoc: `try: SELECT <col> … except sqlite3.OperationalError: ALTER TABLE … ADD COLUMN`. The pattern is repeated in `init_database()`, `guardar_pedido()` and `admin_importar_todo()`; follow it for new columns. Careful: `guardar_pedido()` drops and recreates `pedido` if the `envio_direccion` column is missing.
- **Order numbers:** `pedido.id` starts at 1200 (seeded via `sqlite_sequence`) and doubles as the order number shown in confirmation emails and in the WhatsApp messages the admin sends from the pedidos page.
- **Order contents:** `pedido.productos` is a JSON string of the cart items (`codigo, titulo, precio, cantidad, …`). There is no line-items table; stats, "más vendidos" and exports parse this JSON in Python.
- **Categories:** `producto.categoria` stores the category *name*, and the `categoria` table is just the list of names. Renaming or deleting a category rewrites the matching products by name.
- **Product identity:** a product's stable key is `codigo`, not `id`. Codes look like `A0001` and come from `generar_codigo_producto()`. Excel re-imports can reassign ids, so `/carrito` re-syncs the cart by `codigo`.
- **Product images:** they live in the upload folder (`/data/img`) as `<codigo>.<ext>`. `producto.imagen` holds the filename, and images are served at `/uploads/<filename>`. They are not in the repo; `static/img` only has the logo and favicon.
- **Customer identity:** clientes destacados, and the per-customer order counts in the pedidos list, identify a customer by the last 8 digits of the phone number (`normalizar_telefono()`). Only orders in `ESTADOS_PEDIDO_REALIZADO` count.

### Etiquetas (product highlights)

- **Tables:** `etiqueta` holds `nombre`, `color` and `prioridad` (1 = shown first). `etiqueta_asignacion` links a label to either a `producto_codigo` or a `categoria_id`, with inclusive `fecha_inicio`/`fecha_fin` stored as `YYYY-MM-DD` text. Both tables are created in `init_database()`. The example labels (Nuevo, Descuento, Oportunidad) are seeded only when the `etiqueta` table is first created.
- **Storefront order:** `destacar_productos_con_etiqueta()` runs in `index()`. It gives each product its active label; if a product has several (direct or via its category), the highest priority wins. Labeled products are sorted first, and everything else keeps its `codigo` order. `index.js` draws the badge (`.etiqueta-producto`), and choosing a price sort there overrides this order.
- **Dates:** "today" comes from `hoy_local()`, which uses Argentina time, not the server's UTC. An expired assignment stops showing right away, and its row is deleted the next time `/admin/etiquetas` is opened.
- **Manual cascades:** SQLite foreign keys aren't enforced here, so editing a product's code, deleting a product, or deleting a category updates `etiqueta_asignacion` by hand in those routes. Labels are not part of the "exportar todo" backup.

### Catálogo de mochilas (admin only)

- **What it is:** a second catalog, separate from the store's products, ported from a Windows Flask app the user had (`Catálogo de Mochilas`, packaged with PyInstaller). It lives entirely under `/admin/mochilas`: list, catalog view, add/edit/delete, activate/deactivate, and a PDF to share. Nothing about it is public except the photo files.
- **Data:** table `mochila` in the same `productos.db` (`modelo, precio, cantidad, descripcion, medidas, imagen, activada, orden`). Photos go in `UPLOAD_FOLDER/mochilas` and are served at `/uploads/mochilas/<file>`. Only rows with `activada = 1` appear in the catalog view and the PDF.
- **Seed:** `datos_iniciales/mochilas/` holds the original app's 31 items (`mochilas.json`) and their photos. `importar_mochilas_iniciales()` loads them once, when `init_database()` first creates the table.
- **PDF:** built with fpdf2 + Pillow in `generar_pdf_mochilas()`, A4 with two items per page, matching the original layout (the `PDF_*` constants are millimetres). The core PDF fonts are latin-1 only, so every string goes through `texto_pdf()` first; a detail line that doesn't fit between the model and the price is shortened with "...".
- **Prices:** integers, shown as `$ 12.990` through the `precio_ar` Jinja filter — the store's own templates format prices differently (`{:,.0f}`).

### Checkout flow

1. `static/js/carrito.js` validates the form and POSTs JSON to `/guardar-pedido`.
2. `/guardar-pedido` saves the order and sends a confirmation email over SMTP. The email is skipped while `MAIL_USERNAME` is still the placeholder, and SMTP errors are logged, never raised.
3. The page then goes to `https://wa.me/<number>?text=…` via `window.location.href`. This is intentional: `window.open` gets blocked by Android Chrome after an `await`. The message is built after the save, because its last line is the order's PDF link.

The PDF is generated on every request and never stored. `generar_pdf_pedido()` builds it for both the admin button (`/admin/pedidos/<id>/pdf`) and the public link `/pedido/<id>/<pdf_token>.pdf`. `pdf_token` is a random column set by `/guardar-pedido`; orders without one (older, manual or Excel-imported) have no public link.

The destination number is runtime config, not `config.py`. It lives in `<data>/whatsapp_config.json` (`{activo, numeros}`) and is edited from the admin dashboard. `leer_config_whatsapp()` reads it, and `carrito.html` injects it as `window.WHATSAPP_NUMERO`.

### Values duplicated across layers

Several `Config` values aren't the real source of truth because the frontend hardcodes them. When you change one, grep for every copy:

- **Minimum order (200000):** `carrito.js`, `index.html`, `carrito.html` and `Config.PEDIDO_MINIMO`. It's enforced client-side only; `/guardar-pedido` doesn't check it.
- **Products per page (24):** set in `index.js`. `Config.PRODUCTOS_POR_PAGINA` is unused.
- **Store address, hours and contact WhatsApp number:** `carrito.js`, `index.js`, `carrito.html`, `gracias.html`, `admin/pedidos.html`, and the email HTML in `enviar_email_confirmacion()`.
- **Order states:** in `app.py`, `estados_validos` in `admin_pedido_estado()` and `ESTADOS_PEDIDO_REALIZADO`. In `templates/admin/pedidos.html`, the JS `estados` list and the Jinja billed/unbilled filters.
- **Quantity rules (mínimo/múltiplo/stock):** implemented twice on the client: `snapCantidad()` in `index.js`, and `corregirValor()`/`normalizarItem()` in `carrito.js`.

### Frontend

There's no framework or bundler. SweetAlert2, and Chart.js on the dashboard, load from the jsDelivr CDN.

- **Catalog:** the whole catalog is embedded as JSON in `#productos[data-productos]`. Search, category filter, sorting and pagination all run client-side in `index.js`.
- **Cart:** cart state lives in `localStorage["rmkits_carrito"]`.
- **Lightbox:** `lightbox.js` attaches by event delegation to `.card .img-wrapper, .cart-item-imagen`. On touch devices it deliberately doesn't zoom on tap, because users pinch-zoom instead.
- **Cache-busting:** include storefront static files as `?v={{ asset_version('js/x.js') }}`. `asset_version` comes from the `inject_asset_version` context processor and uses the file's mtime.
- **`config` in templates:** storefront routes pass their own `config` dict to the templates, which shadows Flask's `config` global there.
- **Admin templates:** they extend `admin/base.html` and carry most of their JS and CSS inline. `static/js/admin.js` is only loaded by `admin/productos.html`.

### Admin import/export

- **Products Excel** (`/admin/descargar-excel` ↔ `/admin/subir-excel`): headers must be exactly `ID, Código, Título, Descripción, Precio, Mínimo, Múltiplo, Stock, Categoría, Activo`. Rows that have an `ID` upsert by id; rows without one upsert by `codigo`.
- **Orders:** export produces a ZIP of two xlsx files (datos + productos). Import needs both files, does `INSERT OR REPLACE` by id, and re-reads titles and prices from the current products.
- **Full backup:** `/admin/exportar-todo` produces a ZIP with productos, pedidos and productos_nuevos as JSON, plus the images of "productos nuevos" only. `/admin/importar-todo` **deletes and replaces** all products, orders and productos_nuevos.

### Configuration gotchas

- `python-dotenv` is in requirements but never loaded, so `.env` files are ignored. `SECRET_KEY`, `FLASK_DEBUG` and `MAIL_*` must come from the real environment.
- `docs/` (in Spanish) is partly outdated. It references `importar_excel.py` (gone), Heroku, the `PERSISTENT_DATA_PATH` env var and a `/admin/backup` route. Trust the code over the docs.
