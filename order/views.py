from django.shortcuts import render,redirect
from carts.models import CartItem
from .models import Order
from .forms import OrderForm
import datetime

# Create your views here.

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
    
    if request.method == 'POST':
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

            order = Order.objects.get(user = current_user,is_ordered = False)
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
        
     
   
            



