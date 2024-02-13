import io
import PyPDF2
import pdfkit
import logging
import os
import zipfile
import json
import requests
import pandas as pd
from datetime import datetime
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse
from django.template import Template, Context
from django.db.models import Q
from django.core.mail import EmailMessage
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (ListModelMixin)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.mixins import (RetrieveModelMixin)
from drf_yasg.utils import swagger_auto_schema
from copy import deepcopy
from accesscontrol.models import Operator, OperatorBusinessUnitAssignment
from auto_responder.models import EmailTemplate
from order.order_elastic import order_save
from order.serializers_invoice import InvoicePdfSerializer, InvoiceSerializer
from product.models.models_item import Item
from globalsettings.models import BusinessUnitSetting, GlobalSetting
from order.serializers_shipment import GenerateInvoiceSerializer, \
    ItemShipmentListSerializer, ShipmentListSerializer
from order.invoice_filter import invoice_filter
from order.generate_invoice_html import generate_invoice
from item_stock.models import ItemInventory
from store.models import InventoryLocation, Location
from taxonomy.taxonomy_magento_integration import magento_login
from order.serializers import OrderElasticDataSerializer, OrderInvoiceSerializer, OrderMasterSerializer, ItemStockOrderSerializer
from order.models import Customer, ItemShipmentList, OrderActivity, OrderInvoice, OrderInvoicePicklistType, \
    OrderInvoiceTemplate, OrderItemDetails, OrderItemInvoince, OrderMaster, PicklistMaster, ShipmentMaster

logger = logging.getLogger(__name__)

response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_ARRAY,
                             description='Array of Ids',
                             items=openapi.Items(type=openapi.TYPE_STRING,
                                                 description='Order Id')),
        'ID_BSN_UN': openapi.Schema(type=openapi.TYPE_INTEGER, description="Business unit id")
    },
)


def create_invoice_code(invoice_text):
    last_invoice = OrderInvoice.objects.filter(
        OD_INVOE_OD_ID__OD_TYPE="DNB Order").last()
    if last_invoice:
        last_invoice_id = str(
            last_invoice.OD_INVOE_INCR_ID).replace(invoice_text, "")
        last_invoice_id = int(last_invoice_id) + 1
        last_invoice_id = str(last_invoice_id).zfill(6)
        custom_invoice_id = invoice_text+str(last_invoice_id)
    else:
        last_invoice_id = 0
        last_invoice_id = int(last_invoice_id) + 1
        last_invoice_id = str(last_invoice_id).zfill(6)
        custom_invoice_id = invoice_text+str(last_invoice_id)
    return custom_invoice_id


def invoice_create_if_not_exist(order_instance, requested_data):
    '''Invoice Generate if does not exist'''
    invoice_item_data = []
    od_invoice_picklist_ty_instance = OrderInvoicePicklistType.objects.filter(
        OD_INV_PICK_NM__icontains="Invoice").first()
    item_instance = ItemShipmentList.objects.filter(
        OD_ID=order_instance.OD_ID)
    for item in item_instance:
        invoice_item_data.append(
            {
                "extension_attributes": {},
                "order_item_id": item.OD_ITM_ID.OD_ITM_ID_ITM,
                "qty": item.ITM_SHP_GRN_QTY
            }
        )
    if str(order_instance.OD_TYPE).lower() != 'dnb order':
        requested_data = create_or_get_invoice_for_order(
            order_instance, invoice_item_data, od_invoice_picklist_ty_instance)
    return requested_data


