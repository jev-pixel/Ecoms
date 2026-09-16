from django.urls import path
from . import views
from . import cashier_views
from django.contrib.auth import views as auth_views

app_name = 'shop'

urlpatterns = [
    # ==================== HOME ====================
    path('', views.home, name='home'),
    
    # ==================== PRODUCTS ====================
    path('products/', views.product_list, name='product_list'),
    path('products/category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    
    # ==================== CART ====================
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    
    # ==================== CHECKOUT & ORDERS ====================
    path('checkout/payment-method/', views.select_payment_method, name='select_payment_method'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/online-payment/<int:order_id>/', views.online_payment, name='online_payment'),
    path('checkout/online-payment/<int:order_id>/confirm/', views.confirm_online_payment, name='confirm_online_payment'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # ==================== CASHIER DASHBOARD (staff only) ====================
    path('cashier/', cashier_views.dashboard, name='cashier_dashboard'),
    path('cashier/scan/', cashier_views.scan, name='cashier_scan'),
    path('cashier/order/<uuid:qr_token>/', cashier_views.order_lookup, name='cashier_order_lookup'),
    path('cashier/order/<uuid:qr_token>/punch/', cashier_views.punch_order, name='cashier_punch_order'),

    # ==================== USER PROFILE ====================
    path('profile/', views.profile, name='profile'),
    path('addresses/', views.manage_addresses, name='manage_addresses'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    
    # ==================== WISHLIST ====================
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),  # NEW
    
    # ==================== NOTIFICATIONS ====================
    path('notifications/', views.notifications, name='notifications'),  # NEW
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),  # NEW
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),  # NEW
    
    # ==================== AUTHENTICATION ====================
    path('login/', auth_views.LoginView.as_view(
        template_name='shop/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='shop/password_reset.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='shop/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='shop/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='shop/password_reset_complete.html'
    ), name='password_reset_complete'),
]