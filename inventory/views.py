
from reportlab.lib import colors
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib.auth.views import LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from .forms import UserRegisterForm, InventoryItemForm, CustomerDataForm, SupplierDataForm, OwnerDataForm, InvoicedataForm
from .models import InventoryItem, Category, CustomerData, SupplierData, OwnerData, CustInvoiceData, InvoiceDetail
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
from urllib.parse import unquote 
from django.http import JsonResponse
import os
import json
import pdfkit
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils.dateparse import parse_date
from django.db.models import Sum
from django.db import transaction
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet



date_formats = ["%Y-%m-%d", "%b. %d, %Y"]  # Example: '2025-02-08' and 'Feb. 8, 2025'

def parse_dates(date_str):
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None



class Index(TemplateView):
	template_name = 'inventory/index.html'

class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        items = InventoryItem.objects.filter(user=self.request.user.id).order_by('id')
        query = request.GET.get("imi", "")
        query = unquote(query).strip()
        low_inventory = InventoryItem.objects.filter(
            user=self.request.user.id,
            quantity__lte=LOW_QUANTITY
        )

        if low_inventory.count() > 0:
            if low_inventory.count() > 0:
                messages.error(request, f'{low_inventory.count()} items sold')
            else:
                messages.error(request, f'{low_inventory.count()} item has low inventory')
        if query:
            items = InventoryItem.objects.filter(imi__icontains=query)
        else:
            items = InventoryItem.objects.filter(user=self.request.user.id).order_by("id")

        low_inventory_ids = InventoryItem.objects.filter(
            user=self.request.user.id,
            quantity__lte=LOW_QUANTITY
        ).values_list('id', flat=True)

        return render(request, 'inventory/dashboard.html', {'items': items, 'low_inventory_ids': low_inventory_ids})


class SignUpView(View):
	def get(self, request):
		form = UserRegisterForm()
		return render(request, 'inventory/signup.html', {'form': form})

	def post(self, request):
		form = UserRegisterForm(request.POST)

		if form.is_valid():
			form.save()
			user = authenticate(
				username=form.cleaned_data['username'],
				password=form.cleaned_data['password1']
			)

			login(request, user)
			return redirect('index')

		return render(request, 'inventory/signup.html', {'form': form})

class AddItem(LoginRequiredMixin, CreateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('dashboard')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['categories'] = Category.objects.all()
		return context

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['SupplierData'] = SupplierData.objects.all()
		return context

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)


class EditItem(LoginRequiredMixin, UpdateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('dashboard')

class DeleteItem(LoginRequiredMixin, DeleteView):
	model = InventoryItem
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('dashboard')
	context_object_name = 'item'

class CustomerAd(LoginRequiredMixin, CreateView):
	model = CustomerData
	form_class = CustomerDataForm
	template_name = 'inventory/customeradd.html'
	success_url = reverse_lazy('dashboard2')

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

def custom_logout(request):
    logout(request)  # Logs out user
    return redirect('login')  # Redirect to login page


class Dashboard2(LoginRequiredMixin, View):
    def get(self, request):
        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        query = request.GET.get("cphone", "")
        query = unquote(query).strip()
        if query:
            custs = CustomerData.objects.filter(cphone__icontains=query)
        else:
            custs = CustomerData.objects.filter(user=self.request.user.id).order_by("id")
            # custs = CustomerData.objects.filter(
              #  user=self.request.user.id, datec__gte=first_day_of_month
            #).order_by("id")
        
        context = {
            "custs": custs,
        }
        return render(request, "inventory/dashboard2.html", context)

class DeleteItemCust(LoginRequiredMixin, DeleteView):
	model = CustomerData
	template_name = 'inventory/cust-delete.html'
	success_url = reverse_lazy('dashboard2')
	context_object_name = 'itemcust'

class EditItemCust(LoginRequiredMixin, UpdateView):
	model = CustomerData
	form_class = CustomerDataForm
	template_name = 'inventory/customeradd.html'
	success_url = reverse_lazy('dashboard2')

class Dashboard3(LoginRequiredMixin, View):
    def get(self, request):
        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        query = request.GET.get("sphone", "")
        query = unquote(query).strip()
        if query:
            supps = SupplierData.objects.filter(sphone__icontains=query)
        else:
            #supps = SupplierData.objects.filter(user=self.request.user.id).order_by("id")
            supps = SupplierData.objects.filter(
    		user=self.request.user.id
			).order_by("-id")[:10]  # Order by descending 'id' and limit to 10

            #supps = SupplierData.objects.filter(
            #user=self.request.user.id, datecl__gte=first_day_of_month
            #).order_by("-id")[:10]
        
        context = {
            "supps": supps,
        }
        return render(request, "inventory/dashboard3.html", context)

class SupplierAd(LoginRequiredMixin, CreateView):
	model = SupplierData
	form_class = SupplierDataForm
	template_name = 'inventory/supplieradd.html'
	success_url = reverse_lazy('dashboard3')

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)
		

