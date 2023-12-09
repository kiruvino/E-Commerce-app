from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from . models  import Product, ReviewRating
from django.db import connection
from category.models import Category
from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from .forms import ReviewForm
from django.contrib import messages
from order.models import OrderProduct

# Create your views here.
def store(request,category_url=None):
    categories = None
    products = None
    
    if category_url!= None:
        categories = get_object_or_404(Category,url = category_url)
        products =   Product.objects.all().filter(category = categories,is_available=True)
        paginator = Paginator(products,3)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)
    else:
        products = Product.objects.all().filter(is_available=True)
        paginator = Paginator(products,3)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
            'products':paged_products,
            'product_count':product_count
        }
    return render(request,'store.html',context)
     

def product_detail(request,category_url,product_url):
    try:
        single_product = Product.objects.get(category__url=category_url,slug=product_url)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request),is_active=True,product=single_product).exists()
    except Exception as e:
        raise e
    
    order_product = OrderProduct.objects.filter(user__id=request.user.id, product_id=single_product.id).last()
    context={
        'single_product':single_product,
        'in_cart':in_cart,
        'order_product':order_product
    }

    
    return render(request,'product-detail.html',context)
    
def search(request):
    context = {}
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
            context={
            'products':products,
            'product_count':product_count
            }
                
        return render(request,'store.html',context)

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id = request.user.id,product__id = product_id)
            form = ReviewForm(request.POST,instance=reviews)
            form.save()
            messages.success(request,"Thank you! your review has been submitted")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request,"Thank you! your review has been Created")
                return redirect(url)
                