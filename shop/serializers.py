# shop/serializers.py - Complete Serializers

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem,
    Payment, Review, Wishlist, Address, UserProfile
)


# ==================== USER SERIALIZERS ====================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        # Create user profile
        UserProfile.objects.create(user=user)
        return user


# ==================== CATEGORY SERIALIZERS ====================
class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'product_count', 'parent']
    
    def get_product_count(self, obj):
        return obj.products.filter(available=True).count()


# ==================== PRODUCT SERIALIZERS ====================
class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'category_name', 'brand',
            'price', 'compare_price', 'discount_percentage', 'image',
            'stock', 'is_featured', 'average_rating'
        ]
    
    def get_discount_percentage(self, obj):
        if obj.compare_price and obj.compare_price > obj.price:
            return round(((obj.compare_price - obj.price) / obj.compare_price) * 100, 2)
        return 0


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'category', 'brand', 'sku',
            'description', 'price', 'compare_price', 'discount_percentage',
            'stock', 'image', 'images', 'is_featured', 'available',
            'average_rating', 'review_count', 'created_at', 'updated_at'
        ]
    
    def get_images(self, obj):
        # If you have a separate ProductImage model, use it here
        # For now, just return the main image
        if obj.image:
            return [obj.image.url]
        return []
    
    def get_discount_percentage(self, obj):
        if obj.compare_price and obj.compare_price > obj.price:
            return round(((obj.compare_price - obj.price) / obj.compare_price) * 100, 2)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()


# ==================== CART SERIALIZERS ====================
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'subtotal', 'tax_amount', 'total', 'created_at', 'updated_at']


# ==================== ORDER SERIALIZERS ====================
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'payment_status',
            'subtotal', 'tax_amount', 'shipping_cost', 'total_amount',
            'shipping_full_name', 'shipping_phone', 'shipping_address',
            'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country',
            'billing_full_name', 'billing_phone', 'billing_address',
            'billing_city', 'billing_state', 'billing_postal_code', 'billing_country',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_number', 'created_at', 'updated_at']


# ==================== PAYMENT SERIALIZER ====================
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'payment_method', 'transaction_id', 'amount', 'status', 'created_at']
        read_only_fields = ['transaction_id', 'created_at']


# ==================== REVIEW SERIALIZER ====================
class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'product_name', 'user', 'rating', 'title',
            'comment', 'verified_purchase', 'is_approved', 'created_at'
        ]
        read_only_fields = ['user', 'verified_purchase', 'is_approved', 'created_at']


# ==================== WISHLIST SERIALIZER ====================
class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'created_at']


# ==================== ADDRESS SERIALIZER ====================
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'full_name', 'phone_number',
            'street_address', 'city', 'state', 'postal_code',
            'country', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']