class DeleteItemSup(LoginRequiredMixin, DeleteView):
	model = SupplierData
	template_name = 'inventory/supp-delete.html'
	success_url = reverse_lazy('dashboard3')
	context_object_name = 'itemsup'

class EditItemSup(LoginRequiredMixin, UpdateView):
	model = SupplierData
	form_class = SupplierDataForm
	template_name = 'inventory/supplieradd.html'
	success_url = reverse_lazy('dashboard3')
		
class Dashboard4(LoginRequiredMixin, CreateView):
    def get(self, request):
        # Corrected the filter query
        owners = OwnerData.objects.filter(user=self.request.user).order_by("id")
        
        context = {
            "owners": owners,
        }
        return render(request, "inventory/dashboard4.html", context)

class EditOwner(LoginRequiredMixin, UpdateView):
	model = OwnerData
	form_class = OwnerDataForm
	template_name = 'inventory/owneradd.html'
	success_url = reverse_lazy('dashboard4')

class OwnerAd(LoginRequiredMixin, CreateView):
	model = OwnerData
	form_class = OwnerDataForm
	template_name = 'inventory/owneradd.html'
	success_url = reverse_lazy('dashboard4')

class Dashboard5(LoginRequiredMixin, View):
    def get(self, request):
        today = datetime.now()
        first_day_of_month = today.replace(day=1)
        query = request.GET.get("phone", "")
        query = unquote(query).strip()
        if query:
            invoices = CustInvoiceData.objects.filter(phone__icontains=query)
        else:
            invoices = CustInvoiceData.objects.filter(
    			user=self.request.user.id
			).order_by("-id")[:10]  # Order by descending 'id' and limit to 10

            #invoices = CustInvoiceData.objects.filter(
                #user=self.request.user.id, datein__gte=first_day_of_month
            #).order_by("id")
        
        context = {
            "invoices": invoices,
        }
        return render(request, "inventory/dashboard5.html", context)

	
class EditItemInv(LoginRequiredMixin, UpdateView):
	model = CustInvoiceData
	form_class = InvoicedataForm
	template_name = 'inventory/invoiceadd.html'
	success_url = reverse_lazy('dashboard5')

class DeleteItemInv(LoginRequiredMixin, DeleteView):
	model = CustInvoiceData
	template_name = 'inventory/delete-inv.html'
	success_url = reverse_lazy('dashboard5')
	context_object_name = 'invoices'

@method_decorator(csrf_exempt, name="dispatch")  # Disable CSRF for AJAX (only in development)
class InvoiceAd(LoginRequiredMixin, View):
    def get(self, request):
        cphone_query = request.GET.get("cphone", "").strip()
        imi_query = request.GET.get("imi", "").strip()
        customers, prods = [], []

        if cphone_query:
            customers = CustomerData.objects.filter(cphone__icontains=cphone_query)
            if not customers.exists():
                messages.error(request, "No customer record found.")

        if imi_query:
            prods = InventoryItem.objects.filter(imi__icontains=imi_query)
            if not prods.exists():
                messages.error(request, "No product record found.")

        return render(request, "inventory/invoiceadd.html", {
                "customers": customers if customers else [],
                "prods": prods if prods else []
        })
        # return render(request, "inventory/invoiceadd.html", {"customers": customers, "prods": prods})

    def post(self, request):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":  # AJAX request
            try:
                data = json.loads(request.body)

                # Check if the request is for customer & product search 
                if "imi" in data:
                    imi_number = data["imi"]
                    product = get_object_or_404(InventoryItem, imi=imi_number)
                    return JsonResponse({
                        "name": product.name,
                        "price": product.price
                    }, status=200)

                elif "cphone" in data:
                    customer_id = data["cphone"]
                    customer = get_object_or_404(CustomerData, cphone=customer_id)
                    return JsonResponse({
                        "name": customer.cname,
                        "nie" : customer.cnie,
                        "address": customer.caddress,
                    }, status=200)

                    
                return JsonResponse({"message": "Invoice saved successfully!"}, status=200)

                return JsonResponse({"error": "Invalid data"}, status=400)

            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({"error": "Invalid request"}, status=400)		


