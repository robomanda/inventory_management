from django.contrib import admin
from .models import InventoryItem, Category, CustomerData, OwnerData, CustInvoiceData

admin.site.register(InventoryItem)
admin.site.register(Category)
admin.site.register(CustomerData)
admin.site.register(OwnerData)
admin.site.register(CustInvoiceData)
