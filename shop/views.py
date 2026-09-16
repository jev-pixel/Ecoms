# shop/views.py - Complete Views

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem, 
    Payment, Review, Wishlist, Coupon, Address, UserProfile, Notification
)
from .qr_utils import generate_qr_code_data_uri

# Note: the old duplicate `api_products()` views (calling an undefined
# `ECommerceAPI`) have been removed here — they weren't wired to any URL
# and README_CLEANUP_AND_SETUP.md already flagged them for deletion.


# ==================== HOME ====================
def home(request):
    """Homepage with featured products and categories"""
    featured_products = Product.objects.filter(
        available=True, 
        is_featured=True
    )[:8]
    
    categories = Category.objects.filter(is_active=True, parent=None)[:6]
    
    # Get latest products
    latest_products = Product.objects.filter(available=True).order_by('-created_at')[:8]
    
    # Get products on sale
    sale_products = Product.objects.filter(
        available=True,
        compare_price__isnull=False
    ).exclude(compare_price__lte=F('price'))[:8]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
        'latest_products': latest_products,
        'sale_products': sale_products,
    }
    return render(request, 'shop/home.html', context)


# ==================== PRODUCTS ====================
def product_list(request, category_slug=None):
    """Product listing with filters and search"""
    products = Product.objects.filter(available=True)
    categories = Category.objects.filter(is_active=True)
    selected_category = None
    
    # Filter by category
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(brand__icontains=search_query)
        )
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Filter by brand
    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand=brand)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['price', '-price', 'name', '-name', '-created_at', 'created_at']
    if sort_by in valid_sorts:
        products = products.order_by(sort_by)
    
    # Get all brands for filter
    brands = Product.objects.filter(available=True).values_list('brand', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'brands': brands,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'shop/product_list.html', context)


def product_detail(request, product_id):
    """Product detail page with reviews"""
    product = get_object_or_404(Product, id=product_id, available=True)
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]
    
    # Get reviews
    reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
    
    # Check if user has purchased this product
    user_purchased = False
    user_reviewed = False
    if request.user.is_authenticated:
        user_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exists()
        user_reviewed = Review.objects.filter(
            user=request.user,
            product=product
        ).exists()
    
    # Handle review submission
    if request.method == 'POST' and request.user.is_authenticated:
        if not user_reviewed:
            rating = request.POST.get('rating')
            title = request.POST.get('title')
            comment = request.POST.get('comment')
            
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                title=title,
                comment=comment,
                verified_purchase=user_purchased
            )
            messages.success(request, 'Your review has been submitted and is pending approval.')
            return redirect('shop:product_detail', product_id=product.id)
        else:
            messages.warning(request, 'You have already reviewed this product.')
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'user_purchased': user_purchased,
        'user_reviewed': user_reviewed,
    }
    return render(request, 'shop/product_detail.html', context)


# ==================== CART ====================
def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, available=True)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        messages.error(request, 'Invalid quantity')
        return redirect('shop:product_detail', product_id=product_id)
    
    if quantity > product.stock:
        messages.error(request, 'Not enough stock available')
        return redirect('shop:product_detail', product_id=product_id)
    
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
            messages.warning(request, f'Only {product.stock} items available')
    else:
        cart_item.quantity = quantity
    
    cart_item.save()
    messages.success(request, f'{product.name} added to cart')
    
    return redirect('shop:view_cart')