class GetStoreWiseProduct(GenericAPIView):
    '''Get the store wise product list class'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ItemStockOrderSerializer

    @swagger_auto_schema(tags=['Order'], operation_description="Get Store wise product", operation_summary="Get store wise product list", manual_parameters=[openapi.Parameter('STR_ID', openapi.IN_QUERY,
                                                                                                                                                                               description="Store id",
                                                                                                                                                                               type=openapi.TYPE_STRING),
                                                                                                                                                             openapi.Parameter('store_filter', openapi.IN_QUERY,
                                                                                                                                                                               description="Get all mageworx store",
                                                                                                                                                                               type=openapi.TYPE_INTEGER)])
    def get(self, request, *args, **kwargs):
        '''Get product list'''
        store_id = request.GET.get("STR_ID", None)
        store_filter = int(request.GET.get("store_filter", 0))
        search = request.GET.get('search', '')
        page_size = request.GET.get('page_size', 10)
        limit = int(page_size)
        page = 1
        offset = (page - 1) * limit
        serializer = {}
        store_id_list = []
        if store_id:
            store_id_list = list(Location.objects.filter(
                MAG_MAGEWORX_STR_ID__isnull=False, id=store_id).values_list('id', flat=True))
        else:
            store_id_list = list(Location.objects.filter(
                MAG_MAGEWORX_STR_ID__isnull=False).values_list('id', flat=True))
        logger.info("Mageworx Store ID List : %s", store_id_list)
        if store_filter >= 1:
            logger.info("Store Filter")
            serializer = Location.objects.filter(
                MAG_MAGEWORX_STR_ID__isnull=False).values()
            op_instance = Operator.objects.filter(
                NM_USR__iexact=self.request.user.username)
            if op_instance.exists():
                store_list = OperatorBusinessUnitAssignment.objects.filter(
                    ID_OPR=op_instance.first().ID_OPR).values_list('ID_LCN', flat=True)
                serializer = Location.objects.filter(
                    id__in=store_list, MAG_MAGEWORX_STR_ID__isnull=False).values()
        elif store_id_list:
            logger.info("Store ID List")
            warehouse_id_list = InventoryLocation.objects.filter(
                ID_STR=store_id).values_list('ID_WRH', flat=True)
            logger.info("Warehouse List : %s", warehouse_id_list)
            '''
            "if warehouse_id_list:
                filter_query = Q()
                filter_query.add(
                    Q(WRH_ID__in=warehouse_id_list) &
                    Q(Q(STK_ITM_INVTRY_ID__ID_ITM__AS_ITM_SKU__icontains=search) | Q(
                        STK_ITM_INVTRY_ID__ID_ITM__NM_ITM__icontains=search)),
                    Q.AND
                )
                item_stock = ItemInventory.objects.filter(
                    filter_query)
                paginated_data = item_stock[offset:offset+limit]
                serializer = StoreWiseProductSerilaizer(
                    paginated_data, many=True).data"
            '''
            item_filter_query = Q()
            item_filter_query.add(
                Q(AS_ITM_SKU__icontains=search) | Q(NM_ITM__icontains=search),
                Q.AND
            )
            item_obj = Item.objects.filter(item_filter_query)
            item_obj = item_obj.filter(AS_ITM_STATUS="A")
            logger.info("Item Obj : %s", item_obj)
            item_pagination = item_obj[offset:offset+limit]
            context_data = pd.DataFrame(
                {'data': {"ID_WRH": warehouse_id_list[0]}})
            serializer = ItemStockOrderSerializer(
                item_pagination, many=True, context={'request': context_data}).data

        return Response(serializer, status=status.HTTP_200_OK)


class CustomerDetailsView(GenericAPIView):
    '''Get the store wise product list class'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve_customer_details(self, order_instance, cus, response_list):
        '''Retrieve customer details'''
        billing_instance = order_instance.orderbillingaddress_set.last()
        shipping_instance = order_instance.ordershippingaddress_set.last()
        response = {
            "id": cus.id,
            "OD_CUS_NM": cus.CUST_FNM + ' ' + cus.CUST_LNM,
            "OD_CUS_EMAIL": cus.CUST_EMAIL
        }
        if shipping_instance:
            shipping = {
                "OD_SA_FN": shipping_instance.OD_SA_FN,
                "OD_SA_LN": shipping_instance.OD_SA_LN,
                "OD_SA_EMAIL": shipping_instance.OD_SA_EMAIL,
                "OD_SA_PH": shipping_instance.OD_SA_PH,
                "OD_SA_ST": shipping_instance.OD_SA_ST,
                "OD_SA_CT": shipping_instance.OD_SA_CT,
                "OD_SA_PIN": shipping_instance.OD_SA_PIN,
                "OD_SA_RGN": shipping_instance.OD_SA_RGN,
                "OD_SA_RGN_CODE": shipping_instance.OD_SA_RGN_CODE,
                "OD_SA_RGN_ID": shipping_instance.OD_SA_RGN_ID,
                "OD_SA_CTR_CODE": shipping_instance.OD_SA_CTR_CODE,
            }
            response['shipping'] = shipping
            response['CUST_PH'] = shipping_instance.OD_SA_PH
        if billing_instance:
            billing = {
                "OD_BA_FN": billing_instance.OD_BA_FN,
                "OD_BA_LN": billing_instance.OD_BA_LN,
                "OD_BA_EMAIL": billing_instance.OD_BA_EMAIL,
                "OD_BA_PH": billing_instance.OD_BA_PH,
                "OD_BA_ST": billing_instance.OD_BA_ST,
                "OD_BA_CT": billing_instance.OD_BA_CT,
                "OD_BA_PIN": billing_instance.OD_BA_PIN,
                "OD_BA_RGN": billing_instance.OD_BA_RGN,
                "OD_BA_RGN_CODE": billing_instance.OD_BA_RGN_CODE,
                "OD_BA_RGN_ID": billing_instance.OD_BA_RGN_ID,
                "OD_BA_CTR_CODE": billing_instance.OD_BA_CTR_CODE,
            }
            response['billing'] = billing
        response_list.append(response)
        return response_list

    @swagger_auto_schema(tags=['Order'], operation_description="Get customer details", operation_summary="Get customer details", manual_parameters=[openapi.Parameter('email', openapi.IN_QUERY,
                                                                                                                                                                      description="Email id",
                                                                                                                                                                      type=openapi.TYPE_STRING),
                                                                                                                                                    openapi.Parameter('name', openapi.IN_QUERY,
                                                                                                                                                                      description="Customer Name",
                                                                                                                                                                      type=openapi.TYPE_STRING)])
    def get(self, request, *args, **kwargs):
        '''Get customer list'''
        email_id = request.GET.get('email', '')
        name = request.GET.get('name', '')
        response_list = []
        try:
            filter_query = Q()
            if name:
                first_list = str(name).split(' ')
                if len(first_list) > 1:
                    filter_query.add(Q(Q(CUST_FNM__icontains=first_list[0]) & Q(
                        CUST_LNM__icontains=first_list[1])),
                        Q.AND
                    )
                else:
                    filter_query.add(Q(CUST_FNM__icontains=first_list[0]),
                                     Q.AND
                                     )
            if email_id:
                filter_query.add(
                    Q(CUST_EMAIL__icontains=email_id),
                    Q.AND
                )
            customer_obj = Customer.objects.filter(
                Q(filter_query))
            for cus in customer_obj:
                if cus:
                    order_instance = OrderMaster.objects.filter(
                        OD_CUST=cus.id).last()
                    if order_instance:
                        response_list = self.retrieve_customer_details(
                            order_instance, cus, response_list)
            stat = status.HTTP_200_OK
        except Exception as exp:
            logger.info("Exception occurred : %s", exp)
            stat = status.HTTP_400_BAD_REQUEST
            response_list = []
        return Response(response_list, status=stat)


