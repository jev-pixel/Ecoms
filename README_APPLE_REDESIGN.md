# Apple-Style Redesign — Setup Notes

## Where each file goes

| File here | Destination in your project |
|---|---|
| `static/css/apple-theme.css` | `static/css/apple-theme.css` (project root `static/` dir) |
| `templates/shop/base.html` | `shop/templates/shop/base.html` |
| `templates/shop/navbar.html` | `shop/templates/shop/navbar.html` |
| `templates/shop/_product_card.html` | `shop/templates/shop/_product_card.html` (new file) |
| `templates/shop/home.html` | `shop/templates/shop/home.html` |
| `templates/shop/product_list.html` | `shop/templates/shop/product_list.html` |
| `templates/shop/product_detail.html` | `shop/templates/shop/product_detail.html` |
| `templates/shop/cart.html` | `shop/templates/shop/cart.html` |
| `templates/shop/checkout.html` | `shop/templates/shop/checkout.html` |
| `templates/shop/login.html` | `shop/templates/shop/login.html` |
| `templates/shop/register.html` | `shop/templates/shop/register.html` |
| `templates/shop/order_success.html` | `shop/templates/shop/order_success.html` (**new file — this template never existed, checkout was crashing after a successful order**) |
| `templates/shop/my_orders.html` | `shop/templates/shop/my_orders.html` (**new file — never existed, `/shop/orders/` was crashing**) |
| `templates/shop/order_detail.html` | `shop/templates/shop/order_detail.html` (**new file — never existed**) |
| `templates/shop/profile.html` | `shop/templates/shop/profile.html` (**new file — never existed, `/shop/profile/` was crashing**) |

`apple-theme.css` was also updated (added `.badge`, `.list-row`, `.panel` classes for the new pages) — re-copy it even if you already copied an earlier version.

All of these use the exact template names your `views.py` already renders, and the exact context variable names your views already pass — so no Python changes are needed, just drop the files in and reload.

## Two small bugs fixed along the way

1. **`login.html`** previously linked to `{% url 'password_reset' %}` with no namespace. Because `django.contrib.auth.urls` is included without a namespace in your main `urls.py`, that accidentally pointed at **Django's default, unstyled** password reset page instead of your own `shop/password_reset.html`. Fixed to `{% url 'shop:password_reset' %}`.
2. **`register.html`** now matches the corrected `register()` view from earlier — a single `full_name` field, split server-side, instead of nonexistent `first_name`/`last_name` POST keys.

## What's covered vs. still on the old design

**Redesigned now:** home, navbar/footer shell, product list, product detail, cart, checkout, login, register.

**Redesigned now (round 2):** order confirmation, order history, order detail, profile — these didn't just need a visual refresh, they **didn't exist as files at all**, so hitting `/shop/orders/`, `/shop/profile/`, or completing checkout would 500 error regardless of styling.

**Still on the old design** (functional, just visually inconsistent until redesigned): wishlist, notifications, addresses, password reset pages. They'll still work — they just won't match the new look yet. Since they all extend the same `base.html` pattern, redesigning them is a matter of rewriting each page's inner markup using the same CSS classes already defined in `apple-theme.css` (`.product-grid`, `.field`, `.panel`, `.list-row`, `.auth-card`, etc.) — happy to do that pass next.

**Known but not yet hit:** `shop/password_reset_done.html`, `shop/password_reset_confirm.html`, and `shop/password_reset_complete.html` also don't exist in the project. Only `shop/password_reset.html` (the initial "enter your email" form) does. The full reset flow will crash on the second step if anyone actually tries it — worth fixing before relying on "forgot password" in production.

## After copying files in

1. Run `python manage.py collectstatic` if `DEBUG=False`, or just `runserver` locally (static files are served automatically in dev).
2. Hard-refresh the browser (Ctrl+Shift+R) to bypass any cached old CSS.
3. Check `/shop/`, `/shop/products/`, a product detail page, `/shop/cart/`, `/shop/checkout/` (needs items in cart + an address), `/shop/login/`, and `/shop/register/`.

## One design decision worth knowing

These new templates drop Bootstrap entirely in favor of the custom `apple-theme.css` system, to get true control over the minimal Apple look (Bootstrap's utility classes fight against that aesthetic). If any *other* page still extends Bootstrap classes directly, it'll keep working since Bootstrap's CDN link was only ever included per-page — but it means the old and new pages won't visually match until everything is migrated.