@login_required  
def save_invoice(request):
    if request.method == "POST":
        try:
            # Load JSON data from the request body
            data = json.loads(request.body)
            customer_phone = data.get('customer', '')
            items = data.get('items', [])

            # Step 1: Create the invoice (CustinvoiceData - Parent)
            #customer = CustomerData.objects.get(cphone=customer_phone)  # Assuming customer exists
        
            try:
                customer = CustomerData.objects.get(cphone=customer_phone)
            except CustomerData.DoesNotExist:
                return JsonResponse({'error': 'Customer not found'}, status=400)

            #invoice = CustInvoiceData.objects.create(customer=customer)
            
            invoice = CustInvoiceData.objects.create(
                customer=customer,
                user=request.user,  # Assign logged-in user
                address=customer.caddress,  # Storing customer address
                nif=customer.cnie,  # Storing customer email
                phone=customer.cphone  # Storing customer phone
                
                
            )


            for item in items:
                # Create the invoice detail (invoice_item)
                invoice_item = InvoiceDetail.objects.create(
                    invoice=invoice,
                    imi=item['imi'],
                    name=item['name'],
                    price=item['price'],
                    quantity=item['quantity'],
                    total=item['total']
                )

                # Now, call the reduce_inventory method on the invoice_item instance
                invoice_item.reduce_inventory()  # Properly using the instance to call reduce_inventory()

            # Return response with invoice ID for PDF generation
            return JsonResponse({'message': 'Invoice saved successfully', 'invoice_id': invoice.id}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'invoiceadd.html')


@login_required
def viewPDFInvoice(request, invoice_id):
    # Ensure invoice exists
    invoice = get_object_or_404(CustInvoiceData, id=invoice_id)
    
    # Fetch invoice items
    products = InvoiceDetail.objects.filter(invoice=invoice)

    # Fetch company details (OwnerData)
    p_settings = OwnerData.objects.first()

    # Calculate Invoice Total
    invoiceTotal = sum(item.total for item in products)

    # Context for the template
    context = {
        "invoice": invoice,
        "products": products,
        "p_settings": p_settings,
        "invoiceTotal": invoiceTotal,
    }

    # ✅ Render the template to HTML
    template = get_template("invoice/invoice-template.html")
    html = template.render(context)

    # ✅ Generate PDF using correct wkhtmltopdf path
    pdf = pdfkit.from_string(html, False, configuration=settings.PDFKIT_CONFIG)

    # ✅ Return PDF as response
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{invoice.id}.pdf"'
    return response

def InvoiceDetailView(request, invoice_id):
    invoice = get_object_or_404(CustInvoiceData, id=invoice_id)  # Fetch the parent invoice
    invoice_items = InvoiceDetail.objects.filter(invoice=invoice)  # Fetch related items
    
    invoiceTotal = sum(item.quantity * item.price for item in invoice_items)

    return render(request, 'inventory/invoice_detail.html', {
    'invoice': invoice,
    'invoice_items': invoice_items,
    'invoiceTotal': invoiceTotal
    
    })



