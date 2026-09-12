# Deploying with GitHub + Docker

## 0. Clean up first (recommended)

Your repo has leftover FastAPI experiment files that `README_CLEANUP_AND_SETUP.md`
already flags for removal — do this before your first Docker build so none of
it ships:

- `shop/templates/shop/main.py` (FastAPI app + seed data with junk product names)
- `shop/api_service.py`, `shop/views_api.py`
- the `api_*` URL patterns in `shop/urls.py` and their templates
  (`api_home.html`, `api_cart.html`, `api_checkout.html`, `api_product_list.html`,
  `api_product_detail.html`, `api_transactions.html`, `api_order_success.html`)

None of this is required for Docker to work, but it's dead code pointing at a
service (`localhost:5000`/`8000`) that won't exist in the container, and one
of its seed items has a profane name — not something you want live.

## 1. Add the Docker files to your repo

Drop these four files (generated alongside this guide) into your project
root, next to `manage.py`:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `.env.docker.example`

## 2. Push to GitHub

```bash
git add Dockerfile docker-compose.yml .dockerignore .env.docker.example
git commit -m "Add Docker setup for containerized deployment"
git push origin main
```

Your existing `.gitignore` already excludes `.env`, `*.sqlite3`, `media/`,
etc., so secrets won't get committed.

## 3. Run it locally with Docker Desktop (sanity check)

On any machine with Docker Desktop installed and running:

```bash
git clone https://github.com/<you>/<your-repo>.git
cd <your-repo>
cp .env.docker.example .env
```

Edit `.env`:
- Generate a real `SECRET_KEY`:
  `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- Set a real `POSTGRES_PASSWORD`.
- Leave `DEBUG=False` (True is fine only while you're actively debugging locally).

Then:

```bash
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Open **http://localhost:8000** — you should see the storefront, and
**http://localhost:8000/admin/** for the admin panel.

Useful commands:
```bash
docker compose logs -f web      # tail app logs
docker compose exec web python manage.py <any management command>
docker compose down             # stop (data persists in the postgres_data volume)
docker compose down -v          # stop AND wipe the database volume
```

## 4. Making it reachable by other users/customers

This is the part that trips people up: **Docker Desktop itself doesn't put
anything on the public internet** — it only runs containers on your machine
(or your local network). `docker compose up` on your laptop makes the site
reachable at `http://localhost:8000` for you, and at
`http://<your-laptop's-LAN-IP>:8000` for other devices on the same Wi-Fi —
but not for anyone outside that network, and not reliably (it goes down
when your laptop sleeps or closes).

To have real customers reach it, you need the *same* Docker setup running on
a machine that's always on and has a public IP. Your options, roughly
easiest to most involved:

**A. A cloud VM you manage yourself** (DigitalOcean, Linode, AWS Lightsail,
a cheap VPS, etc.)
1. Spin up a small Ubuntu instance, install Docker Engine + the Compose
   plugin on it.
2. `git clone` your repo there (or set up a CI step that does it), copy your
   real `.env` onto the server (don't commit it), and run
   `docker compose up --build -d` — identical to step 3 above.
3. Point a domain's DNS `A` record at the VM's public IP.
4. Put a reverse proxy in front for HTTPS — either:
   - add an `nginx` + `certbot` service to `docker-compose.yml`, or
   - install **Caddy** on the host (simplest: automatic Let's Encrypt certs
     with a 2-line Caddyfile reverse-proxying to `localhost:8000`).
5. Add your domain to `ALLOWED_HOSTS` in `.env` and restart
   (`docker compose up -d --force-recreate web`).

**B. A platform that runs your Dockerfile for you** (Render, Railway,
Fly.io, AWS App Runner, etc.)
- These detect your `Dockerfile` automatically, build it, run it, give you
  HTTPS and a public URL out of the box, and usually offer a managed
  Postgres add-on you point `DATABASE_URL` at. Push to GitHub, connect the
  repo in their dashboard, set the same env vars (`SECRET_KEY`, `DEBUG`,
  `ALLOWED_HOSTS`, `DATABASE_URL`), and it deploys on every push. Least
  ops work, since you don't manage the server at all.
- (Your existing `Procfile` was written for this style of platform without
  Docker — once you add a `Dockerfile`, most of these platforms will prefer
  building from it instead, so you can typically drop the `Procfile`.)

**C. Docker Desktop's Kubernetes / "Docker Desktop for Teams" sharing
features** — these help teammates run the same containers consistently on
*their own* machines for development; they don't expose a container to the
public internet either. Still useful if this app has co-developers who all
need an identical local environment.

## 5. Production checklist before pointing real customers at it

- `DEBUG=False` and `SECRET_KEY` is a freshly generated, non-default value.
- `ALLOWED_HOSTS` lists your real domain (and only what's needed).
- Media uploads (`media_volume`) persist across restarts because they're a
  named Docker volume — but if you ever move to a multi-server or
  auto-scaling setup, switch to S3/Cloudinary via `django-storages` as your
  own `settings.py` comment already suggests, since a local volume won't be
  shared across multiple app instances.
- Take periodic backups of the `postgres_data` volume
  (`docker compose exec db pg_dump ...`) — a Docker volume alone isn't a
  backup strategy.
