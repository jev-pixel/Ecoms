# shop/api_views.py - REST API ViewSets and Views

from rest_framework import viewsets, status, permissions, serializers  # Add serializers here
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem,
    Payment, Review, Wishlist, Address
)
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, CategorySerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, PaymentSerializer,
    ReviewSerializer, WishlistSerializer, AddressSerializer,
    UserSerializer, UserRegistrationSerializer
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for products
    list: Get all products
    retrieve: Get single product
    """
    queryset = Product.objects.filter(available=True)
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(brand__icontains=search)
            )
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by brand
        brand = self.request.query_params.get('brand', None)
        if brand:
            queryset = queryset.filter(brand__iexact=brand)
        
        # Filter featured products
        featured = self.request.query_params.get('featured', None)
        if featured:
            queryset = queryset.filter(is_featured=True)
        
        # Sorting
        sort_by = self.request.query_params.get('sort', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get reviews for a product"""
        product = self.get_object()
        reviews = Review.objects.filter(product=product, is_approved=True)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for categories
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class CartViewSet(viewsets.ModelViewSet):
    """
    API endpoint for shopping cart
    """
    serializer_class = CartSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            return Cart.objects.filter(session_key=session_key)
    
    def get_or_create_cart(self):
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id, available=True)
        
        if quantity > product.stock:
            return Response(
                {'error': 'Not enough stock available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart = self.get_or_create_cart()
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                cart_item.quantity = product.stock
            cart_item.save()
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """Update cart item quantity"""
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        cart = self.get_or_create_cart()
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        
        if quantity <= 0:
            cart_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        if quantity > cart_item.product.stock:
            return Response(
                {'error': 'Not enough stock available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item.quantity = quantity
        cart_item.save()
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        product_id = request.data.get('product_id')
        cart = self.get_or_create_cart()
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from cart"""
        cart = self.get_or_create_cart()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for orders
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items')
    
    def create(self, request):
        """Create a new order from cart"""
        # Get cart
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not cart or not cart.items.exists():
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get addresses
        shipping_address_id = request.data.get('shipping_address_id')
        billing_address_id = request.data.get('billing_address_id')
        payment_method = request.data.get('payment_method')
        notes = request.data.get('notes', '')
        
        shipping_address = get_object_or_404(Address, id=shipping_address_id, user=request.user)
        billing_address = get_object_or_404(Address, id=billing_address_id, user=request.user)
        
        # Check stock availability
        for item in cart.items.all():
            if item.quantity > item.product.stock:
                return Response(
                    {'error': f'Not enough stock for {item.product.name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Calculate totals
        subtotal = cart.subtotal
        tax_amount = cart.tax_amount
        shipping_cost = 50.00  # Fixed shipping cost
        total_amount = subtotal + tax_amount + shipping_cost
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            shipping_full_name=shipping_address.full_name,
            shipping_phone=shipping_address.phone_number,
            shipping_address=shipping_address.street_address,
            shipping_city=shipping_address.city,
            shipping_state=shipping_address.state,
            shipping_postal_code=shipping_address.postal_code,
            shipping_country=shipping_address.country,
            billing_full_name=billing_address.full_name,
            billing_phone=billing_address.phone_number,
            billing_address=billing_address.street_address,
            billing_city=billing_address.city,
            billing_state=billing_address.state,
            billing_postal_code=billing_address.postal_code,
            billing_country=billing_address.country,
            notes=notes,
        )
        
        # Create order items and update stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_sku=item.product.sku,
                quantity=item.quantity,
                unit_price=item.product.price,
                total_price=item.total_price
            )
            
            # Update product stock
            product = item.product
            product.stock -= item.quantity
            product.save()
        
        # Create payment record
        Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=total_amount,
            status='pending' if payment_method != 'cash_on_delivery' else 'completed'
        )
        
        # Clear cart
        cart.items.all().delete()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        
        if order.status in ['shipped', 'delivered', 'cancelled']:
            return Response(
                {'error': 'Order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restore stock
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()
        
        order.status = 'cancelled'
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for product reviews
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        # Check if user already reviewed
        if Review.objects.filter(user=self.request.user, product=product).exists():
            raise serializers.ValidationError('You have already reviewed this product')
        
        # Check if user purchased this product
        verified_purchase = OrderItem.objects.filter(
            order__user=self.request.user,
            product=product,
            order__status='delivered'
        ).exists()
        
        serializer.save(
            user=self.request.user,
            product=product,
            verified_purchase=verified_purchase
        )


class WishlistViewSet(viewsets.ModelViewSet):
    """
    API endpoint for wishlist
    """
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    def create(self, request):
        """Add product to wishlist"""
        product_id = request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            return Response(
                {'message': 'Product already in wishlist'},
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(wishlist_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def remove(self, request):
        """Remove product from wishlist"""
        product_id = request.data.get('product_id')
        Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user addresses
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ==================== AUTHENTICATION APIs ====================
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration API"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get user profile"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== STATISTICS APIs ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_statistics(request):
    """Get user order statistics"""
    orders = Order.objects.filter(user=request.user)
    
    stats = {
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='pending').count(),
        'completed_orders': orders.filter(status='delivered').count(),
        'cancelled_orders': orders.filter(status='cancelled').count(),
        'total_spent': sum(order.total_amount for order in orders.filter(payment_status='paid')),
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([AllowAny])
def product_statistics(request):
    """Get product statistics"""
    stats = {
        'total_products': Product.objects.filter(available=True).count(),
        'featured_products': Product.objects.filter(is_featured=True, available=True).count(),
        'out_of_stock': Product.objects.filter(stock=0, available=True).count(),
        'low_stock': Product.objects.filter(stock__lte=10, stock__gt=0, available=True).count(),
    }
    
    return Response(stats)


# ==================== DASHBOARD APIs ====================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """User dashboard data"""
    user = request.user
    
    # Get recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get cart info
    cart = Cart.objects.filter(user=user).first()
    cart_count = cart.total_items if cart else 0
    
    # Get wishlist count
    wishlist_count = Wishlist.objects.filter(user=user).count()
    
    data = {
        'user': UserSerializer(user).data,
        'recent_orders': OrderSerializer(recent_orders, many=True).data,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'total_orders': Order.objects.filter(user=user).count(),
    }
    
    return Response(data)


# ==================== SEARCH API ====================
@api_view(['GET'])
@permission_classes([AllowAny])
def search_products(request):
    """Search products"""
    query = request.GET.get('q', '')
    
    if not query:
        return Response({'results': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(brand__icontains=query) |
        Q(category__name__icontains=query),
        available=True
    ).distinct()[:20]
    
    serializer = ProductListSerializer(products, many=True)
    return Response({'results': serializer.data})