def view_cart(request):
    """View shopping cart"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    # Calculate totals
    subtotal = cart.subtotal
    tax = cart.tax_amount
    total = cart.total
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
    }
    return render(request, 'shop/cart.html', context)


def update_cart(request, product_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, 'Item removed from cart')
        elif quantity > product.stock:
            messages.error(request, 'Not enough stock available')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated')
    
    return redirect('shop:view_cart')


def remove_from_cart(request, product_id):
    """Remove item from cart"""
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    
    CartItem.objects.filter(cart=cart, product=product).delete()
    messages.success(request, 'Item removed from cart')
    
    return redirect('shop:view_cart')


# ==================== CHECKOUT ====================
@login_required
def select_payment_method(request):
    """
    Checkout step 1: cash at the counter, or pay online now.
    Stored in the session so `checkout()` below knows which sub-flow
    (and which set of payment_method radio buttons) to show next.
    """
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty')
        return redirect('shop:product_list')

    if request.method == 'POST':
        payment_type = request.POST.get('payment_type')
        if payment_type not in ('cash', 'online'):
            messages.error(request, 'Please choose a payment option')
            return redirect('shop:select_payment_method')
        request.session['checkout_payment_type'] = payment_type
        return redirect('shop:checkout')

    return render(request, 'shop/select_payment_method.html', {'cart': cart})


ONLINE_PAYMENT_METHODS = ['gcash', 'maya', 'credit_card', 'debit_card']


@login_required
def checkout(request):
    """Checkout process — step 2, after select_payment_method has stored
    the cash/online choice in the session."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()

    if not cart_items:
        messages.warning(request, 'Your cart is empty')
        return redirect('shop:product_list')

    for item in cart_items:
        if item.quantity > item.product.stock:
            messages.error(request, f'Not enough stock for {item.product.name}')
            return redirect('shop:view_cart')

    # Without this, checkout.html's {% if payment_type == 'cash' %} branch
    # can't tell which payment sub-flow to render (it was previously always
    # falling through to the online branch, and cash orders had no way to
    # submit since that branch renders no payment_method inputs).
    payment_type = request.session.get('checkout_payment_type')
    if payment_type not in ('cash', 'online'):
        messages.info(request, 'Please choose how you want to pay first.')
        return redirect('shop:select_payment_method')

    # Only a shipping address is collected now — the separate billing-address
    # step was dropped to cut checkout friction. Order.billing_* fields still
    # exist in the schema, so they're mirrored from shipping below.
    shipping_addresses = Address.objects.filter(
        user=request.user,
        address_type__in=['shipping', 'both']
    )

    if not shipping_addresses.exists():
        messages.warning(request, 'Please add a shipping address before checking out.')
        return redirect('shop:manage_addresses')

    if request.method == 'POST':
        shipping_address_id = request.POST.get('shipping_address')
        notes = request.POST.get('notes', '')

        if not shipping_address_id:
            messages.error(request, 'Please select a shipping address')
            return redirect('shop:checkout')

        # Cash orders don't submit a payment_method field at all (the
        # template just shows a static "pay at counter" line) — only
        # require and validate one for the online branch. Payment.payment_method
        # has no 'cash' choice, only 'cash_on_delivery', so map to that.
        if payment_type == 'cash':
            payment_method = 'cash_on_delivery'
        else:
            payment_method = request.POST.get('payment_method')
            if payment_method not in ONLINE_PAYMENT_METHODS:
                messages.error(request, 'Please select a payment method')
                return redirect('shop:checkout')

        try:
            shipping_address = Address.objects.get(
                id=shipping_address_id,
                user=request.user,
                address_type__in=['shipping', 'both']
            )
        except Address.DoesNotExist:
            messages.error(request, 'Invalid shipping address selected')
            return redirect('shop:checkout')

        # Tax and shipping fee removed — total is just the cart subtotal.
        subtotal = cart.subtotal
        tax_amount = Decimal('0.00')
        shipping_cost = Decimal('0.00')
        total_amount = subtotal

        order = Order.objects.create(
            user=request.user,
            payment_type=payment_type,
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
            billing_full_name=shipping_address.full_name,
            billing_phone=shipping_address.phone_number,
            billing_address=shipping_address.street_address,
            billing_city=shipping_address.city,
            billing_state=shipping_address.state,
            billing_postal_code=shipping_address.postal_code,
            billing_country=shipping_address.country,
            notes=notes,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_sku=item.product.sku,
                quantity=item.quantity,
                unit_price=item.product.price,
                total_price=item.total_price
            )
            product = item.product
            product.stock -= item.quantity
            product.save()

        # Both cash-at-counter and online payments start pending — cash is
        # confirmed by the cashier at pickup (cashier_views.punch_order),
        # online is confirmed by confirm_online_payment() below.
        Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=total_amount,
            status='pending'
        )

        cart_items.delete()
        del request.session['checkout_payment_type']

        messages.success(request, f'Order {order.order_number} placed successfully!')

        if payment_type == 'online':
            return redirect('shop:online_payment', order_id=order.id)
        return redirect('shop:order_success', order_id=order.id)

    subtotal = cart.subtotal
    total = subtotal

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': total,
        'shipping_addresses': shipping_addresses,
        'payment_type': payment_type,
    }
    return render(request, 'shop/checkout.html', context)


@login_required
def online_payment(request, order_id):
    """
    Separate flow for online payment: order already exists (created in
    checkout()), payment is still pending. This is a placeholder screen —
    swap the "I've completed payment" button for a real GCash/Maya/PayMongo
    redirect + webhook when a live gateway is wired in.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_type='online')

    if order.payment_status == 'paid':
        return redirect('shop:order_success', order_id=order.id)

    return render(request, 'shop/online_payment.html', {'order': order})


@login_required
def confirm_online_payment(request, order_id):
    """Marks the online payment as received. Replace this body with the
    gateway's webhook/callback handling once one is integrated."""
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_type='online')

    if request.method == 'POST':
        order.payment_status = 'paid'
        order.save(update_fields=['payment_status'])

        payment = getattr(order, 'payment', None)
        if payment:
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save(update_fields=['status', 'paid_at'])

        messages.success(request, 'Payment received — show your QR code at the counter to collect your order.')
        return redirect('shop:order_success', order_id=order.id)

    return redirect('shop:online_payment', order_id=order.id)


@login_required
def order_success(request, order_id):
    """Order success page — now includes a QR code the cashier scans to
    pull the order up on the counter dashboard."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    qr_target = request.build_absolute_uri(
        reverse('shop:cashier_order_lookup', args=[order.qr_token])
    )
    context = {
        'order': order,
        'qr_code': generate_qr_code_data_uri(qr_target),
    }
    return render(request, 'shop/order_success.html', context)


# ==================== USER ACCOUNT ====================
@login_required
def my_orders(request):
    """User order history"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'orders': page_obj}
    return render(request, 'shop/my_orders.html', context)


