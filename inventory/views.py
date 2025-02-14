
from decimal import Decimal, ROUND_HALF_UP
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
from .models import InventoryItem, Category, CustomerData, SupplierData, OwnerData, CustInvoiceData, InvoiceDetail, OwnerData
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils.dateformat import DateFormat
from django.utils.dateparse import parse_date
from django.utils import timezone
from urllib.parse import unquote 
from django.http import JsonResponse
import os
import json
import pdfkit
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
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


LOW_QUANTITY = 2  # Adjust this as per your requirement

class Dashboard(LoginRequiredMixin, View):
    def get(self, request):
        items = InventoryItem.objects.filter(user=request.user).order_by('id')
        query = request.GET.get("imi", "").strip()

        if query:
            items = items.filter(imi__icontains=unquote(query))

        sold_items_count = InventoryItem.objects.filter(user=request.user, quantity=0).count()
        low_inventory_count = InventoryItem.objects.filter(user=request.user, quantity__lte=LOW_QUANTITY).exclude(quantity=0).count()

        # Handling messages based on the inventory conditions
        if sold_items_count > 0:
            messages.error(request, f"{sold_items_count} item{'s' if sold_items_count > 1 else ''} sold")

        if low_inventory_count > 0:
            messages.error(request, f"{low_inventory_count} item{'s' if low_inventory_count > 1 else ''} has low inventory")

        low_inventory_ids = InventoryItem.objects.filter(user=request.user, quantity__lte=LOW_QUANTITY).values_list('id', flat=True)

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

    def post(self, request):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":  # AJAX request
            try:
                data = json.loads(request.body)

                # Product Search
                if "imi" in data:
                    imi_number = data["imi"]
                    product = get_object_or_404(InventoryItem, imi=imi_number)
                    return JsonResponse({
                        "name": product.name,
                        "price": product.price
                    }, status=200)

                # Customer Search
                elif "cphone" in data:
                    customer_id = data["cphone"]
                    customer = get_object_or_404(CustomerData, cphone=customer_id)
                    return JsonResponse({
                        "name": customer.cname,
                        "nie": customer.cnie,
                        "address": customer.caddress,
                    }, status=200)

                return JsonResponse({"message": "Invoice saved successfully!"}, status=200)

            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({"error": "Invalid request"}, status=400)




