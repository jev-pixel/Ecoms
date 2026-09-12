# Cleanup & Deployment Prep — What Changed and Why

## 1. Delete the FastAPI leftovers

These files belong to a separate, unfinished FastAPI backend that isn't
needed since the Django `shop` app already has its own models, cart,
checkout, and REST API. Keeping both means running two servers and keeping
them in sync for no benefit.

Delete from your real project (not touched here, since these were read-only
copies):

- `main.py` (the FastAPI version — keep Django's `manage.py`/`asgi.py`/`wsgi.py`)
- `database_auth.py`
- `auth_models.py`
- `setup_db.py`
- `auth.py`
- `crud_auth.py`
- `auth.db`
- `api_service.py`
- `views_api.py`
- Any URL patterns in `shop/urls.py` pointing at `views_api` functions
  (`api_home`, `api_product_list`, `api_checkout`, etc.) and their matching
  templates (`api_home.html`, `api_cart.html`, `api_checkout.html`,
  `api_order_success.html`, `api_product_detail.html`, `api_product_list.html`,
  `api_transactions.html`) — unless you're intentionally keeping this as a
  separate demo, in which case leave it as-is but don't deploy it publicly
  alongside the real store.

Also check `shop/views.py` — it defines `api_products` **twice** (two
functions with the same name). Only the second definition is ever used;
delete the first to avoid confusion.

## 2. Files in this folder — copy these into your project

| File | Destination | Purpose |
|---|---|---|
| `settings.py` | `ecommerce/settings.py` | Reads secrets from environment, adds WhiteNoise, supports Postgres via `DATABASE_URL` |
| `urls.py` | `ecommerce/urls.py` | Removes the duplicate `shop.urls` include at `/api/` |
| `requirements.txt` | project root | Dependencies for `pip install -r requirements.txt` |
| `Procfile` | project root | Tells Railway/Render/Heroku-style hosts how to run migrations and start gunicorn |
| `.env.example` | project root | Template — copy to `.env` and fill in real values for local dev |
| `.gitignore` | project root | Keeps `.env`, `db.sqlite3`, and `media/` out of version control |

## 3. Local setup after copying these in

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env: generate a real SECRET_KEY, leave DATABASE_URL unset to use SQLite locally
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 4. Deploying (Railway example — Render is nearly identical)

1. Push this repo to GitHub.
2. In Railway: **New Project → Deploy from GitHub repo**.
3. Add a **Postgres** service to the project — Railway auto-injects
   `DATABASE_URL` into your app's environment.
4. In your app service's **Variables** tab, add:
   - `SECRET_KEY` (generate one, don't reuse the dev one)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=<your-app>.up.railway.app`
   - `CORS_ALLOWED_ORIGINS=https://<your-app>.up.railway.app` (if needed)
5. Railway detects the `Procfile` automatically: runs `migrate` on release,
   then starts `gunicorn ecommerce.wsgi`.
6. Once deployed, run once via Railway's shell/console:
   ```bash
   python manage.py createsuperuser
   ```
7. Visit `https://<your-app>.up.railway.app/` — should redirect to `/shop/`.

## 5. Known gap: media files won't persist

Railway/Render containers are ephemeral — anything written to `MEDIA_ROOT`
(product images uploaded via `/admin/`) will disappear on the next deploy or
restart. This is fine to launch and test with, but before relying on it for
real product photos, swap in `django-storages` + an S3-compatible bucket
(Cloudinary also has a generous free tier and is simpler to set up for
Django `ImageField`s).
