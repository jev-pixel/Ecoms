# shop/admin.py — Practical admin configuration for day-to-day product entry

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem,
    Payment, Review, Wishlist, Coupon, Address, UserProfile, ProductImage
)


class ProductImageInline(admin.TabularInline):
    """Lets you attach extra gallery photos without leaving the product screen."""
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'display_order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'display_order')
    list_editable = ('is_active', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail', 'name', 'category', 'price', 'stock',
        'is_featured', 'available', 'sku',
    )
    list_display_links = ('thumbnail', 'name')
    list_editable = ('price', 'stock', 'is_featured', 'available')
    list_filter = ('category', 'available', 'is_featured', 'brand')
    search_fields = ('name', 'sku', 'brand', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('sku', 'created_at', 'updated_at')
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {'fields': ('category', 'name', 'slug', 'brand', 'description')}),
        ('Pricing & stock', {'fields': ('price', 'compare_price', 'stock', 'low_stock_threshold', 'weight')}),
        ('Media', {'fields': ('image',)}),
        ('Visibility', {'fields': ('available', 'is_featured')}),
        ('System', {'fields': ('sku', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:6px;">', obj.image.url)
        return "—"
    thumbnail.short_description = ''


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'total_price')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'user', 'payment_type', 'status', 'payment_status',
        'total_amount', 'confirmed_by', 'created_at',
    )
    list_filter = ('status', 'payment_status', 'payment_type', 'created_at')
    list_editable = ('status', 'payment_status')
    search_fields = ('order_number', 'user__username', 'user__email')
    readonly_fields = (
        'order_number', 'qr_token', 'subtotal', 'tax_amount', 'total_amount',
        'confirmed_by', 'confirmed_at', 'created_at', 'updated_at',
    )
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'verified_purchase', 'created_at')
    list_filter = ('is_approved', 'rating', 'verified_purchase')
    list_editable = ('is_approved',)
    search_fields = ('product__name', 'user__username', 'comment')
    actions = ['approve_reviews']

    @admin.action(description='Approve selected reviews')
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'valid_from', 'valid_to', 'used_count', 'usage_limit')
    list_editable = ('is_active',)
    search_fields = ('code',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'address_type', 'city', 'is_default')
    list_filter = ('address_type', 'is_default')
    search_fields = ('full_name', 'user__username', 'city')


# Simple registrations — no custom list view needed for these
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(Wishlist)
admin.site.register(UserProfile)
