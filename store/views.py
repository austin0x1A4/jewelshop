import django
from django.contrib.auth.models import User
from store.models import Address, Cart, Category, Order, Product
from django.shortcuts import redirect, render, get_object_or_404
from .forms import RegistrationForm, AddressForm
from django.contrib import messages
from django.views import View
import decimal
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse  # Added import
import json
import os
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q
from decimal import Decimal
from .utils import get_amazon_pay_client
# Create your views here.

def home(request):
    categories = Category.objects.filter(is_active=True, is_featured=True)[:3]
    products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    context = {
        'categories': categories,
        'products': products,
    }
    return render(request, 'store/index.html', context)

def detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.exclude(id=product.id).filter(is_active=True, category=product.category)
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/detail.html', context)

def all_categories(request):
    categories = Category.objects.filter(is_active=True)
    return render(request, 'store/categories.html', {'categories':categories})

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(is_active=True, category=category)
    categories = Category.objects.filter(is_active=True)
    context = {
        'category': category,
        'products': products,
        'categories': categories,
    }
    return render(request, 'store/category_products.html', context)

# Authentication Starts Here

class RegistrationView(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'account/register.html', {'form': form})
    
    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, "Congratulations! Registration Successful!")
            form.save()
        return render(request, 'account/register.html', {'form': form})
        
@login_required
def profile(request):
    addresses = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user)
    return render(request, 'account/profile.html', {'addresses':addresses, 'orders':orders})

@method_decorator(login_required, name='dispatch')
class AddressView(View):
    def get(self, request):
        form = AddressForm()
        return render(request, 'account/add_address.html', {'form': form})

    def post(self, request):
        form = AddressForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            user = request.user

            # Check if an address with the same data already exists
            existing_address = Address.objects.filter(
                Q(user=user),
                **{field: cleaned_data[field] for field in cleaned_data}
            ).first()

            if existing_address:
                messages.warning(request, "An address with the same details already exists.")
                return JsonResponse({'success': False, 'message': 'Address already exists.'})
            else:
                try:
                    address = Address(user=user, **cleaned_data)
                    address.save()
                    messages.success(request, "New Address Added Successfully.")
                    
                except IntegrityError:
                    messages.error(request, "An error occurred while saving the address. Please try again.")
                    return JsonResponse({'success': False, 'message': 'Integrity error.'})
                except Exception as e:
                    messages.error(request, f"An unexpected error occurred: {str(e)}")
                    return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
        else:
            error_message = ""
            for field, errors in form.errors.items():
                for error in errors:
                    error_message += f"{field.title()}: {error} "
            return JsonResponse({'success': False, 'message': error_message})

        return redirect('store:profile')
def remove_address(request, id):
    a = get_object_or_404(Address, user=request.user, id=id)
    a.delete()
    messages.success(request, "Address removed.")
    return redirect('store:profile')

@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    product = get_object_or_404(Product, id=product_id)

    # Check whether the Product is alread in Cart or Not
    cart_item, created = Cart.objects.get_or_create(product=product, user=user)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    
    return redirect('store:cart')

@login_required
def cart(request):
    user = request.user
    cart_products = Cart.objects.filter(user=user)
    combined_data = []
    amount = decimal.Decimal(0)
    shipping_amount = decimal.Decimal(10)

    for cart_product in cart_products:
        temp_amount = (cart_product.quantity * cart_product.product.price)
        amount += temp_amount
        combined_data.append((cart_product, temp_amount))

    addresses = Address.objects.filter(user=user)
    selected_address_id = request.POST.get('address')

    if selected_address_id:
        try:
            selected_address = Address.objects.get(id=selected_address_id, user=user)
        except Address.DoesNotExist:
            selected_address = None
    else:
        selected_address = None

    form = AddressForm()  # Create a form instance to pass to the template

    context = {
        'combined_data': combined_data,
        'amount': amount,
        'shipping_amount': shipping_amount,
        'total_amount': amount + shipping_amount,
        'addresses': addresses,
        'selected_address': selected_address,
        'form': form  # Include the form in the context
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = user
            address.save()
            addresses = Address.objects.filter(user=user)  # Refresh addresses
            return JsonResponse({
                'success': True,
                'address': {
                    'id': address.id,
                    'address_line1': address.address_line1,
                    'city': address.city
                },
                'addresses': list(addresses.values('id', 'address_line1', 'city'))
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'errors': errors})

    return render(request, 'store/cart.html', context)

@login_required
def remove_cart(request, cart_id):
    if request.method == 'GET':
        c = get_object_or_404(Cart, id=cart_id)
        c.delete()
        messages.success(request, "Product removed from Cart.")
    return redirect('store:cart')

@login_required
def plus_cart(request, cart_id):
    if request.method == 'GET':
        cp = get_object_or_404(Cart, id=cart_id)
        cp.quantity += 1
        cp.save()
    return redirect('store:cart')

@login_required
def minus_cart(request, cart_id):
    if request.method == 'GET':
        cp = get_object_or_404(Cart, id=cart_id)
        if cp.quantity == 1:
            cp.delete()
        else:
            cp.quantity -= 1
            cp.save()
    return redirect('store:cart')
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def checkout(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)

    combined_data = [(item, item.product.price * item.quantity) for item in cart_items]
    amount = sum(item[1] for item in combined_data)
    shipping_amount = Decimal('10.00')
    total_amount = amount + shipping_amount
    address_id = request.GET.get('address_id')
    address = Address.objects.filter(id=address_id, user=user).first()

    if not address:
        messages.error(request, 'No address selected or entered. Please return to cart and select an address.')
        return redirect('store:cart')

    # Create a Stripe PaymentIntent
    intent = stripe.PaymentIntent.create(
        amount=int(total_amount * 100),  # Stripe uses cents
        currency='usd',
        metadata={'user_id': user.id},
    )

    context = {
        'cart_items': cart_items,
        'total_price': total_amount,
        'address': address,
        'client_secret': intent.client_secret,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'combined_data': combined_data,
        'amount': amount,
        'shipping_amount': shipping_amount,
    }
    return render(request, 'store/checkout.html', context)
@login_required
def orders(request):
    all_orders = Order.objects.filter(user=request.user).order_by('-ordered_date')
    return render(request, 'store/orders.html', {'orders': all_orders})

def shop(request):
    return render(request, 'store/shop.html')

def test(request):
    return render(request, 'store/test.html')
# views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import stripe
from .utils import calculate_total_price

@csrf_exempt
@login_required
def process_payment(request):
    if request.method == 'POST':
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        address_id = request.POST.get('address_id')
        address = get_object_or_404(Address, id=address_id)

        # Create orders for each item in the cart
        for cart_item in cart_items:
            Order.objects.create(
                user=user,
                address=address,
                product=cart_item.product,
                quantity=cart_item.quantity
            )
            cart_item.delete()

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def payment_success(request):
    return render(request, 'store/payment_success.html')

@login_required
def payment_failure(request):
    return render(request, 'store/payment_failure.html')
    