from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Category, InventoryItem, CustomerData, SupplierData, OwnerData, CustInvoiceData

class UserRegisterForm(UserCreationForm):
	email = forms.EmailField()

	class Meta:
		model = User
		fields = ['username', 'email', 'password1', 'password2']

class InventoryItemForm(forms.ModelForm):
	category = forms.ModelChoiceField(queryset=Category.objects.all(), initial=0)
	supply = forms.ModelChoiceField(queryset=SupplierData.objects.all(), initial=0)
	class Meta:
		model = InventoryItem
		fields = ['imi','name', 'quantity', 'price', 'category', 'supply']

class CustomerDataForm(forms.ModelForm):
  	class Meta:
  		model = CustomerData
  		fields = ['cname','cnie','cphone', 'caddress']

class SupplierDataForm(forms.ModelForm):
  	class Meta:
  		model = SupplierData
  		fields = ['sname','sphone', 'saddress']

class OwnerDataForm(forms.ModelForm):
  	class Meta:
  		model = OwnerData
  		fields = ['firma', 'fphone', 'whtsapp', 'cif', 'domainn', 'faddress']

class InvoicedataForm(forms.ModelForm):
	class Meta:
		model = CustInvoiceData
		fields = ['customer',  'nif', 'address']