@login_required
def order_detail(request, order_id):
    """Order detail page — shows the QR code again while the order hasn't
    been picked up yet, so the customer can re-open it at the counter."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {'order': order}

    if order.status not in ('delivered', 'cancelled', 'refunded'):
        qr_target = request.build_absolute_uri(
            reverse('shop:cashier_order_lookup', args=[order.qr_token])
        )
        context['qr_code'] = generate_qr_code_data_uri(qr_target)

    return render(request, 'shop/order_detail.html', context)


@login_required
def profile(request):
    """User profile page"""
    if request.method == 'POST':
        # Update profile
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        
        # Update or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone_number = request.POST.get('phone_number')
        profile.save()
        
        messages.success(request, 'Profile updated successfully')
        return redirect('shop:profile')
    
    context = {'user': request.user}
    return render(request, 'shop/profile.html', context)


@login_required
def manage_addresses(request):
    """Manage user addresses"""
    addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Add new address
        Address.objects.create(
            user=request.user,
            address_type=request.POST.get('address_type'),
            full_name=request.POST.get('full_name'),
            phone_number=request.POST.get('phone_number'),
            street_address=request.POST.get('street_address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country'),
            is_default=request.POST.get('is_default') == 'on'
        )
        messages.success(request, 'Address added successfully')
        return redirect('shop:manage_addresses')
    
    context = {'addresses': addresses}
    return render(request, 'shop/addresses.html', context)


@login_required
def delete_address(request, address_id):
    """Delete an address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully')
    return redirect('shop:manage_addresses')


# ==================== WISHLIST ====================
@login_required
def wishlist(request):
    """User wishlist"""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    context = {'wishlist_items': wishlist_items}
    return render(request, 'shop/wishlist.html', context)


@login_required
def add_to_wishlist(request, product_id):
    """Add product to wishlist"""
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    
    if created:
        messages.success(request, f'{product.name} added to wishlist')
    else:
        messages.info(request, f'{product.name} is already in your wishlist')
    
    return redirect(request.META.get('HTTP_REFERER', 'shop:product_list'))


@login_required
def remove_from_wishlist(request, product_id):
    """Remove product from wishlist"""
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, 'Item removed from wishlist')
    return redirect('shop:wishlist')


@login_required
def clear_wishlist(request):
    """Clear all items from wishlist"""
    if request.method == 'POST' or request.method == 'GET':
        Wishlist.objects.filter(user=request.user).delete()
        messages.success(request, 'Your wishlist has been cleared.')
    return redirect('shop:wishlist')


# ==================== SEARCH ====================
def search(request):
    """Advanced search"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(available=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'query': query,
        'total_results': products.count()
    }
    return render(request, 'shop/search_results.html', context)


# ==================== AJAX ENDPOINTS ====================
@login_required
def cart_count(request):
    """Get cart item count (AJAX)"""
    cart = get_or_create_cart(request)
    count = cart.total_items
    return JsonResponse({'count': count})


def apply_coupon(request):
    """Apply coupon code (AJAX)"""
    if request.method == 'POST':
        code = request.POST.get('code')
        cart = get_or_create_cart(request)
        
        try:
            coupon = Coupon.objects.get(code=code.upper())
            is_valid, message = coupon.is_valid()
            
            if is_valid:
                # Calculate discount
                subtotal = cart.subtotal
                
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (coupon.discount_value / 100)
                    if coupon.max_discount_amount:
                        discount = min(discount, coupon.max_discount_amount)
                else:
                    discount = coupon.discount_value
                
                # Check minimum purchase
                if subtotal < coupon.min_purchase_amount:
                    return JsonResponse({
                        'success': False,
                        'message': f'Minimum purchase of ₱{coupon.min_purchase_amount} required'
                    })
                
                return JsonResponse({
                    'success': True,
                    'message': 'Coupon applied successfully',
                    'discount': float(discount),
                    'code': coupon.code
                })
            else:
                return JsonResponse({'success': False, 'message': message})
        
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


# ==================== AUTH ====================
def register(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('shop:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # The form only submits one "full_name" field, not separate
        # first_name/last_name — split it here instead of reading
        # POST keys that don't exist (which returned None and broke
        # the NOT NULL constraint on auth_user.last_name).
        full_name = (request.POST.get('full_name') or '').strip()
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'shop/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'shop/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'shop/register.html')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create profile
        UserProfile.objects.create(user=user)

        messages.success(request, 'Account created successfully! Please login.')
        return redirect('shop:login')

    return render(request, 'shop/register.html')


@login_required
def notifications(request):
    notifications = request.user.notifications.all()[:50]
    context = {'notifications': notifications}
    return render(request, 'shop/notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    messages.success(request, 'Notification marked as read.')
    return redirect('shop:notifications')


@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('shop:notifications')


def custom_logout(request):
    """Custom logout view"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('shop:home')