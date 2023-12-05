
import json
from django.http import HttpResponse
from django.shortcuts import render,redirect
from carts.models import CartItem
from .models import Order,payment,OrderProduct
from .forms import OrderForm
import datetime
from django.core.exceptions import MultipleObjectsReturned


# Create your views here.
def payments(request):
    body = json.loads(request.body)

    order = Order.objects.all().filter(user=request.user,is_ordered=False).last()

    paymentobject = payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status']
    )

    paymentobject.save()

    order.payment = paymentobject
    order.is_ordered = True
    order.save()

    #Move the cart items to Order product table

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id 
        orderproduct.payment = order.paymentobject 
        orderproduct.user_id = request.user
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity   
        orderproduct.product_price = item.product.price 
        orderproduct.ordered = True
        orderproduct.save()

        




def place_order(request):
    current_user = request.user
    tax = 0
    grand_total = 0
    total = 0
    data = Order
    
    cart_items = CartItem.objects.filter(user=current_user,is_active=True)
    cart_count = cart_items.count()
    if cart_count <=0:
        redirect('store')
    
    for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity )
            
    tax = (2 * total)/100
    grand_total = total + tax
    print(request.method)
    if request.method == 'POST':
        try:
            form = OrderForm(request.POST)
            
            if form.is_valid():
                data = Order()
                data.user = current_user
                data.first_name = form.cleaned_data['first_name']
                data.last_name = form.cleaned_data['last_name']
                data.email = form.cleaned_data['email']
                data.phone = form.cleaned_data['phone']
                data.address_line_1 = form.cleaned_data['address_line_1']
                data.address_line_2 = form.cleaned_data['address_line_2']
                data.city = form.cleaned_data['city']
                data.state = form.cleaned_data['state']
                data.country = form.cleaned_data['country']
                data.order_note = form.cleaned_data['order_note']
                data.order_total = grand_total
                data.tax = tax
                data.ip = request.META.get('REMOTE_ADDR')
                data.save()

                #order number generation
                yr = int(datetime.date.today().strftime('%Y'))
                dt = int(datetime.date.today().strftime('%d'))
                mt = int(datetime.date.today().strftime('%m'))

                d = datetime.date(yr,mt,dt)
                current_date = d.strftime('%Y%m%d')
                data.order_number = current_date + str(data.id)
                data.save()
                
                order = Order.objects.all().filter(user = current_user,is_ordered = False).last()
                
                context = {
                    'order':order,
                    'cart_items':cart_items,
                    'total':total,
                    'tax':tax,
                    'grand_total':grand_total
                }

                return render(request,'payments.html',context)
            else:
             return redirect('checkout')
        except MultipleObjectsReturned:
            pass