def send_mail_on_order_invoice_create(serializers, invoice_id, order_instance, od_invoice_picklist_ty_instance):
    '''Send mail on order invoice ceate'''
    if serializers.is_valid():
        serializer_data = serializers.save()
        invoice_templates = generate_invoice(
            order_instance, invoice_id)
        order_invoice_template_instances = OrderInvoiceTemplate()
        order_invoice_template_instances.OD_INVOE_TEMP_FILE = invoice_templates
        order_invoice_template_instances.OD_INVOE_ID = serializer_data
        order_invoice_template_instances.OD_INV_PICK_ID = od_invoice_picklist_ty_instance
        order_invoice_template_instances.save()
        order_instance.OD_INVC_NUM = serializers.data.get("OD_INVOE_INCR_ID")
        order_instance.save()
    return serializers.data


def update_item_data_on_invoice(item, order_instance):
    '''Update item data on invoice'''
    for item_data in item.get('items'):
        item_instance = OrderItemDetails.objects.filter(
            OD_ID=order_instance.OD_ID, OD_ITM_ID_ITM=item_data.get('order_item_id')).first()
        if item_instance:
            item_instance.OD_ITM_QTY_PKD = item_data.get('qty')
            item_instance.OD_ITM_TAX_AMT = item_data.get('tax_amount')
            item_instance.OD_ITM_DSC_AMT = item_data.get(
                'discount_amount')
            item_instance.OD_ITM_NET_AMT = item_data.get(
                'row_total') + item_data.get('tax_amount') - item_data.get('discount_amount')
            item_instance.save()


def update_order_data_on_invoice(order_instance, item):
    '''Update order data on invoice'''
    order_instance.OD_DIS_AMT = float(abs(item.get(
        'discount_amount')))
    order_instance.OD_NT_AMT = float(item.get('subtotal'))
    order_instance.OD_SHP_AMT = float(item.get('shipping_amount'))
    order_instance.OD_TL_AMT = float(item.get('grand_total'))
    order_instance.save()


