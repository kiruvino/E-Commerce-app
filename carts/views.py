import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from store.models import Product, Variation
from carts.models import Cart, CartItem
from django.contrib.auth.decorators import login_required

# Create your views here.

def _cart_id(request):
    cart_session_key = request.session.session_key
    if not cart_session_key:
        cart_session_key = request.session.create()
    return cart_session_key
    

def add_cart(request,product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id) #get the product
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]

                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass


        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variation.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                # increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                if item.is_active == 0:
                    item.is_active = 1 
                item.save()
    else:
        product_variation = []
        if request.method == 'POST':
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variation= Variation.objects.get(product=product,variation_category=key,variation_value=value)
                    product_variation.append(variation)
                except:
                    pass
        
        try:
            cart = Cart.objects.get(cart_id =_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        is_cart_item_exist = CartItem.objects.filter(product=product,cart=cart).exists()
        if is_cart_item_exist:
            cart_item = CartItem.objects.filter(product = product, cart = cart)
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variations = item.variation.all()
                ex_var_list.append(list(existing_variations))
                id.append(item.id)
            if product_variation in ex_var_list:
                #increase the quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product,id=item_id)
                item.quantity +=1
                if item.is_active == 0:
                    item.is_active = 1 
                item.save()
            else:
                cart_item = CartItem.objects.create(product=product,quantity=1,cart=cart)
                if len(product_variation)>0:
                    cart_item.variation.clear()
                    cart_item.variation.add(*product_variation)
                if cart_item.is_active == 0:
                    cart_item.is_active = 1 
                cart_item.save()
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                cart = cart
            )
            if len(product_variation)>0:
                cart_item.variation.clear()
                cart_item.variation.add(*product_variation)
            cart_item.save()
        

    return redirect('cart')

def decrement_cartItem(request,product_id,cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

    if cart_item.quantity >1:
        cart_item.quantity -= 1
        
        cart_item.save()
    else:
        cart_item.is_active=0
        cart_item.quantity = 0
        cart_item.save()

    return redirect('cart')

def remove_cart_item(request,product_id,cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

    cart_item.is_active = 0
    cart_item.quantity = 0
    cart_item.save()

    return redirect('cart')

   
    
def cart(request, total =0 , quantity = 1, cart_items=None):
    try:
        tax = None
        grand_total = None
        if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart,is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity )
            
        tax = (2 * total)/100
        grand_total = total + tax

    except:
        pass #just ignore
    
    context = {
        'cartItems':cart_items,
        'total':total,
        'tax':tax,
        'grand_total':grand_total
    }
    return render(request,'cart.html',context)

@login_required(login_url='login')
def checkout(request, total =0 , quantity = 1, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart,is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity )
    except:
        pass
    
    context = {
        'cartItems':cart_items
    }
    return render(request,'checkout.html',context)


