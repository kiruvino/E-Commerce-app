

from django.urls import path

from . import views 

urlpatterns = [
    
    path('',views.cart,name='cart'),
    path('add_cart/<int:product_id>/',views.add_cart,name='addcart'),
    path('dec_cart/<int:product_id>/<int:cart_item_id>',views.decrement_cartItem,name='decrement_cart_item'),
    path('remove_cart_item/<int:product_id>/<int:cart_item_id>',views.remove_cart_item,name="remove_cart_item"),
    path('checkout/',views.checkout,name="checkout")
] 
