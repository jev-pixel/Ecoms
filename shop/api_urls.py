# shop/api_urls.py - REST API URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'products', api_views.ProductViewSet, basename='product')
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'cart', api_views.CartViewSet, basename='cart')
router.register(r'orders', api_views.OrderViewSet, basename='order')
router.register(r'reviews', api_views.ReviewViewSet, basename='review')
router.register(r'wishlist', api_views.WishlistViewSet, basename='wishlist')
router.register(r'addresses', api_views.AddressViewSet, basename='address')

app_name = 'api'

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Authentication
    path('auth/register/', api_views.register, name='register'),
    path('auth/profile/', api_views.profile, name='profile'),
    path('auth/profile/update/', api_views.update_profile, name='update_profile'),
    
    # Statistics
    path('statistics/orders/', api_views.order_statistics, name='order_statistics'),
    path('statistics/products/', api_views.product_statistics, name='product_statistics'),
    
    # Dashboard
    path('dashboard/', api_views.dashboard, name='dashboard'),
    
    # Search
    path('search/', api_views.search_products, name='search'),
]