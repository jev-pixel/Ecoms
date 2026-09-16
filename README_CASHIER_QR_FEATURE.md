# Cashier Dashboard + QR Code Checkout — Setup Notes

## What this adds

1. **Checkout now asks "Cash or Online?" first.** A new step
   (`/shop/checkout/payment-method/`) shows two cards — *Cash Payment*
   (pay at the counter) and *Online Payment* (GCash / Maya / card). The
   choice is stashed in the session and read by the existing `checkout()`
   view, which now only shows the online payment-method radios when
   "Online" was picked.
2. **Online payment gets its own separate flow.** After checkout, a
   cash order goes straight to `order_success`. An online order goes to
   a new `/shop/checkout/online-payment/<id>/` screen first — this is a
   **placeholder** ("I've completed payment" button) standing in for a
   real GCash/Maya/PayMongo redirect + webhook. Wire that in later
   without touching the rest of the flow.
3. **Every order gets a QR-code receipt** instead of a plain
   confirmation. It encodes a link straight to that order's cashier page
   (`/shop/cashier/order/<qr_token>/`), generated on the fly as a base64
   PNG (no media storage needed — works fine on Vercel's ephemeral
   filesystem). Shown on `order_success.html` and again on
   `order_detail.html` while the order is still active.
4. **New Cashier Dashboard** (`/shop/cashier/`, staff-only):
   - A queue of orders needing counter attention, filterable by status.
   - `/shop/cashier/scan/` — opens the device camera (via the
     `html5-qrcode` CDN library) to scan a customer's QR, with a manual
     order-number field as a fallback (e.g. no camera permission).
   - Scanning/looking up an order lands on `cashier_order_detail.html`,
     where a single button "punches" the order forward:
     cash order → collect payment & confirm → start preparing → mark
     served. Online orders skip the cash-collection step since they're
     already paid.

## Data model changes (`Order`)

| Field | Purpose |
|---|---|
| `payment_type` | `'cash'` or `'online'` — set at checkout, drives which cashier action shows |
| `qr_token` | Random UUID encoded into the QR code. Deliberately separate from `order_number` so a shown/printed code can't be used to enumerate other orders |
| `confirmed_by` | Which staff account punched the order at the counter |

`confirmed_at` already existed on `Order` and is now actually used —
it's stamped the first time a cashier confirms the order.

## Files to copy in

| File here | Destination |
|---|---|
| `shop/qr_utils.py` | `shop/qr_utils.py` (**new**) |
| `shop/cashier_views.py` | `shop/cashier_views.py` (**new**) |
| `shop/migrations/0004_order_qr_and_cashier_fields.py` | `shop/migrations/0004_order_qr_and_cashier_fields.py` (**new**) |
| `shop/models.py` | `shop/models.py` (replace — only `Order` changed) |
| `shop/views.py` | `shop/views.py` (replace) |
| `shop/urls.py` | `shop/urls.py` (replace) |
| `shop/admin.py` | `shop/admin.py` (replace) |
| `shop/templates/shop/navbar.html` | same path (replace — adds staff-only Cashier link) |
| `shop/templates/shop/checkout.html` | same path (replace) |
| `shop/templates/shop/cart.html` | same path (replace — checkout link now goes through payment-method choice) |
| `shop/templates/shop/order_success.html` | same path (replace) |
| `shop/templates/shop/order_detail.html` | same path (replace) |
| `shop/templates/shop/select_payment_method.html` | same path (**new**) |
| `shop/templates/shop/online_payment.html` | same path (**new**) |
| `shop/templates/shop/cashier_dashboard.html` | same path (**new**) |
| `shop/templates/shop/cashier_scan.html` | same path (**new**) |
| `shop/templates/shop/cashier_order_detail.html` | same path (**new**) |
| `static/css/append_to_premium-motor-theme.css` | **append its contents** to the bottom of `static/css/premium-motor-theme.css` — don't overwrite the file |
| `requirements.txt` | replace (adds `qrcode[pil]`) |

I also fixed two pre-existing bugs while rewriting `views.py`:
- `notifications()` / `mark_notification_read()` used the `Notification`
  model without importing it — added to the import line.
- Removed the two dead, duplicate `api_products()` view definitions that
  called an undefined `ECommerceAPI` (already flagged in
  `README_CLEANUP_AND_SETUP.md` for deletion, and unreachable anyway
  since nothing in `urls.py` pointed at them).

## After copying files in

```bash
pip install -r requirements.txt        # pulls in qrcode[pil]
python manage.py migrate               # applies 0004_order_qr_and_cashier_fields
```

Then, for Docker:
```bash
docker compose exec web pip install -r requirements.txt
docker compose exec web python manage.py migrate
```

### Give someone cashier access

The counter account just needs `is_staff = True` — it does **not** need
to be a superuser or have any admin permissions. In `/admin/`:
**Users → (pick the account) → check "Staff status" → Save.**

## Trying it end to end

1. As a shopper: add items to cart → **Proceed to checkout** →
   choose **Cash Payment** → fill in address/notes → **Place order** →
   land on `order_success.html` with a QR code.
2. Log in as a staff account in another browser/incognito window →
   `/shop/cashier/` → **Scan a QR code** → point the camera at the QR
   (or type the order number) → **Collect ₱X cash & confirm**.
3. Repeat with **Online Payment** instead — you'll pass through the
   placeholder `online_payment.html` screen first; the cashier side
   skips straight to "Start preparing" since it's already paid.

## Worth doing next (not included here — separate follow-ups)

- **Real payment gateway.** `confirm_online_payment()` in `views.py` is
  the one function to replace with an actual GCash/Maya/PayMongo/QR Ph
  redirect + webhook — everything else (QR receipt, cashier dashboard)
  stays the same regardless of which gateway you plug in.
- **A dedicated "Ready/Served" status** — right now the cashier punch
  button reuses `Order.STATUS_CHOICES` (`pending → confirmed →
  processing → delivered`), where "Delivered" is standing in for
  "picked up at the counter." Renaming or adding a status is a one-line
  change in `models.py` + a migration if you want the label to read
  better for a pickup counter instead of a delivery order.
- **Live queue updates.** The dashboard is a normal page load right
  now; adding simple polling (like `navbar.html`'s existing cart-badge
  fetch) or a small WebSocket channel would let the counter screen
  refresh itself as new orders come in, instead of needing a manual
  reload.
