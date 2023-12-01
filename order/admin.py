from django.contrib import admin
from .models import Order,payment

# Register your models here.
admin.site.register(Order)
admin.site.register(payment)