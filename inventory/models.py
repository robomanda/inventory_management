from djmoney.models.fields import MoneyField
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum


class InventoryItem(models.Model):
	imi = models.CharField(max_length=20, unique=True)
	name = models.CharField(max_length=50)
	quantity = models.PositiveIntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2)
	cost = models.DecimalField(max_digits=10, decimal_places=2)
	supply = models.ForeignKey('SupplierData', max_length=15, on_delete=models.SET_NULL, blank=True, null=True)
	category = models.ForeignKey('Category', max_length=15, on_delete=models.SET_NULL, blank=True, null=True)
	datecrea = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)

	def calculate_price(self):
		owner_data = OwnerData.objects.filter(user=self.user).first()
		if owner_data:
			margin_multiplier = 1 + (owner_data.margin / 100)
			return round(self.cost * margin_multiplier, 2)
		return self.cost  # Default to cost if no margin is set
	
	def save(self, *args, **kwargs):
		self.price = self.calculate_price()
		super().save(*args, **kwargs)
		
	def __str__(self):
		return self.name

class CustomerData(models.Model):
	cname = models.CharField(max_length=50)
	cnie = models.CharField(max_length=20)
	cphone = models.IntegerField()
	caddress = models.CharField (max_length=50)
	datec = models.DateTimeField(auto_now_add=True) 
	user = models.ForeignKey(User, on_delete=models.CASCADE)
		
	def __str__(self):
		return self.cname


class Category(models.Model):
	 name = models.CharField(max_length=100)

	 class Meta:
			verbose_name_plural = 'categories'

	 def __str__(self):
	 	return self.name

class SupplierData(models.Model):
	sname = models.CharField(max_length=15)
	sphone = models.IntegerField()
	saddress = models.CharField (max_length=50)
	datecl = models.DateTimeField(auto_now_add=True) 
	user = models.ForeignKey(User, on_delete=models.CASCADE)
		
	def __str__(self):
		return self.sname

class OwnerData(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	firma = models.CharField(max_length=50)
	fphone = models.IntegerField()
	whtsapp = models.IntegerField()
	cif = models.CharField(max_length=35, default=0)
	margin = models.DecimalField(max_digits=5, decimal_places=2)
	iva = models.DecimalField(max_digits=5, decimal_places=2)
	domainn = models.CharField(max_length=50)
	faddress = models.CharField (max_length=50)
	#logo = models.ImageField(upload_to='logos/', null=True, blank=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
		
	def __str__(self):
		return f"{self.user.username} - Margin: {self.margin}%"

class CustInvoiceData(models.Model):
	customer = models.ForeignKey(CustomerData, on_delete=models.CASCADE)
	phone = models.IntegerField()
	nif = models.CharField(max_length=35, default=0)
	address = models.CharField (max_length=50)
	total_before_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Invoice total before tax
	total_after_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)   # Invoice total after tax
	datein = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

	def calculate_invoice_totals(self):
		total_before_iva = sum(item.total for item in self.items.all())  # Sum of all invoice items
		#total_before_iva = sum(item.total_price for item in self.detailsdata_set.all())  # Sum of all invoice items
		owner_data = OwnerData.objects.filter(user=self.user).first()
		iva_percentage = owner_data.iva if owner_data else 0.0  # Fetch IVA from OwnerData

		total_after_iva = round(total_before_iva * (1 + iva_percentage / 100), 2)
		self.total_before_iva = total_before_iva
		self.total_after_iva = total_after_iva
		self.save()
		
	def __str__(self):
		return f"Invoice #{self.id} for {self.customer.cname} - Total Before IVA: {self.total_before_iva}, Total After IVA: {self.total_after_iva}"
		#return f"Invoice #{self.id} for {self.customer.cname}"  # FIXED


class InvoiceDetail(models.Model):
    invoice = models.ForeignKey('CustInvoiceData', on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=25)
    imi = models.CharField(max_length=20)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.quantity} x {self.price})"

    def total_sales(self):
        """Sum up the total price from related InvoiceDetail records."""
        return self.items.aggregate(grand_total=Sum('total'))['total'] or 0  # Ensures it returns 0 if no data

    def reduce_inventory(self):
        """Reduce the inventory quantity after an invoice is saved."""
        try:
            inventory_item = InventoryItem.objects.get(imi=self.imi)  # Find the inventory item by IMI
            # Ensure self.quantity is an integer before comparison
            quantity_to_reduce = int(self.quantity)  # Convert to integer if it's a string
            if inventory_item.quantity >= quantity_to_reduce:  # Check if there's enough stock
                inventory_item.quantity -= quantity_to_reduce  # Reduce the stock
                inventory_item.save()  # Save the updated inventory item
            else:
                raise ValueError(f"Not enough stock for {inventory_item.name}. Only {inventory_item.quantity} left.")
        except InventoryItem.DoesNotExist:
            raise ValueError(f"Inventory item with IMI {self.imi} does not exist.")
        except ValueError as e:
            raise e  # Raise the error message if stock is insufficient or item doesn't exist