def create_or_get_invoice_for_order(order_instance, invoice_item_data, od_invoice_picklist_ty_instance):
    '''Create invoice for order'''
    magento_token, magento_url = magento_login()
    headers = {
        "content-type": "application/json"
    }
    get_invoice_url = str(
        magento_url)+f"/rest/default/V1/invoices?searchCriteria[filterGroups][0][filters][0][field]=order_id&searchCriteria[filterGroups][0][filters][0][value]={order_instance.CH_OD_ID}"
    response_get_invoice = requests.get(
        url=get_invoice_url, headers=headers, auth=magento_token)
    loaded_data = json.loads(
        response_get_invoice.text)
    logger.info("Invoice data : %s", loaded_data.get('items'))
    if response_get_invoice.status_code == 200 and len(loaded_data.get('items')) > 0:
        for item in loaded_data.get('items'):
            invoice_payload = {}
            invoice_payload['OD_INVOE_OD_ID'] = order_instance.OD_ID
            invoice_payload['OD_INVOE_INCR_ID'] = item.get(
                'increment_id')
            invoice_payload['OD_INVOE_ENT_ID'] = item.get(
                'entity_id')
            invoice_payload['OD_INVOE_GRND_TOT'] = item.get(
                'grand_total')
            invoice_payload['OD_INVOE_SHIP_AMT'] = item.get(
                'shipping_amount')
            invoice_payload['OD_INVOE_SHIP_INCL_TAX'] = item.get(
                'shipping_incl_tax')
            invoice_payload['OD_INVOE_CRT_AT'] = item.get(
                'created_at')
            invoice_payload['OD_INVOE_UPDT_AT'] = item.get(
                'updated_at')
            invoice_payload['OD_INVOE_STATE_ID'] = item.get(
                'state')
            invoice_payload['OD_INVOE_STR_ID'] = item.get(
                'store_id')
            invoice_payload['OD_INVOE_BILL_ADD_ID'] = item.get(
                'billing_address_id')
            invoice_payload['OD_INVOE_SHIP_ADD_ID'] = item.get(
                'shipping_address_id')
            invoice_payload['OD_SHP_ID'] = order_instance.itemshipmentlist_set.first(
            ).OD_SHP_ID.OD_SHP_ID
            invoice_payload['OD_PICK_ID'] = order_instance.itemshipmentlist_set.first(
            ).OD_PICK_ID.OD_PICK_ID
            serializers = OrderInvoiceSerializer(data=invoice_payload)
            data = send_mail_on_order_invoice_create(
                serializers, item.get('increment_id'), order_instance, od_invoice_picklist_ty_instance)
    else:
        invoice_url = str(
            magento_url) + f"rest/default/V1/order/{order_instance.CH_OD_ID}/invoice"
        invoicepayload = {
            "capture": False,
            "notify": False,
            "items": invoice_item_data
        }
        invoicepayload = json.dumps(invoicepayload)
        create_response = requests.post(
            url=invoice_url, headers=headers, data=invoicepayload, auth=magento_token)
        logger.info("Response for invoice : %s", create_response.status_code)

        if create_response.status_code == 200:
            get_data = json.loads(create_response.text)
            magento_invoice_get_url = str(
                magento_url) + f"/rest/default/V1/invoices/{int(get_data)}"
            response_invoice_get = requests.get(
                url=magento_invoice_get_url, headers=headers, auth=magento_token)
            if response_invoice_get.status_code == 200:
                invoice_magento_response = json.loads(
                    response_invoice_get.text)
                logger.info("Response for get invoice data : %s",
                            create_response.status_code)
                invoice_payload = {}
                invoice_payload['OD_INVOE_OD_ID'] = order_instance.OD_ID
                invoice_payload['OD_INVOE_INCR_ID'] = invoice_magento_response.get(
                    'increment_id')
                invoice_payload['OD_INVOE_ENT_ID'] = invoice_magento_response.get(
                    'entity_id')
                invoice_payload['OD_INVOE_GRND_TOT'] = invoice_magento_response.get(
                    'grand_total')
                invoice_payload['OD_INVOE_SHIP_AMT'] = invoice_magento_response.get(
                    'shipping_amount')
                invoice_payload['OD_INVOE_SHIP_INCL_TAX'] = invoice_magento_response.get(
                    'shipping_incl_tax')
                invoice_payload['OD_INVOE_CRT_AT'] = invoice_magento_response.get(
                    'created_at')
                invoice_payload['OD_INVOE_UPDT_AT'] = invoice_magento_response.get(
                    'updated_at')
                invoice_payload['OD_INVOE_STATE_ID'] = invoice_magento_response.get(
                    'state')
                invoice_payload['OD_INVOE_STR_ID'] = invoice_magento_response.get(
                    'store_id')
                invoice_payload['OD_INVOE_BILL_ADD_ID'] = invoice_magento_response.get(
                    'billing_address_id')
                invoice_payload['OD_INVOE_SHIP_ADD_ID'] = invoice_magento_response.get(
                    'shipping_address_id')
                invoice_payload['OD_SHP_ID'] = order_instance.itemshipmentlist_set.first(
                ).OD_SHP_ID.OD_SHP_ID
                invoice_payload['OD_PICK_ID'] = order_instance.itemshipmentlist_set.first(
                ).OD_PICK_ID.OD_SHP_ID

                serializer = OrderInvoiceSerializer(data=invoice_payload)
                if serializer.is_valid():
                    serializer_data = serializer.save()
                    invoice_template = generate_invoice(
                        order_instance, invoice_magento_response.get('increment_id'))
                    order_invoice_template_instance = OrderInvoiceTemplate()
                    order_invoice_template_instance.OD_INVOE_TEMP_FILE = invoice_template
                    order_invoice_template_instance.OD_INVOE_ID = serializer_data
                    order_invoice_template_instance.save()
                    logger.info("Generate invoice template successfully done")
                    data = serializer.data
    return data


