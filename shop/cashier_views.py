# shop/cashier_views.py - Cashier Dashboard
"""
Staff-only views for the counter. A customer's order_success/order_detail
page shows them a QR code; a cashier scans (or types) it here to confirm
payment and move the order through prep -> served.

Access control: cashier_required just needs request.user.is_staff, same
as staff_member_required, but redirects to the storefront's own login
page (shop:login) instead of /admin/login/. Give a counter account staff
status from /admin/ (Users -> is_staff) — no need for a full superuser.
"""
import uuid
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Order

ACTIVE_STATUSES_EXCLUDED = ['delivered', 'cancelled', 'refunded']


def cashier_required(view_func):
    @login_required(login_url='shop:login')
    @user_passes_test(lambda u: u.is_staff, login_url='shop:login')
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapped


@cashier_required
def dashboard(request):
    """The queue: every order that still needs counter attention."""
    status_filter = request.GET.get('status', 'active')
    orders = Order.objects.select_related('user').prefetch_related('items')

    if status_filter == 'active':
        orders = orders.exclude(status__in=ACTIVE_STATUSES_EXCLUDED)
    else:
        orders = orders.filter(status=status_filter)

    orders = orders.order_by('created_at')

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'cash_pending_count': Order.objects.filter(
            payment_type='cash', payment_status='pending'
        ).exclude(status__in=ACTIVE_STATUSES_EXCLUDED).count(),
        'online_ready_count': Order.objects.filter(
            payment_type='online', payment_status='paid', status='pending'
        ).count(),
    }
    return render(request, 'shop/cashier_dashboard.html', context)


@cashier_required
def scan(request):
    """Camera QR scanner page, with a manual code/order-number fallback.

    `code` can be a bare order_number, a bare qr_token, or the full QR
    URL (…/cashier/order/<token>/) if a scanner hands back the raw
    decoded text instead of just the token — order_lookup below strips
    that down to the token itself before it ever reaches here in the
    camera flow, but the manual textbox can still contain either form,
    so both are handled.
    """
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().rstrip('/')
        # A pasted full URL -> just the last path segment.
        if '/' in code:
            code = code.rsplit('/', 1)[-1]

        order = Order.objects.filter(order_number__iexact=code).first()
        if not order:
            try:
                order = Order.objects.filter(qr_token=uuid.UUID(code)).first()
            except (ValueError, AttributeError):
                order = None

        if not order:
            messages.error(request, f'No order found for "{code}"')
            return redirect('shop:cashier_scan')
        return redirect('shop:cashier_order_lookup', qr_token=order.qr_token)

    return render(request, 'shop/cashier_scan.html')


@cashier_required
def order_lookup(request, qr_token):
    """What the cashier sees after scanning — order contents + a punch button."""
    order = get_object_or_404(Order.objects.prefetch_related('items'), qr_token=qr_token)
    return render(request, 'shop/cashier_order_detail.html', {'order': order})


@cashier_required
def punch_order(request, qr_token):
    """
    Advance the order one step and stamp who did it.

    Cash orders: first punch also collects payment (payment_status -> paid).
    Online orders are already paid by the time they reach the counter, so
    the cashier is just confirming / progressing the kitchen queue.
    """
    order = get_object_or_404(Order, qr_token=qr_token)

    if request.method == 'POST':
        if request.POST.get('action') == 'confirm_cash':
            order.payment_status = 'paid'
            payment = getattr(order, 'payment', None)
            if payment:
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.save(update_fields=['status', 'paid_at'])

        if order.status == 'pending':
            order.status = 'confirmed'
            order.confirmed_at = timezone.now()
            order.confirmed_by = request.user
        elif order.status == 'confirmed':
            order.status = 'processing'
        elif order.status == 'processing':
            order.status = 'delivered'  # served / picked up at the counter

        order.save()
        messages.success(
            request,
            f'Order {order.order_number} updated to "{order.get_status_display()}"'
        )

    return redirect('shop:cashier_order_lookup', qr_token=order.qr_token)