@login_required
@csrf_exempt
def save_invoice(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            customer_phone = data.get('customer', '').strip()
            items = data.get('items', [])

            if not customer_phone:
                return JsonResponse({'error': 'Customer phone is required'}, status=400)

            if not items:
                return JsonResponse({'error': 'Invoice must have at least one item'}, status=400)

            # Fetch the customer
            try:
                customer = CustomerData.objects.get(cphone=customer_phone)
            except CustomerData.DoesNotExist:
                return JsonResponse({'error': 'Customer not found'}, status=400)

            # Fetch the owner's IVA setting
            owner_data = OwnerData.objects.filter(user=request.user).first()
            iva_percentage = Decimal(owner_data.iva if owner_data else 0.0)

            # Calculate totals
            total_before_iva = sum(Decimal(item['total']) for item in items if 'total' in item)
            total_after_iva = round(total_before_iva * (Decimal(1) + iva_percentage / Decimal(100)), 2)

            with transaction.atomic():
                invoice = CustInvoiceData.objects.create(
                    customer=customer,
                    user=request.user,
                    address=customer.caddress,
                    nif=customer.cnie,
                    phone=customer.cphone,
                    total_before_iva=total_before_iva,
                    total_after_iva=total_after_iva
                )

                for item in items:
                    try:
                        inventory_item = InventoryItem.objects.get(imi=item['imi'])
                        quantity = int(item['quantity'])

                        if inventory_item.quantity < quantity:
                            raise ValueError(f"Not enough stock for {inventory_item.name}. Only {inventory_item.quantity} left.")

                        InvoiceDetail.objects.create(
                            invoice=invoice,
                            imi=item['imi'],
                            name=item['name'],
                            price=Decimal(item['price']),
                            quantity=quantity,
                            total=Decimal(item['total'])
                        )

                        inventory_item.quantity -= quantity
                        inventory_item.save()
                    except InventoryItem.DoesNotExist:
                        return JsonResponse({'error': f"Product with IMI {item['imi']} not found"}, status=400)
                    except ValueError as e:
                        return JsonResponse({'error': str(e)}, status=400)

            return JsonResponse({
                'message': 'Invoice saved successfully',
                'invoice_id': invoice.id,
                'total_before_iva': total_before_iva,
                'total_after_iva': total_after_iva
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)



def viewPDFInvoice(request, invoice_id):
    invoice = CustInvoiceData.objects.get(id=invoice_id)
    products = InvoiceDetail.objects.filter(invoice=invoice)
    owner = OwnerData.objects.first()  # Fetch company details for header

    context = {
        "invoice": invoice,
        "products": products,
        "owner": owner,
        "invoiceTotal": invoice.total_before_iva,
        "invoiceTotalAfterIVA": invoice.total_after_iva
    }

    # Load the HTML template and render it
    template = get_template("invoice/invoice-template.html")
    html = template.render(context)

    # Generate PDF using pdfkit
    options = {
        'page-size': 'A4',
        'encoding': "UTF-8",
        'enable-local-file-access': None
    }
    pdf = pdfkit.from_string(html, False, configuration=settings.PDFKIT_CONFIG, options=options)

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
    owner_data = OwnerData.objects.filter(user=request.user).first()
    iva_percentage = Decimal(owner_data.iva if owner_data else 0.0)

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
    total_after_iva = round(grand_total * (Decimal(1) + iva_percentage / Decimal(100)), 2)

    return render(request, "inventory/sales_report.html", {
        "sales": sales,
        "start_date": start_date,
        "end_date": end_date,
        "grand_total": grand_total,
        "total_after_iva": total_after_iva
    })


@login_required
def export_sales_report_pdf(request):
    start_date_str = request.GET.get("start_date", "")
    end_date_str = request.GET.get("end_date", "")

    sales = CustInvoiceData.objects.filter(user=request.user).order_by("datein")  # ✅ Sort sales by date
    owner_data = OwnerData.objects.filter(user=request.user).first()
    iva_percentage = Decimal(owner_data.iva if owner_data and owner_data.iva is not None else 0.0)

    # Parse start_date and end_date
    start_date = parse_dates(start_date_str)
    end_date = parse_dates(end_date_str)
    

    if start_date and end_date:
        start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
        end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
        sales = sales.filter(datein__range=[start_date, end_date])

    # ✅ Compute total per invoice
    sales = sales.annotate(total_amount=Sum("items__total"))

    # ✅ Compute grand total safely
    grand_total = sum((sale.total_amount or 0) for sale in sales)
    grand_total = Decimal(grand_total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # ✅ Compute total_after_iva
    total_after_iva = grand_total * (Decimal(1) + iva_percentage / Decimal(100))
    total_after_iva = total_after_iva.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # ✅ Compute total IVA
    total_iva = total_after_iva - grand_total
    total_iva = total_iva.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # ✅ Format dates correctly
    formatted_start_date = DateFormat(start_date).format("b d, Y") if start_date else "N/A"
    formatted_end_date = DateFormat(end_date).format("b d, Y") if end_date else "N/A"

    # ✅ Get current date
    current_date = timezone.localtime(timezone.now()).strftime("%b %d, %Y")

    context = {
        "sales": sales,
        "start_date": formatted_start_date,
        "end_date": formatted_end_date,
        "grand_total": grand_total,
        "total_after_iva": total_after_iva,
        "total_iva": total_iva,
        "current_date": current_date,
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
    shop_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'shoplogo1.png')
    manda_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'manda-logo.png')

    # ✅ Add logo if the file exists
    if os.path.exists(shop_logo_path):
        shop_logo = Image(shop_logo_path, width=50, height=38)  # Adjust width/height as needed
        elements.append(shop_logo)

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
    elements.append(Spacer(1, 20))

# ✅ Add logo at the bottom (centered)
    if os.path.exists(manda_logo_path):
        manda_logo = Image(manda_logo_path, width=30, height=15)  # Adjust size as needed
        elements.append(manda_logo)


    doc.build(elements)

    return response



def export_products_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="products_list.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    
    # ✅ Correctly get the absolute path of the logo
    shop_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'shoplogo1.png')
    manda_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'manda-logo.png')
    

    # ✅ Add logo at the top and center it
    styles = getSampleStyleSheet()
    if os.path.exists(shop_logo_path):
        shop_logo = Image(shop_logo_path, width=50, height=38)  # Adjust size as needed
        elements.append(shop_logo)
        elements.append(Spacer(1, 12))

    # ✅ Add title "Product List"
    title = Paragraph("<b>Product List</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # ✅ Define table header
    data = [["IMI", "Name", "Quantity", "Cost", "Price", "Supply", "Supplier Phone", "Supply Date"]]

    # Fetch products with supplier data
    products = InventoryItem.objects.all().select_related('supply').values_list(
        "imi", "name", "quantity", "cost", "price", "supply__sname", "supply__sphone", "datecrea"
    )

    total_cost = 0
    total_price = 0

    for product in products:
        data.append(list(product))
        total_cost += product[3]  # Index 3 = cost
        total_price += product[4]  # Index 4 = price

    # ✅ Add total row at the bottom
    data.append(["", "", "Grand Total:€", f"{total_cost:.2f}", f"{total_price:.2f}", "", "", ""])

    # ✅ Compute total profit
    total_profit = Decimal(total_price) - Decimal(total_cost)
    total_profit = total_profit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # ✅ Append profit row
    #data.append(["", "", "Total Profit:€", f"{total_profit:.2f}", "", "", "", ""])

    # ✅ Create table with styling
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (3, -1), (4, -1), colors.blue)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # ✅ Add profit summary text below the table
    profit_summary = Paragraph(f"<b>Total difference: €{total_profit}</b>", styles['Title'])
    elements.append(profit_summary)

    elements.append(Spacer(1, 20))

    
    # ✅ Add logo at the bottom (centered)
    if os.path.exists(manda_logo_path):
        manda_logo = Image(manda_logo_path, width=30, height=15)  # Adjust size as needed
        elements.append(manda_logo)

    doc.build(elements)
    
    return response


def export_suppliers_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="supplier_list.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # ✅ Correctly get the absolute path of the logo
    shop_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'shoplogo1.png')
    manda_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'manda-logo.png')

    # ✅ Add logo if the file exists
    if os.path.exists(shop_logo_path):
        shop_logo = Image(shop_logo_path, width=50, height=38)  # Adjust width/height as needed
        elements.append(shop_logo)

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
    elements.append(Spacer(1, 20))

# ✅ Add logo at the bottom (centered)
    if os.path.exists(manda_logo_path):
        manda_logo = Image(manda_logo_path, width=30, height=15)  # Adjust size as needed
        elements.append(manda_logo)

    doc.build(elements)

    return response