class OrderInvoiceGet(RetrieveModelMixin, GenericAPIView):
    '''Order Invoice Generate'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def generate_pdf_list_for_zip(self, requested_data, pdf_files, error_list):
        '''Generate PDF list to zip'''
        for i in requested_data:
            order_instance = OrderMaster.objects.filter(CU_OD_ID=i).first()

            if order_instance:
                order_invoice_instance = OrderInvoice.objects.filter(
                    OD_INVOE_OD_ID=order_instance.OD_ID).first()

                if order_invoice_instance:
                    od_inv_template_instance = OrderInvoiceTemplate.objects.filter(
                        OD_INVOE_ID=order_invoice_instance.OD_INVOE_ID).first()

                    if od_inv_template_instance:
                        # Use a dynamic filename with the order or invoice number
                        output_filename = f'{i}_invoice.pdf'
                        output_path = os.path.join(
                            settings.MEDIA_ROOT + "/" + str(output_filename))

                        # Convert HTML to PDF and save to output_path
                        pdfkit.from_string(
                            str(od_inv_template_instance.OD_INVOE_TEMP_FILE), output_path
                        )
                        pdf_files.append(
                            {'filename': output_filename, 'path': output_path})
                    else:
                        logger.info(
                            "Template not found!")
                        error_list.append(
                            {"id": i, "Remarks": "Template not found!"})
                else:
                    requested_data = invoice_create_if_not_exist(
                        order_instance, requested_data)
            else:
                error_list.append(
                    {"id": i, "Remarks": "Order ID not found!"})
        return pdf_files, error_list

    def __init__(self):
        self.columns = {"OD_INVOE_INCR_ID": "Invoice ID", "CU_OD_ID": "Order ID",
                        "CUST_NM": "Customer Name", "OD_DATE": "Order Date", "OD_STR_NM": "Store Name",
                        "OD_TL_AMT": "Grand Total", "OD_TX_AMT": "Tax Amount",
                        "OD_SHP_AMT": "Shipping Amount", "OD_NT_AMT": "Net Amount"}
        self.column_type = {
            "OD_INVOE_INCR_ID": "str", "CU_OD_ID": "str", "CUST_NM": "str", "OD_DATE": "Date",
            "OD_STR_NM": "str", "OD_TL_AMT": "price-left", "OD_TX_AMT": "price-left",
            "OD_SHP_AMT": "price-left", "OD_NT_AMT": "price-left"
        }

    @swagger_auto_schema(tags=['Order Invoice'], operation_description="Get Invoice Generation", operation_summary="Get Invoice Generation", manual_parameters=[openapi.Parameter('order_id', in_=openapi.IN_QUERY,
                                                                                                                                                                                  type=openapi.TYPE_STRING)])
    def get(self, request, *args, **kwargs):
        '''Post api for Order Invoice creation'''
        requested_data = str(request.GET.get('order_id', '')).split(',')
        switch_to_list_flag = request.GET.get('stl_flag', '')
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        page = int(page)
        search = request.GET.get('search', '')
        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('search', None)
        copy_request_data.pop('page', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('stl_flag', None)
        copy_request_data.pop('status_filter', None)
        copy_request_data.pop('order_id', None)
        if switch_to_list_flag == '1' or (len(copy_request_data) > 0) or (len(search) > 0 or request.GET.get('ordering') is not None):
            response = invoice_filter(
                int(page), int(page_size), search, copy_request_data, request.GET.get('ordering'))
            response = {
                "total": response[1],
                "page": int(page),
                "page_size": int(page_size),
                "results": response[0],
                "columns": self.columns,
                "column_type": self.column_type
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            error_list = []
            pdf_files = []
            try:
                pdf_files, error_list = self.generate_pdf_list_for_zip(
                    requested_data, pdf_files, error_list)

                # Check if any errors occurred
                if error_list:
                    response_data = {'errors': error_list}
                    stat = status.HTTP_400_BAD_REQUEST
                    return Response(response_data, status=stat)
                else:
                    # Create a zip file
                    zip_filename = 'invoices.zip'
                    zip_filepath = os.path.join(
                        settings.MEDIA_ROOT + "/" + str(zip_filename))

                    with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
                        for pdf in pdf_files:
                            zip_file.write(pdf['path'], pdf['filename'])

                    # Create a response with the zip file
                    with open(zip_filepath, 'rb') as zip_file:
                        response = HttpResponse(
                            zip_file.read(), content_type='application/zip')
                        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'

                    # Clean up: remove individual PDF files and the zip file
                    for pdf in pdf_files:
                        os.remove(pdf['path'])
                    os.remove(zip_filepath)
                    return response
            except Exception:
                return Response({"message": "Something went wrong!!!"}, status=status.HTTP_400_BAD_REQUEST)


class OrderInvoicePicklist(GenericAPIView, ListModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'OD_SHP_ID'

    def dnb_invoice(self, invoice_text, shipment_data, shipment_type):
        '''Generating DNB Invoice'''
        current_datetime = datetime.now()
        created = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(shipment_data, dict):
            shipment_data = [shipment_data]
        for order in shipment_data:
            od_id = order.get("CU_OD_ID")
            order_obj = OrderMaster.objects.filter(CU_OD_ID=od_id).first()
            is_invoice_created = OrderInvoice.objects.filter(
                OD_SHP_ID=order.get("OD_SHP_ID"), OD_INVOE_OD_ID__CU_OD_ID=od_id).first()
            if is_invoice_created is None:
                '''create a new Invoice'''
                custom_invoice_id = create_invoice_code(invoice_text)
            with transaction.atomic():
                orderwise_invoice_details = {
                    "OD_INVOE_OD_ID": order_obj.OD_ID,
                    "OD_INVOE_INCR_ID": custom_invoice_id,
                    "OD_INVOE_GRND_TOT": order.get("OD_NT_AMT"),
                    "OD_INVOE_SHIP_AMT": order.get("OD_SHP_AMT"),
                    "OD_INVOE_SHIP_INCL_TAX": order.get("OD_TX_AMT"),
                    "OD_INVOE_CRT_AT": created,
                    "OD_INVOE_UPDT_AT": created,
                    "OD_INVOE_STATE_ID": 2,
                    "OD_INVOE_STR_ID": order_obj.STR_ID,
                    "OD_INVOE_BILL_ADD_ID": order_obj.orderbillingaddress_set.first().id,
                    "OD_INVOE_SHIP_ADD_ID": order_obj.ordershippingaddress_set.first().id,
                    "OD_SHP_ID": ShipmentMaster.objects.filter(OD_SHP_ID=order.get("OD_SHP_ID")).first().OD_SHP_ID,
                    "ITM_PICK_ID": PicklistMaster.objects.filter(OD_PICK_ID=order.get("OD_PICK_ID")).first().OD_PICK_ID
                }
                serializers = OrderInvoiceSerializer(
                    data=orderwise_invoice_details)
                instance_od_invoice_picklist_ty = OrderInvoicePicklistType.objects.filter(
                    OD_INV_PICK_NM__icontains="Invoice").first()
                data = send_mail_on_order_invoice_create(
                    serializers, custom_invoice_id, order_obj, instance_od_invoice_picklist_ty)
                if data:
                    if shipment_type == "orderwise":
                        for itm in order.get("item"):
                            item_info = Item.objects.filter(
                                AS_ITM_SKU=itm.get("AS_ITM_SKU")).first()
                            order_item_info = OrderItemDetails.objects.filter(
                                OD_ID=order_obj, OD_ITM=item_info).first()
                            item_invoice = {
                                "OD_INVC_ID": serializers.instance,
                                "OD_ID": order_obj,
                                "AS_ITM": item_info,
                                "OD_ITM_ID": order_item_info,
                                "OD_ITM_INVC_PR": order_item_info.OD_ITM_OR_PR
                            }
                            OrderItemInvoince.objects.create(**item_invoice)
                    else:
                        item_info_order = Item.objects.filter(
                            AS_ITM_SKU=order.get("AS_ITM_SKU")).first()
                        order_item_info = OrderItemDetails.objects.filter(
                            OD_ID=order_obj, OD_ITM=item_info_order).first()
                        item_invoice = {
                            "OD_INVC_ID": serializers.instance,
                            "OD_ID": order_obj,
                            "AS_ITM": item_info_order,
                            "OD_ITM_ID": order_item_info,
                            "OD_ITM_INVC_PR": order_item_info.OD_ITM_OR_PR
                        }
                        OrderItemInvoince.objects.create(**item_invoice)

                    order_obj.OD_INVC_NUM = data.get("OD_INVOE_INCR_ID")
                    order_obj.save()
        return data

    def generate_invoice(self, invoice_starts_with, data):
        '''Generating Invoice'''
        invoice_data = False
        order_instance = OrderMaster.objects.filter(
            CU_OD_ID=data.get('CU_OD_ID')).first()
        if order_instance.OMS_OD_STS == "ready_for_pickup":
            check_shipment = ItemShipmentList.objects.filter(
                OD_SHP_ID=data.get("OD_SHP_ID"), OD_ID__CU_OD_ID=data.get('CU_OD_ID'))
            if data.get("OD_TYPE").lower() == "dnb order":
                if data.get("shipment_type") == "orderwise":
                    order_serializers = InvoiceSerializer(
                        check_shipment.first())
                else:
                    order_serializers = ItemShipmentListSerializer(
                        check_shipment, many=True)

                if data.get("shipment_type") == "orderwise" and check_shipment:
                    invoice_data = self.dnb_invoice(
                        invoice_starts_with, order_serializers.data, data.get("shipment_type"))
            elif data.get("OD_TYPE").lower() == "webstore-pickup" or\
                    data.get("OD_TYPE").lower() == "webstore-delivery" or\
                    data.get("OD_TYPE").lower() == "webstore":
                invoice_data = invoice_create_if_not_exist(
                    order_instance, data)
        return invoice_data
    
    def create_pdf(self, data_list):
        order_info = OrderMaster.objects.filter(CU_OD_ID__in=data_list)
        invoice_serializer = InvoicePdfSerializer(order_info, many=True)
        html = ''
        template_info = EmailTemplate.objects.filter(
            ET_DS="Invoice Template").first()
        file_name = 'invoice.html'
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        with open(file_path, 'w') as file:
            file.write(template_info.ET_HTML_TXT)
        with open(file_path, 'r') as file:
            template_content = file.read()
        for data in invoice_serializer.data:
            temp = {}
            temp["OD_INVOE_INCR_ID"] = data.get("OD_INVOE_INCR_ID")
            temp["OD_INVOE_CRT_AT"] = data.get("OD_INVOE_CRT_AT")
            temp["CU_OD_ID"] = data.get("order").get("CU_OD_ID")
            temp["OD_DATE"] = (datetime.strptime(
                data.get("order").get("OD_DATE"), "%Y-%m-%d %H:%M:%S%z")).strftime("%Y-%m-%d")
            temp["OD_CUS_NM"] = data.get("order").get("OD_CUS_NM").title()
            temp["OD_SA_CUST_NM"] = data.get('shipping_address').get("OD_SA_CUST_NM").title() \
                if data.get('shipping_address').get("OD_SA_CUST_NM") else ""
            temp["OD_SA_PH"] = data.get('shipping_address').get("OD_SA_PH")
            temp["OD_SA_ST"] = data.get('shipping_address').get("OD_SA_ST")
            temp["OD_SA_CT"] = data.get('shipping_address').get("OD_SA_CT")
            temp["OD_SA_RGN"] = data.get('shipping_address').get("OD_SA_RGN")
            temp["OD_SA_PIN"] = data.get('shipping_address').get("OD_SA_PIN")
            temp["OD_SA_CTR_CODE"] = data.get('shipping_address').get("OD_SA_CTR_CODE")
            temp["OD_BA_CUST_NM"] = data.get('billing_address').get("OD_BA_CUST_NM").title() \
                if data.get('billing_address').get("OD_BA_CUST_NM") else ""
            temp["OD_BA_PH"] = data.get('billing_address').get("OD_BA_PH")
            temp["OD_BA_ST"] = data.get('billing_address').get("OD_BA_ST")
            temp["OD_BA_CT"] = data.get('billing_address').get("OD_BA_CT")
            temp["OD_BA_RGN"] = data.get('billing_address').get("OD_BA_RGN")
            temp["OD_BA_PIN"] = data.get('billing_address').get("OD_BA_PIN")
            temp["OD_BA_CTR_CODE"] = data.get('billing_address').get("OD_BA_CTR_CODE")
            temp["PT_MD_NM"] = data.get("order").get("PT_MD_NM")
            temp["OD_TL_AMT"] = data.get("order").get("OD_TL_AMT")
            temp["OD_SHP_AMT"] = data.get("order").get("OD_SHP_AMT")
            temp["OD_NT_AMT"] = data.get("order").get("OD_NT_AMT")
            temp["OD_TX_AMT"] = data.get("order").get("OD_TX_AMT")
            temp["OD_PD_AMT"] = data.get("order").get("OD_PD_AMT")
            temp["OD_DIS_AMT"] = data.get("order").get("OD_DIS_AMT")
            temp["amount_in_word"] = data.get("amount_in_word")
            temp["OD_TYPE"] = data.get("order").get("OD_TYPE")
            temp["OD_INST"] = data.get("order").get("OD_INST")
            temp["item_info"] = data.get("item")
            template = Template(template_content)
            rendered_html = template.render(Context(temp))
            html = html + rendered_html
        return html
    
    def invoice_starts_with_code(self, bsn_unit):
        if bsn_unit:
            global_obj = GlobalSetting.objects.filter(
                ID_GB_STNG=bsn_unit).first()
            invoice_starts_with = global_obj.INVO_ID_STRT_WITH
        else:
            invoice_starts_with = "INVC"
        return invoice_starts_with

    def get(self, request, *args, **kwargs):
        '''Get an Invoice Data'''
        shipment_id = self.kwargs.get(self.lookup_url_kwarg)
        shipment_order_ids = ItemShipmentList.objects.filter(OD_SHP_ID = ShipmentMaster.objects.filter(
            OD_SHIP_CODE__iexact=shipment_id).first()).values_list("OD_ID", flat=True)
        shipment_info = OrderMaster.objects.filter(
            OD_ID__in=shipment_order_ids)
        serializer_data = GenerateInvoiceSerializer(shipment_info, many=True).data
        results = {
            "message": "Getting the Invoice Informations",
            "data": serializer_data
        }
        return Response(results, status=status.HTTP_200_OK)

    def update_activity(self, request, order):
        for i in order:
            OrderActivity.objects.create(
                OD_ACT_OD_MA_ID=i,
                OD_ACT_CRT_AT=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                OD_ACT_STATUS="Ready for Pickup",
                OD_ACT_CMT="Invoice Generated",
                OD_ACT_CRT_BY=request.user.get_full_name())
            get_all_serialzied_data = OrderElasticDataSerializer(i).data
            order_save(get_all_serialzied_data,
                    settings.ES_ORDER_INDEX, i.OD_ID)

    def post(self, request, *args, **kwargs):
        ''' Create New Invoice '''
        request_datas = request.data.get("data")
        bsn_unit_id = request.GET.get('ID_BSN_UN', 0)
        serializer_list = []
        order_id_list = []
        response = {}
        for request_data in request_datas:
            order_id = request_data.get("CU_OD_ID")
            order_id_list.append(order_id)
            check_invoice = OrderInvoice.objects.filter(
                OD_INVOE_OD_ID__CU_OD_ID=order_id).first()
            if check_invoice:
                response["message"] = "Only to pass this section."
            else:
                try:
                    bsn_unit = BusinessUnitSetting.objects.filter(
                        ID_BSN_UN=bsn_unit_id).first()
                    invoice_starts_with = self.invoice_starts_with_code(bsn_unit)
                    invoice_data = self.generate_invoice(
                        invoice_starts_with, request_data)
                    if invoice_data:
                        shipment_order_list = ItemShipmentList.objects.filter(
                            OD_SHP_ID = ShipmentMaster.objects.filter(
                            OD_SHP_ID=request_data.get("OD_SHP_ID")).first()).values_list("OD_ID", flat=True)
                        shipment_info = OrderMaster.objects.filter(
                            OD_ID__in=list(set(shipment_order_list)), OMS_OD_STS="ready_for_pickup")
                        serializer_data = GenerateInvoiceSerializer(
                            shipment_info, many=True).data
                        serializer_list.append(serializer_data)
                        self.update_activity(request, shipment_info)
                    else:
                        response["message"] = {"message": "Picking is not Completed."}
                        return Response(response)
                except Exception:
                    response["message"] = {"message": "Something went Wrong."}
                    return Response(response)
        if len(serializer_list) > 0 or len(serializer_list) == 0 :
            pdf_data = self.create_pdf(order_id_list)
            response["data"] = pdf_data
            response["message"] = "Invoice Created Successfully."
            return Response(response)
        else:
            response["message"] = {"message": "Invoice Already Generated."}
        return Response(response)
