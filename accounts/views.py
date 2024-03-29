from email.message import EmailMessage
from django.http import HttpResponse 
from django.shortcuts import render, redirect , get_object_or_404

from django.conf import settings
from .forms import RegistrationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages , auth
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from carts.views import _cart_id
from carts.models import Cart, CartItem
from order.models import Order, OrderProduct
from django.contrib.auth.decorators import login_required


def register(request):
   
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        print(request.POST['email'],form.is_valid())
        if form.is_valid():
            
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            #create a user profile
            profile = UserProfile()
            profile.user_id = user.id
            profile.profile_picture = 'default/default-user.png'
            profile.save()
            #logic for sending email to verify email address
            current_site  = get_current_site(request)
            print(current_site)
            mail_subject = "DAKart - Please activate your account"
            email_from = settings.EMAIL_HOST_USER
            message = render_to_string('accounts/account_verification_email.html',{
                 'user':user,                         
                 'domain':current_site,
                 'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                 'token':default_token_generator.make_token(user)
            })
            to_email = [email,]
            send_mail(mail_subject,message,email_from,to_email)
            return redirect('/accounts/login?command=verification&email='+email)
    
    form = RegistrationForm()
    context = {
                'form': form,
             }
    return render(request, 'accounts/register.html', context)
             
            
    

def login(request):
    if request.method == 'POST':
        entered_email = request.POST["email"]
        entered_password = request.POST["password"]
        
        user =  auth.authenticate(email=entered_email, password = entered_password)
        
       
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart,is_active=True)
                    

                    # Getting the product variations by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variation.all()
                        product_variation.append(list(variation))

                    # Get the cart items from the user to access his product variations
                    
                        
                    
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variation.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    # product_variation = [1, 2, 3, 4, 6]
                    # ex_var_list = [4, 6, 3, 5]

                    for pr in product_variation:
                        
                        if pr in ex_var_list:
                            
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            if item.is_active == 0:
                                item.is_active = 1 
                            item.user = user
                            item.save()
                        else:
                            
                            cart_item = CartItem.objects.filter(cart=cart,is_active=True)
                            for item in cart_item:
                                if item.is_active == 0:
                                    item.is_active = 1
                                item.user = user
                                item.save()
            except:
                pass

            auth.login(request,user)
            return redirect('welcome')
        else:
                messages.error(request,"Invalid Login Credentials")
                return redirect('login')
    
    return render(request, 'accounts/login.html')

def logout(request):
     auth.logout(request)
     messages.success(request,'You have logged out')
     return redirect('login')
     
def activate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError , OverflowError, Account.DoesNotExist):
         user = None
    
    if user is not None and default_token_generator.check_token(user,token):
         user.is_active = True
         user.save()
         messages.success(request,"Your account is activated!")
         return redirect('login')
    else:
         messages.error(request,"Invalid activation link")
         return redirect('register')


def dashboard(request):
     orders = Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
     orders_count = orders.count()
     
     userprofile = UserProfile.objects.get(user_id=request.user.id)
     
     context = {
        'orders_count':orders_count,
        'userprofile':userprofile
     }
     return render(request,'accounts/dashboard.html',context)

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request,'accounts/my_orders.html', context)

@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }
    return render(request, 'order_detail.html', context)

@login_required(login_url='login')
def edit_profile(request):
    user_profile = None
    try:
        user_profile = UserProfile.objects.get(user_id=request.user.id)
    except:
        pass

    if request.method == "POST":
        user_form = UserForm(request.POST,instance=request.user)
        user_profile_form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid() and user_profile_form.is_valid():
            user_form.save()
            user_profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('edit_profile')
    else:
         user_form = UserForm(instance=request.user)
         profile_form = UserProfileForm(instance=user_profile)
    context ={
             'user_form': user_form,
             'profile_form':profile_form,
             'user_profile':user_profile
         }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        user =   Account.objects.get(username__iexact=request.user.username)
        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                auth.logout(request)
                
            else:
                messages.error(request, "please enter valid current password")
                
        else:
            messages.error(request, "password does not match")
            


    return render(request, 'accounts/change_password.html')




