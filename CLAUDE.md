# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

RM KITS is a Spanish-language wholesale ("mayorista") shopping-cart web app built with Flask. Customers browse a product catalog, build a cart (persisted in `localStorage`), and finalize orders — which are saved to SQLite and handed off to WhatsApp with a prefilled message. An admin panel manages products, categories, orders, "new products", featured clients, and price lists. Deployed on Render.

Everything user-facing is in Spanish (Argentine): currency `es-AR`, prices in ARS, "CABA"/"GBA" shipping zones. Keep new strings in Spanish.

## Commands

```bash
pip install -r requirements.txt
python app.py            # dev server, http://localhost:5000 (debug from FLASK_DEBUG)
gunicorn app:app         # production entrypoint (see procfile)
```

There is **no test suite, linter, or build step**. `runtime.txt` pins Python 3.11.9 for Render.

## Architecture

### Single-file backend
All routes and logic live in **`app.py`** (~2600 lines). `config.py` holds the `Config` class (loaded via `app.config.from_object`). There are no blueprints, models, or ORM — raw `sqlite3` via the `get_db_connection()` context manager (`conn.row_factory = sqlite3.Row`; callers do `dict(row)`).

Route groups in `app.py`:
- **Storefront**: `/`, `/carrito`, `/guardar-pedido` (POST, saves order + sends confirmation email), `/gracias`, `/enviar_pedido` (legacy, unused), `/uploads/<filename>` (serves persistent images).
- **Admin** (`/admin/...`): all protected by the `@login_required` decorator (session-based, checks `session['admin_logged_in']`). Covers dashboard, productos, categorias, pedidos, productos-nuevos, clientes-destacados, lista-precios, Excel up/download, and full JSON+images backup export/import.

### Database — expected to pre-exist
The `producto` table is **never created by the code**. The app assumes a seeded `productos.db` is already present at `Config.DATABASE_PATH`; `init_database()` and `migrar_categorias_existentes()` bail out early (with warnings) if the DB or `producto` table is missing, and the app still boots. Only `categoria`, `producto_nuevo`, and `pedido` are auto-created.

`producto` columns (inferred from queries): `id, codigo, titulo, descripcion, precio, minimo, multiplo, stock, imagen, categoria, activo`. Products are populated/updated by uploading an Excel file in the admin panel (`/admin/subir-excel`) with exact headers: `ID, Código, Título, Descripción, Precio, Mínimo, Múltiplo, Stock, Categoría, Activo`.

Schema migrations are done ad hoc inline: `try: SELECT <col> ... except sqlite3.OperationalError: ALTER TABLE ADD COLUMN`. Follow that pattern for new columns. `pedido` IDs are forced to start at 1200 via `sqlite_sequence`.

Product identity across Excel re-imports is by **`codigo`**, not `id` (IDs get reassigned) — the cart re-syncs price/stock/image by `codigo` in `/carrito`.

### Persistent storage
`Config.PERSISTENT_DATA_PATH` is hardcoded to `/data` (a Render persistent disk). Both the SQLite DB (`/data/productos.db`) and product images (`/data/img/`) live there so they survive redeploys. `init_persistent_storage()` runs at import time to create these dirs and log diagnostics. **Local dev gotcha**: the path is `/data` regardless of environment, so local runs need `/data` to exist and be writable, or you must edit `config.py`. The migration-from-legacy-locations block only runs when `PERSISTENT_DATA_PATH != '/data'`.

### WhatsApp number config
The destination WhatsApp number is **not** in `config.py` for the storefront flow — it's stored in `/data/whatsapp_config.json` (`{activo, numeros}`) and edited from the admin dashboard. Read/write via `leer_config_whatsapp()` / `guardar_config_whatsapp()`. `Config.WHATSAPP_NUMBER` is only a fallback used by the index page. The frontend receives it as `window.WHATSAPP_NUMERO`.

### Frontend
No framework. Templates in `templates/` (storefront) and `templates/admin/` (extends `admin/base.html`). Static JS in `static/js/` (`index.js`, `carrito.js`, `admin.js`). SweetAlert2 is loaded from CDN; everything else is vanilla JS.

- Server passes data to JS via `data-*` attributes (`{{ productos|tojson|safe }}`) and `window.*` assignments in inline `<script>` blocks.
- Cart state key: `localStorage["rmkits_carrito"]`.
- Asset cache-busting: `?v={{ asset_version('js/foo.js') }}` (mtime-based, via the `inject_asset_version` context processor). No need to bump versions manually.

### Auth
Admin credentials are plaintext in `config.py` (`ADMIN_USERS` dict). `login_required` gates admin routes. `@app.before_request` redirects http→https when behind Render's proxy (`X-Forwarded-Proto`).

### Email
`enviar_email_confirmacion()` sends an order confirmation via SMTP (Gmail by default, `MAIL_*` env vars). Silently no-ops if `MAIL_USERNAME` is still the placeholder. Failures are logged, never raised — they must not break the order flow.

## Documentation

Detailed feature docs (in Spanish) are in `docs/` — `ADMIN_MANUAL.md`, `ALMACENAMIENTO_PERSISTENTE.md`, `PANEL_ADMIN_README.md`, `PRODUCTOS_NUEVOS_README.md`, `ACTUALIZACION_CARRITO.md`, `MEJORAS.md`.
