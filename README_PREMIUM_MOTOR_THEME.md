# Premium Motor Shop Theme — Setup Notes

## What changed and why

Your screenshot showed the mismatch clearly: the site is styled like a light,
Apple-style consumer template, but the hero text still said *"Instruments
worth playing"* and talked about guitars/musicians, while the actual catalog
is Rims / Seats / Tires. The footer also still said "© Serotonin" instead of
your real brand name. That's leftover copy from an earlier template pass.

This pass re-skins the same class structure (`.hero`, `.product-card`,
`.filter-pill`, `.summary-card`, etc.) with an automotive palette and copy,
so **no Python/view changes are needed** — just drop in these files.

- **Charcoal + chrome + racing-red** instead of the Apple blue/white
- **Dark nav, hero, footer, and cart summary** for a "garage bay" feel
- **Bold, uppercase, tracked-out headings** instead of soft SF-Pro type
- Category tiles get a small red accent tick + desaturate-on-hover effect
- Hero gets a small uppercase eyebrow line ("PRECISION · PERFORMANCE · PARTS")

## Files to copy in

| File here | Destination |
|---|---|
| `premium-motor-theme.css` | `static/css/premium-motor-theme.css` (new file — keep `apple-theme.css` too, or delete it once you confirm the new one works) |
| `base.html` | `shop/templates/shop/base.html` (swaps the stylesheet link + fixes the footer copy/brand name) |
| `home.html` | `shop/templates/shop/home.html` (fixes the hero copy to match a motor shop instead of a music store) |

## After copying in

1. `python manage.py collectstatic` if `DEBUG=False`, otherwise just reload
   locally.
2. Hard refresh (Ctrl+Shift+R) to bypass cached CSS.
3. Check `/shop/`, `/shop/products/`, a product detail page, `/shop/cart/`,
   `/shop/checkout/`, `/shop/login/`.

## Worth doing next (not included here, since they touch more files/content)

- **Category images**: the rims/seats/tire photos in your screenshot look
  slightly warm/oversaturated next to the new charcoal palette — the new
  CSS desaturates them slightly and sharpens on hover, but swapping in
  studio-shot product photography (consistent lighting/background) would
  read a lot more "premium" than lifestyle stock photos.
- **`product_list.html` / `product_detail.html` / `checkout.html` / etc.**
  already use the shared classes this theme restyles, so they'll pick up
  the new look automatically — no changes needed there.
- **Pages still on the old Bootstrap look** (per your own
  `README_APPLE_REDESIGN.md`): `wishlist.html`, `notifications.html`,
  `addresses.html`, `password_reset*.html`, `loginsample.html`,
  `products.html` — these don't extend `base.html` at all, so they won't
  inherit this theme. If you want a fully consistent "premium motor shop"
  feel site-wide, those are the next ones to convert to extend
  `shop/base.html` and use the shared classes above.
- Consider renaming the brand consistently — `page.html` and a couple of
  other unused template variants still float around; worth deleting once
  you confirm which templates are live (your `views.py` only ever renders
  the ones wired up in `urls.py`).
