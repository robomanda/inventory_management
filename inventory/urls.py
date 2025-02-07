from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from .views import Index, SignUpView, CustomLogoutView, Dashboard, AddItem, EditItem, DeleteItem, CustomerAd, CustomLogoutView, Dashboard2, DeleteItemCust, EditItemCust, Dashboard3, SupplierAd, DeleteItemSup, EditItemSup, Dashboard4, EditOwner, OwnerAd, Dashboard5, InvoiceAd, EditItemInv, DeleteItemInv, save_invoice, viewPDFInvoice, InvoiceDetailView, export_sales_report_pdf, sales_report
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('dashboard2/', Dashboard2.as_view(), name='dashboard2'),
    path('dashboard3/', Dashboard3.as_view(), name='dashboard3'),
    path('dashboard4/', Dashboard4.as_view(), name='dashboard4'),
    path('dashboard5/', Dashboard5.as_view(), name='dashboard5'),
    path('customeradd/', CustomerAd.as_view(), name ='customeradd'),
    path('supplieradd/', SupplierAd.as_view(), name='supplieradd'),
    path('owneradd/', OwnerAd.as_view(), name='owneradd'),
    path('add-item/', AddItem.as_view(), name='add-item'),
    path('invoiceadd/', InvoiceAd.as_view(), name='invoiceadd'),
    path('edit-item/<int:pk>/', EditItem.as_view(), name='edit-item'),
    path('edit-inv/<int:pk>/', EditItemInv.as_view(), name='edit-inv'),
    path('cust-edit/<int:pk>/', EditItemCust.as_view(), name='cust-edit'),
    path('delete-item/<int:pk>/', DeleteItem.as_view(), name='delete-item'),
    path('delete-inv/<int:pk>/', DeleteItemInv.as_view(), name='delete-inv'),
    path('cust-delete/<int:pk>/', DeleteItemCust.as_view(), name='cust-delete'),
    path('supp-edit/<int:pk>/', EditItemSup.as_view(), name='supp-edit'),
    path('supp-delete/<int:pk>/', DeleteItemSup.as_view(), name='supp-delete'),
    path('edit-owner/<int:pk>/', EditOwner.as_view(), name='edit-owner'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    #path('logout/', auth_views.CustomLogoutView.as_view(template_name='inventory/logout.html'), name='logout'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path("save-invoice/", save_invoice, name="save_invoice"),
    path('invoice/<int:invoice_id>/pdf/', viewPDFInvoice, name='invoice_pdf'),
    path('invoice/<int:invoice_id>/', InvoiceDetailView, name='invoice_detail'),
    path('sales-report/', sales_report, name='sales_report'),
    path('sales-report/pdf/', export_sales_report_pdf, name='export_sales_report_pdf'),
]

