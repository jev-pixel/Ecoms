# D:\Ecom\shop\views_api.py
# New views that use FastAPI backend instead of Django models

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .api_service import ECommerceAPI

# API-powered home page
def api_home(request):
    """Home page showing products from API"""
    items = ECommerceAPI.get_all_items()
    
    # Check if API is accessible
    if not items and not ECommerceAPI.check_api_health():
        messages.error(request, "⚠️ Backend API is not running. Please start FastAPI on port 8000.")
    
    context = {
        'products': items[:6] if items else [],
        'api_status': 'connected' if items else 'disconnected'
    }
    return render(request, 'shop/api_home.html', context)

# API-powered product list
def api_product_list(request, category=None):
    """Display all products from API"""
    items = ECommerceAPI.get_all_items()
    
    # Filter by category if specified
    if category:
        items = [item for item in items if item.get('category') == category]
    
    context = {
        'products': items,
        'category': category,
    }
    return render(request, 'shop/api_product_list.html', context)

# API-powered product detail
def api_product_detail(request, product_id):
    """Show product details from API"""
    item = ECommerceAPI.get_item_by_id(product_id)
    
    if not item:
        messages.error(request, f'Product {product_id} not found')
        return redirect('shop:api_home')
    
    context = {
        'product': item
    }
    return render(request, 'shop/api_product_detail.html', context)

# Add to cart (session-based)
@login_required(login_url='shop:login')
def api_add_to_cart(request, product_id):
    """Add product to cart (stored in session)"""
    # Verify product exists in API
    item = ECommerceAPI.get_item_by_id(product_id)
    
    if not item:
        messages.error(request, 'Product not found')
        return redirect('shop:api_home')
    
    # Get cart from session
    cart = request.session.get('api_cart', {})
    
    # Add or increment quantity
    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'quantity': 1,
            'name': item['name'],
            'price': item['price']
        }
    
    request.session['api_cart'] = cart
    request.session.modified = True
    
    messages.success(request, f"✅ {item['name']} added to cart!")
    return redirect('shop:api_view_cart')

# View cart
@login_required(login_url='shop:login')
def api_view_cart(request):
    """Display cart contents"""
    cart = request.session.get('api_cart', {})
    cart_items = []
    total_price = Decimal('0.0')
    
    for product_id, item_data in cart.items():
        # Fetch fresh product data from API
        product = ECommerceAPI.get_item_by_id(int(product_id))
        
        if product:
            quantity = int(item_data.get('quantity', 1))
            subtotal = Decimal(str(product['price'])) * quantity
            total_price += subtotal
            
            cart_items.append({
                'product_id': product_id,
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal,
            })
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'shop/api_cart.html', context)

# Update cart quantity
@login_required(login_url='shop:login')
def api_update_cart(request, product_id):
    """Update quantity in cart"""
    if request.method == 'POST':
        cart = request.session.get('api_cart', {})
        
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity < 1:
                quantity = 1
        except ValueError:
            quantity = 1
        
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] = quantity
            request.session['api_cart'] = cart
            request.session.modified = True
            messages.success(request, 'Cart updated!')
    
    return redirect('shop:api_view_cart')

# Remove from cart
@login_required(login_url='shop:login')
def api_remove_from_cart(request, product_id):
    """Remove item from cart"""
    cart = request.session.get('api_cart', {})
    
    if str(product_id) in cart:
        product_name = cart[str(product_id)].get('name', 'Item')
        del cart[str(product_id)]
        request.session['api_cart'] = cart
        request.session.modified = True
        messages.success(request, f'❌ {product_name} removed from cart')
    
    return redirect('shop:api_view_cart')

# Checkout - Create order via API
@login_required(login_url='shop:login')
def api_checkout(request):
    """Process checkout and create order via API"""
    cart = request.session.get('api_cart', {})
    
    if not cart:
        messages.info(request, '🛒 Your cart is empty')
        return redirect('shop:api_product_list')
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name') or request.user.get_full_name() or request.user.username
        customer_email = request.POST.get('customer_email') or request.user.email
        
        # Prepare order items for API
        order_items = []
        for product_id, item_data in cart.items():
            order_items.append({
                'item_id': int(product_id),
                'quantity': item_data['quantity']
            })
        
        # Create order via API
        result = ECommerceAPI.create_order(customer_name, customer_email, order_items)
        
        if result:
            # Clear cart
            request.session['api_cart'] = {}
            request.session.modified = True
            
            messages.success(request, f'🎉 Order #{result["id"]} placed successfully!')
            return redirect('shop:api_order_success', order_id=result['id'])
        else:
            messages.error(request, '❌ Failed to create order. Please try again.')
            return redirect('shop:api_view_cart')
    
    # GET request - show checkout form
    cart_items = []
    total_price = Decimal('0.0')
    
    for product_id, item_data in cart.items():
        product = ECommerceAPI.get_item_by_id(int(product_id))
        if product:
            quantity = item_data['quantity']
            subtotal = Decimal(str(product['price'])) * quantity
            total_price += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'customer_name': request.user.get_full_name() or request.user.username,
        'customer_email': request.user.email,
    }
    return render(request, 'shop/api_checkout.html', context)

# Order success page
@login_required(login_url='shop:login')
def api_order_success(request, order_id):
    """Display order confirmation"""
    order = ECommerceAPI.get_order_by_id(order_id)
    
    context = {
        'order': order,
        'order_id': order_id
    }
    return render(request, 'shop/api_order_success.html', context)

# View all transactions/orders
@login_required(login_url='shop:login')
def api_transactions(request):
    """Display all orders/transactions"""
    status = request.GET.get('status', None)
    transactions = ECommerceAPI.get_all_transactions(status=status)
    
    context = {
        'transactions': transactions,
        'current_status': status,
    }
    return render(request, 'shop/api_transactions.html', context)

# Admin: Update order status
@login_required(login_url='shop:login')
def api_update_order_status(request, order_id):
    """Update order status (admin function)"""
    if request.method == 'POST':
        new_status = request.POST.get('status')
        result = ECommerceAPI.update_order(order_id, status=new_status)
        
        if result:
            messages.success(request, f'✅ Order #{order_id} updated to {new_status}')
        else:
            messages.error(request, f'❌ Failed to update order #{order_id}')
    
    return redirect('shop:api_transactions')

# Admin: Delete order
@login_required(login_url='shop:login')
def api_delete_order(request, order_id):
    """Delete an order (admin function)"""
    if request.method == 'POST':
        result = ECommerceAPI.delete_order(order_id)
        
        if result:
            messages.success(request, f'✅ Order #{order_id} deleted successfully')
        else:
            messages.error(request, f'❌ Failed to delete order #{order_id}')
    
    return redirect('shop:api_transactions')