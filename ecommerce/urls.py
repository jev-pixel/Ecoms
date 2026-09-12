# ecommerce/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Shop app URLs (page views: home, products, cart, checkout, etc.)
    path('shop/', include('shop.urls')),

    # REST API (was previously duplicated with shop.urls at the same prefix —
    # removed that duplicate include so /api/ only serves the DRF endpoints)
    path('api/', include('shop.api_urls')),

    # Redirect root URL to /shop/
    path('', lambda request: redirect('shop:home'), name='home'),

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/shop/'), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve media files in development only.
# In production, WhiteNoise handles static files; media (user uploads)
# should go through a cloud storage backend (see settings.py note).
if settings.DEBUG or settings.SERVE_MEDIA_LOCALLY:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
