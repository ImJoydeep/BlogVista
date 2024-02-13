'''party urls'''
from django.urls import path
from party.supplier_bulk_api import SupplierBulkAPIView, ManufacturerBulkAPIView

from party.maufacturer_multiple_views import ManufacturerMultipleStatusUpdate
from .views import GetCountryList, GetStateList, ContactPurposeTypeList, ContactMethodTypeList, LegalStatusTypeList
from .employee_views import EmployeeViews, EmployeeListViews
from .employee_update_views import EmployeeUpdateViews
from .employee_multiple_views import EmployeeMultipleStatusUpdate
from .supplier_views import SupplierCreateViews, SupplierListViews, SupplierUpdateViews
from .supplier_multiple_views import SupplierMultipleStatusUpdate, SupplierKeyValueCheckView
from .manufacturer_views import ManufacturerCreateViews, ManufacturerListViews, ManufacturerUpdateViews
from .customer_views import CustomerCreateViews, CustomerListViews,CustomerUpdateViews,CustomerStatusUpdate,CustomerDeleteAPIView

urlpatterns = [
    path('contactpurpose/', ContactPurposeTypeList.as_view(), name="contactpurpose"),
    path('contactmethod/', ContactMethodTypeList.as_view(), name="contactmethod"),
    path('legalstatustype/', LegalStatusTypeList.as_view(), name="legalstatustype"),
    path('country/', GetCountryList.as_view(), name="Country_list"),
    path('state/', GetStateList.as_view(), name="State_List"),
    path('employee/', EmployeeViews.as_view(), name="employee_create"),
    path('employeelist/', EmployeeListViews.as_view(), name="employee_list"),
    path('employee/multiple/',
         EmployeeMultipleStatusUpdate.as_view(), name="employee_multiple_status_update"),
    path('employee/<employee_id>/',
         EmployeeUpdateViews.as_view(), name="employee_update"),
    path('supplier/', SupplierCreateViews.as_view(), name="supplier_create"),
    path('supplierlist/', SupplierListViews.as_view(), name="supplier_list"),
    path('supplier/multiple/',
         SupplierMultipleStatusUpdate.as_view(), name="supplier_multiple_status_update"),
    path('supplier/keyvaluecheck/',
         SupplierKeyValueCheckView.as_view(), name="supplier_key_value_check"),
    path('supplier/bulk/', SupplierBulkAPIView.as_view(),
         name="supplier_bulk_create_update"),
    path('supplier/<ID_SPR>/',
         SupplierUpdateViews.as_view(), name="supplier_update"),

    path('manufacturer/', ManufacturerCreateViews.as_view(),
         name="manufacturer_create"),
    path('manufacturerlist/', ManufacturerListViews.as_view(),
         name="manufacturer_list"),
    path('manufacturer/multiple/',
         ManufacturerMultipleStatusUpdate.as_view(), name="manufacturer_multiple_status_update"),
    path('manufacturer/bulk/', ManufacturerBulkAPIView.as_view(),
         name="manufacturer_bulk_create_update"),
    path('manufacturer/<ID_MF>/',
         ManufacturerUpdateViews.as_view(), name="manufacturer_update"),
    path('customer/', CustomerCreateViews.as_view(),
         name="customer_create"),
    path('customer/<int:pk>/', CustomerUpdateViews.as_view(),
         name="Update Customer"),
    path('customerlist/', CustomerListViews.as_view(),
         name="customer_list"),
    path('customer/statusupdate/', CustomerStatusUpdate.as_view(),
         name="Customer Status Update"),
    path('customer/delete/', CustomerDeleteAPIView.as_view(),
         name="Delete Customer"),
]