def sales_report(request):
    start_date_str = request.GET.get("start_date", "")
    end_date_str = request.GET.get("end_date", "")

    sales = CustInvoiceData.objects.filter(user=request.user)

    # Parse start_date and end_date
    start_date = parse_dates(start_date_str)
    end_date = parse_dates(end_date_str)

    if start_date and end_date:
        # Make the dates timezone-aware
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        sales = sales.filter(datein__range=[start_date, end_date])

    # ✅ Correctly compute total amount per invoice
    sales = sales.annotate(total_amount=Sum("items__total"))

    # ✅ Compute grand total (sum of all invoices)
    grand_total = sum(sale.total_amount for sale in sales if sale.total_amount)

    return render(request, "inventory/sales_report.html", {
        "sales": sales,
        "start_date": start_date,
        "end_date": end_date,
        "grand_total": grand_total
    })


from django.utils.dateformat import DateFormat

@login_required
def export_sales_report_pdf(request):
    start_date_str = request.GET.get("start_date", "")
    end_date_str = request.GET.get("end_date", "")

    sales = CustInvoiceData.objects.filter(user=request.user)

    # Parse start_date and end_date
    start_date = parse_dates(start_date_str)
    end_date = parse_dates(end_date_str)

    if start_date and end_date:
        # Make the dates timezone-aware
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        sales = sales.filter(datein__range=[start_date, end_date])

    # ✅ Compute total per invoice
    sales = sales.annotate(total_amount=Sum("items__total"))

    # ✅ Compute grand total
    grand_total = sum(sale.total_amount for sale in sales if sale.total_amount)

    # Format start_date and end_date for display in the template
    formatted_start_date = DateFormat(start_date).format("b d, Y") if start_date else ""
    formatted_end_date = DateFormat(end_date).format("b d, Y") if end_date else ""

    # Get the current date for footer display
    current_date = timezone.localtime(timezone.now()).strftime("%b d, Y")

    context = {
        "sales": sales,  # Pass the sales with total_amount calculated
        "start_date": formatted_start_date,
        "end_date": formatted_end_date,
        "grand_total": grand_total,  # Ensure grand total is included
        "current_date": current_date  # Add current date for footer
    }

    # ✅ Generate PDF
    template = get_template("inventory/sales_report_pdf.html")
    html = template.render(context)
    pdf = pdfkit.from_string(html, False, configuration=settings.PDFKIT_CONFIG)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="sales_report_{formatted_start_date}_to_{formatted_end_date}.pdf"'
    return response



def export_customers_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="customer_list.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # ✅ Correctly get the absolute path of the logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'manda-logo.png')

    # ✅ Add logo if the file exists
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=60)  # Adjust width/height as needed
        elements.append(logo)

    # ✅ Add title "Customer List"
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Customer List</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))  # Add spacing below title

    # ✅ Define table header
    data = [["ID", "Name", "NIE", "Phone", "Address", "Date Created"]]
    customers = CustomerData.objects.all().values_list("id", "cname", "cnie", "cphone", "caddress", "datec")

    for customer in customers:
        data.append(list(customer))

    # ✅ Create table with styling
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    return response

def export_products_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="products_list.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # ✅ Correctly get the absolute path of the logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'manda-logo.png')

    # ✅ Add logo if the file exists
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=60)  # Adjust width/height as needed
        elements.append(logo)

    # ✅ Add title "Product List"
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Product List</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))  # Add spacing below title

    # ✅ Define table header
    data = [["IMI", "Name", "Quantity", "Price", "Supply", "Supplier phone", "Supply-date"]]
    
    # Fetch products with supplier data
    products = InventoryItem.objects.all().select_related('supply').values_list(
        "imi", "name", "quantity", "price", "supply__sname", "supply__sphone", "datecrea"
    )

    for product in products:
        # Add data for each product, including supplier's name and phone
        data.append(list(product))

    # ✅ Create table with styling
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    return response

def export_suppliers_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="supplier_list.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # ✅ Correctly get the absolute path of the logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'manda-logo.png')

    # ✅ Add logo if the file exists
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=60)  # Adjust width/height as needed
        elements.append(logo)

    # ✅ Add title "Customer List"
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Customer List</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))  # Add spacing below title

    # ✅ Define table header
    data = [["ID", "Name", "Phone", "Address", "Date Created"]]
    suppliers = SupplierData.objects.all().values_list("id", "sname", "sphone", "saddress", "datecl")

    for supplier in suppliers:
        data.append(list(supplier))

    # ✅ Create table with styling
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    return response




