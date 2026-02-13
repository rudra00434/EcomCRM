from django.contrib import admin
from .models import Customer,Tag,Product,order
admin.site.register(Customer)
admin.site.register(Tag)
admin.site.register(Product)
admin.site.register(order)
# Register your models here.
