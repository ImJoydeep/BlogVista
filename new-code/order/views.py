import os
import logging
import time
from copy import deepcopy
from rest_framework import generics
from django.core.exceptions import ValidationError
from django.template import Template, Context
from django.db import transaction
from django.conf import settings
from auto_responder.models import EmailTemplate
from .common_functions import check_email
from .dnb_utility import create_dnb_order
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework import filters, views
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import ListModelMixin, CreateModelMixin, UpdateModelMixin, DestroyModelMixin
from drf_yasg.utils import swagger_auto_schema
import requests
import json
from .utility import create_magento_order
from rest_framework.views import APIView
from taxonomy.taxonomy_magento_integration import magento_login
from store.models import Location
from .order_filter import order_export, order_list_filter
from order.order_elastic import get_order_by_id, get_order_list_from_elastic
from .models import OrderActivity, OrderMaster, OrderPaymentDetails, OrderShippingAddress, OrderBillingAddress, OrderItemDetails, Customer, Crates, AssociateCrate
from order.order_elastic import delete_order_from_elastic, get_order_list_from_elastic
from drf_yasg import openapi
from .serializers import OrderItemListSerializer, OrderMasterSerializer, OrderBillingAddressSerializer, OrderPaymentDetailsSerializers, OrderShippingAddressSerializer, OrderItemDetailsSerializer, \
    CustomerSerializer, OrderActivitySerilaizer, CratesSerializer, CratesPostSerializer, CratestatusSerializer
from party.models import State, ITUCountry
from taxonomy.models import Color
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from order.crate_filter import crates_filter
from auto_responder.email import send_order_create_email


logger = logging.getLogger(__name__)


application_json_key = "application/json"
invalid_id_key = "Invalid Id"


class GetOrderList(ListModelMixin, GenericAPIView):
    queryset = OrderMaster.objects.filter(is_deleted=False, is_blocked=False)
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrderMasterSerializer
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["CU_OD_ID", "OD_STS"]
    search_fields = ['CU_OD_ID', 'OD_CUS_NM',
                     'OD_CUS_EMAIL', 'OD_DATE', 'STR_ID']
    ordering_fields = '__all__'
    ordering = ['-OD_ID']

    def get_serializer_class(self):
        if self.request.GET.get("view_type") == "orderwise":
            return OrderMasterSerializer
        elif self.request.GET.get("view_type") == "itemwise":
            return OrderItemListSerializer

    def filter_queryset(self):
        if self.request.GET.get("device_type") == "mobile":
            return self.queryset(OMS_OD_STS__in=["ready_to_pick", "new"])

    def __init__(self):
        self.columns_order = {
            "OMS_OD_STS": "Status",
            "flag": "Flag",
            "OD_TYPE": "Order Type",
            "CU_OD_ID": "Order Number",
            "OD_SHIP_CODE": "Picking Id",
            "OD_PICK_BY": "Picker Name",
            "OD_CUS_NM": "Customer Name",
            "OD_CUS_EMAIL": "Customer Email",
            "OD_TOT_QTY": "Quantity",
            "OD_TL_AMT": "Order Amount",
            "OD_DATE": "Order Date & Time",
            "OD_STR_NM": "Store Name",
            "OD_SA_PH": "Phone Number",
            "OD_NT_AMT": "Net Amount",
            "OD_DIS_AMT": "Discount Amount",
            "OD_TX_AMT": "Tax Payment",
            "OD_PD_AMT": "Captured Amount",
            "OD_ITM_AMT_REF": "Refund Amount",
            "PT_MD_NM": "Payment Type",
            "OD_BA_CT": "Billing City",
            "OD_SA_CT": "Shipping City",
            "OD_BA_ST": "Billing Address",
            "OD_SA_ST": "Shipping Address",
            "OD_BA_PIN": "Billing Zipcode",
            "OD_SA_PIN": "Shipping Zipcode",
            "OD_INVC_NUM": "Invoice Number",
            "OD_INST": "Instruction"
        }
        self.column_type_order = {"OMS_OD_STS": "status",
                                  "flag": "order_flag",
                                  "OD_TYPE": "str",
                                  "CU_OD_ID": "str",
                                  "OD_SHIP_CODE": "ship_id",
                                  "OD_PICK_BY": "str",
                                  "OD_CUS_NM": "cust-name",
                                  "OD_CUS_EMAIL": "email",
                                  "OD_SA_PH": "phone",
                                  "OD_TOT_QTY": "qty",
                                  "OD_NT_AMT": "price-left",
                                  "OD_DATE": "Datetime",
                                  "OD_STR_NM": "store",
                                  "OD_TL_AMT": "price-left",
                                  "OD_DIS_AMT": "price-left",
                                  "OD_PD_AMT": "price-left",
                                  "OD_TX_AMT": "price-left",
                                  "OD_ITM_AMT_REF": "price-left",
                                  "PT_MD_NM": "str",
                                  "OD_BA_CT": "str",
                                  "OD_SA_CT": "str",
                                  "OD_BA_ST": "str",
                                  "OD_SA_ST": "str",
                                  "OD_BA_PIN": "int",
                                  "OD_SA_PIN": "int",
                                  "OD_INVC_NUM": "str",
                                  "OD_INST": "str"
                                  }
        self.column_items = {
            "OMS_OD_STS": "Status",
            "OD_TYPE": "Order Type",
            "CU_OD_ID": "Order Number",
            "OD_ITM": "Product Name",
            "OD_CUS_NM": "Customer Name",
            "OD_CUS_EMAIL": "Customer Email",
            "OD_QTY": "Quantity",
            "OD_TL_AMT": "Order Amount",
            "OD_DATE": "Order Date & Time",
            "OD_STR_NM": "Store Name",
            "OD_SA_PH": "Phone Number",
            "OD_NT_AMT": "Net Amount",
            "OD_DIS_AMT": "Discount Amount",
            "OD_TX_AMT": "Tax Payment",
            "OD_PD_AMT": "Captured Amount",
            "OD_ITM_AMT_REF": "Refund Amount",
            "PT_MD_NM": "Payment Type",
            "OD_BA_CT": "Billing City",
            "OD_SA_CT": "Shipping City",
            "OD_BA_ST": "Billing Address",
            "OD_SA_ST": "Shipping Address",
            "OD_BA_PIN": "Billing Zipcode",
            "OD_SA_PIN": "Shipping Zipcode",
            "OD_INVC_NUM": "Invoice Number",
            "OD_SHP_NUM": "Shipping Number",
            "OD_INST": "Instruction"
        }
        self.column_type_item = {
            "OMS_OD_STS": "status",
            "OD_TYPE": "str",
            "CU_OD_ID": "str",
            "OD_ITM": "str",
            "OD_CUS_NM": "cust-name",
            "OD_CUS_EMAIL": "email",
            "OD_SA_PH": "phone",
            "OD_QTY": "qty",
            "OD_NT_AMT": "price-left",
            "OD_DATE": "Datetime",
            "OD_STR_NM": "str",
            "OD_TL_AMT": "price-left",
            "OD_DIS_AMT": "price-left",
            "OD_PD_AMT": "price-left",
            "OD_TX_AMT": "price-left",
            "OD_ITM_AMT_REF": "price-left",
            "PT_MD_NM": "str",
            "OD_BA_CT": "str",
            "OD_SA_CT": "str",
            "OD_BA_ST": "str",
            "OD_SA_ST": "str",
            "OD_BA_PIN": "int",
            "OD_SA_PIN": "int",
            "OD_INVC_NUM": "str",
            "OD_SHP_NUM": "str",
            "OD_INST": "str"
        }

    def order_dashboard_count(self):
        '''Order dashboard count'''
        order_instance = OrderMaster
        total_count = order_instance.objects.all().count()
        new_count = order_instance.objects.filter(OMS_OD_STS='new').count()
        ready_to_pick_count = order_instance.objects.filter(
            OMS_OD_STS='ready_to_pick').count()
        ready_for_pickup_count = order_instance.objects.filter(
            OMS_OD_STS='ready_for_pickup').count()
        void_count = order_instance.objects.filter(OMS_OD_STS='void').count()
        attention_count = order_instance.objects.filter(
            OMS_OD_STS='on hold').count()
        complete_count = order_instance.objects.filter(
            OMS_OD_STS='complete').count()
        return [new_count, ready_to_pick_count, ready_for_pickup_count, void_count, attention_count, complete_count, total_count]

    def get_order_export_data(self, device_flag, response, device_id, current_user, file_name, bsn_unit_id, file_type):
        '''get color export data'''
        if len(response[0]) > 0:
            notification_data = {"device_id": device_id, "message_title": "Order Export", "message_body": "Order Export Successfully Done",
                                 "notification_type": "Order Export", "event_id": None, "user_id": current_user.id, "file_name": file_name, "export_flag": True}
            location = 'export_files/'+str(file_name)
            copy_column_order = deepcopy(self.columns_order)
            del [copy_column_order['flag']]
            if device_id is None or device_id == '':
                device_flag = False
            if len(response[0]) > 1000:
                order_export.delay(response, copy_column_order, bsn_unit_id,
                                   file_name, location, notification_data, device_flag, file_type)
                message = {
                    "message": "Export processing in background. You will get a file URL on Email as well as Notification."}
                stat = status.HTTP_200_OK
            else:
                order_export(response, copy_column_order, bsn_unit_id,
                             file_name, location, notification_data, device_flag, file_type)
                message = {"file_name": file_name}
                stat = status.HTTP_200_OK
        else:
            message = {}
            message['error'] = {"message": 'No Data Found'}
            stat = status.HTTP_404_NOT_FOUND
        return message, stat

    @swagger_auto_schema(tags=['Order'], operation_description="Order List", operation_summary="View Order List")
    def get(self, request, *args, **kwargs):
        response = {}
        queryset = OrderMaster.objects.filter(
            is_deleted=False, is_blocked=False).order_by("-OD_ID")
        search = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        export_flag = self.request.GET.get('export_flag', 0)
        file_type = request.GET.get('type', 'xlsx')
        bsn_unit_id = request.GET.get('ID_BSN_UN', 0)
        device_id = request.GET.get('device_id', None)
        page_size = self.request.GET.get('page_size', queryset.count())
        status_filter = request.GET.get('status_filter', None)
        device = self.request.GET.get('device_type', '')
        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('page', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('search', None)
        copy_request_data.pop('export_flag', None)
        copy_request_data.pop('type', None)
        copy_request_data.pop('ID_BSN_UN', None)
        copy_request_data.pop('device_id', None)
        copy_request_data.pop('status_filter', None)
        copy_request_data.pop('view_type', None)
        copy_request_data.pop('device_type', None)
        if export_flag == '1':
            logger.info("Order export")
            device_flag = True
            current_user = request.user
            file_name = 'Order_Export_Data' + \
                str(time.time())+'.'+str(file_type).lower()
            response = get_order_list_from_elastic(
                settings.ES_ORDER_INDEX, page, page_size, status_filter, search, copy_request_data, device, request.GET.get('ordering'), self.request.user.username)
            message, stat = self.get_order_export_data(device_flag, response, device_id,
                                                       current_user, file_name, bsn_unit_id, file_type)
            return Response(message, status=stat)
        if len(copy_request_data) > 0 or (len(search) > 0 or request.GET.get('ordering') is not None) or status_filter:
            response_data = get_order_list_from_elastic(
                settings.ES_ORDER_INDEX, page, page_size, status_filter, search, copy_request_data, device, request.GET.get('ordering'), self.request.user.username)
            if self.request.GET.get('view_type') == 'orderwise':
                response["columns"] = self.columns_order
                response["column_type"] = self.column_type_order
            elif self.request.GET.get('view_type') == 'itemwise':
                response["columns"] = self.column_items
                response["column_type"] = self.column_type_item
            count_data = self.order_dashboard_count()
            response['new_count'] = count_data[0]
            response['ready_to_pick_count'] = count_data[1]
            response['ready_for_pickup_count'] = count_data[2]
            response['void_count'] = count_data[3]
            response['attention_count'] = count_data[4]
            response['complete_count'] = count_data[5]
            response['total_orders'] = count_data[6]
            response["page"] = int(page)
            response["page_size"] = int(page_size)
            response["total"] = response_data[1]
            response["results"] = response_data[0]
            return Response(response)
        else:
            return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        if self.request.GET.get('view_type') == 'orderwise':
            response["columns"] = self.columns_order
            response["column_type"] = self.column_type_order
        else:
            response["columns"] = self.column_items
            response["column_type"] = self.column_type_item
        count_data = self.order_dashboard_count()
        response.data['new_count'] = count_data[0]
        response.data['ready_to_pick_count'] = count_data[1]
        response.data['ready_for_pickup_count'] = count_data[2]
        response.data['void_count'] = count_data[3]
        response.data['attention_count'] = count_data[4]
        response.data['complete_count'] = count_data[5]
        response['total_orders'] = count_data[6]
        return response

    def check_oms_store_data(self, order_obj):
        magento_id = order_obj.get("STR_ID")
        store_check = Location.objects.filter(id=magento_id).first()
        if store_check and store_check.MAG_MAGEWORX_STR_ID is not None:
            return True
        return False

    def check_email_store(self, magento_customer_info, magento_store_info):
        if magento_customer_info[0] == False or magento_store_info == False:
            return False
        else:
            return True

    def post(self, request, *args, **kwargs):
        back_order_obj = request.data
        logger.info("Create Order Request Data : %s", back_order_obj)
        response = {}

        # Fetch Payment details
        try:
            magento_customer_info = check_email(
                back_order_obj.get("CUST_EMAIL"))

            magento_store_info = self.check_oms_store_data(back_order_obj)
            with transaction.atomic():
                data_check = self.check_email_store(
                    magento_customer_info, magento_store_info)
                if not data_check:
                    business_unit_id = back_order_obj.get("ID_BSN_UN")
                    ip = request.META.get('REMOTE_ADDR', None)
                    customer_email = Customer.objects.filter(
                        CUST_EMAIL=back_order_obj.get("CUST_EMAIL"))
                    if customer_email.exists():
                        customer_info = customer_email.first()
                    else:
                        split_name = back_order_obj["CUST_NAME"].split(" ")
                        temp_cust = {}
                        temp_cust["CUST_FNM"] = split_name[0]
                        temp_cust["CUST_LNM"] = split_name[-1]
                        temp_cust["CUST_EMAIL"] = back_order_obj["CUST_EMAIL"]
                        temp_cust["CUST_PH"] = back_order_obj["CUST_PH"]

                        serializer = CustomerSerializer(data=temp_cust)
                        if serializer.is_valid():
                            customer_info = serializer.save()
                        else:
                            transaction.set_rollback(True)
                            return Response(serializer.errors,
                                            status=status.HTTP_400_BAD_REQUEST)

                    dnb_order = create_dnb_order(
                        back_order_obj, customer_info, ip, business_unit_id, request.user)
                    logger.info(
                        "Magento Order Creation Status: %s", dnb_order)
                    if dnb_order.OD_ID:
                        order_type = "Order Create"
                        order_master = OrderMaster.objects.filter(
                            OD_ID=dnb_order.OD_ID).first()
                        logger.info("Order Master : %s", order_master)
                        send_order_create_email(order_type, order_master)
                    response["message"] = "Successfully Order Placed"
                    response["orderID"] = dnb_order.OD_ID
                    return Response(response, status=status.HTTP_200_OK)

                else:
                    # call magento order api

                    magento_order_status = create_magento_order(
                        back_order_obj)
                    logger.info(
                        "Magento Order Creation Status: %s", magento_order_status)
                    response["message"] = "Successfully Order Placed"
                    return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Magento Order Creation error: %s", e)
            return Response({"error": str(e), "message": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        ''' Order Edit'''
        response = {}
        data = request.data
        custom_order_id = request.GET.get("CU_OD_ID", None)
        if custom_order_id is not None:
            check_order = OrderMaster.objects.filter(
                CU_OD_ID=custom_order_id, OD_STS="pending").first()
            changed_billing_address = OrderBillingAddress.objects.filter(
                OD_BA_OD_ID__OD_ID=check_order.OD_ID).first()
            changed_shipping_address = OrderShippingAddress.objects.filter(
                OD_SA_OD_ID__OD_ID=check_order.OD_ID).first()
            if check_order:
                with transaction.atomic():
                    self.check_order(
                        check_order, data, changed_billing_address, changed_shipping_address)
                    self.item_details(data, check_order)
                response = {
                    "message": "Order updated successfully"
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                response["message"] = "Incorrect Order ID"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            response["message"] = "Order ID is not None"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def item_details(self, data, check_order):
        temp = []
        for item in data.get("items"):
            get_item = OrderItemDetails.objects.filter(
                OD_ID__OD_ID=check_order.OD_ID).first()
            if get_item:
                item_serializer = OrderItemDetailsSerializer(
                    get_item, data=item)
                if item_serializer.is_valid():
                    item_serializer.save()
                else:
                    transaction.set_rollback(True)
                    return Response(item_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return temp

    def check_order(self, check_order, data, changed_billing_address, changed_shipping_address):
        if check_order:
            if changed_billing_address:
                billing_address = {
                    "OD_BA_LN": data.get("OD_BA_LN", ""),
                    "OD_BA_FN": data.get("OD_BA_FN", ""),
                    "OD_BA_EMAIL": data.get("OD_BA_EMAIL", ""),
                    "OD_BA_PH": data.get("OD_BA_PH", ""),
                    "OD_BA_ST": data.get("OD_BA_ST", ""),
                    "OD_BA_CT": data.get("OD_BA_CT", ""),
                    "OD_BA_RGN": data.get("OD_BA_RGN", ""),
                    "OD_BA_CTR_CODE": data.get("OD_BA_CTR_CODE", ""),
                    "OD_BA_PIN": data.get("OD_BA_PIN", ""),
                }
                order_billing_serilaizer = OrderBillingAddressSerializer(
                    changed_billing_address, data=billing_address, partial=True)
                if order_billing_serilaizer.is_valid():
                    order_billing_serilaizer.save()
                else:
                    transaction.set_rollback(True)
                    return Response(order_billing_serilaizer.errors, status=status.HTTP_400_BAD_REQUEST)
            if changed_shipping_address:
                shipping_address = {
                    "OD_SA_LN": data.get("OD_SA_LN", ""),
                    "OD_SA_FN": data.get("OD_SA_FN", ""),
                    "OD_SA_EMAIL": data.get("OD_SA_EMAIL", ""),
                    "OD_SA_PH": data.get("OD_SA_PH", ""),
                    "OD_SA_ST": data.get("OD_SA_ST", ""),
                    "OD_SA_CT": data.get("OD_SA_CT", ""),
                    "OD_SA_RGN": data.get("OD_SA_RGN", ""),
                    "OD_SA_CTR_CODE": data.get("OD_SA_CTR_CODE", ""),
                    "OD_SA_PIN": data.get("OD_SA_PIN", ""),
                }
                order_shipping_serializer = OrderShippingAddressSerializer(
                    changed_shipping_address, data=shipping_address, partial=True)
                if order_shipping_serializer.is_valid():
                    order_shipping_serializer.save()
                else:
                    transaction.set_rollback(True)
                    return Response(order_shipping_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@ swagger_auto_schema(tags=['Order'], operation_description="Order Details", operation_summary="Order Details")
class GetOrderDetails(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrderMasterSerializer

    def order_billing(self, order_id):
        billing_address_queryset = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=order_id).last()
        if billing_address_queryset:
            billing_address_serialize = OrderBillingAddressSerializer(
                billing_address_queryset)
            billing_address_serializer = billing_address_serialize.data
        else:
            billing_address_serializer = {
                "CRT_DT": "",
                "UPDT_DT": "",
                "OD_BA_FN": "",
                "OD_BA_LN": "",
                "OD_BA_EMAIL": "",
                "OD_BA_PH": "",
                "OD_BA_ST": "",
                "OD_BA_CT": "",
                "OD_BA_RGN": "",
                "OD_BA_RGN_CODE": "",
                "OD_BA_CTR_CODE": "",
                "OD_BA_PIN": "",
            }

        return billing_address_serializer

    def order_shipping(self, order_id):
        shipping_address_queryset = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=order_id).last()
        if shipping_address_queryset:
            shipping_address_serialize = OrderShippingAddressSerializer(
                shipping_address_queryset)
            shipping_address_serializer = shipping_address_serialize.data
        else:
            shipping_address_serializer = {
                "CRT_DT": "",
                "UPDT_DT": "",
                "OD_SA_FN": "",
                "OD_SA_LN": "",
                "OD_SA_EMAIL": "",
                "OD_SA_PH": "",
                "OD_SA_ST": "",
                "OD_SA_CT": "",
                "OD_SA_RGN": "",
                "OD_SA_RGN_CODE": "",
                "OD_SA_CTR_CODE": "",
                "OD_SA_PIN": "",
            }

        return shipping_address_serializer

    def retrieve_next_id(self, next_order):
        '''Get the next id'''
        try:
            next_id = next_order.CU_OD_ID
        except Exception as exp:
            logger.info("next_id Exception : %s", exp)
            next_id = None
        return next_id
    
    def remove_duplicate_picksheet_note(self, data_list):
        temp = []
        for data in data_list:
            try:
                if data.get("NT_DETAILS") is not None:
                    if data.get("NT_DETAILS")[0].get("PSN_ID") not in temp:
                        temp.append(data.get("NT_DETAILS")[0].get("PSN_ID"))
                    else:
                        data.pop("NT_DETAILS")
            except Exception as exp:
                logger.info("Exception : %s", exp)

    def order_print(self, order, billing, item, activity, transaction):
        html = ''
        temp = {}
        template_info = EmailTemplate.objects.filter(ET_DS="Demo order Print").first()
        file_name = 'order_print.html'
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        with open(file_path, 'w') as file:
                file.write(template_info.ET_HTML_TXT)
        with open(file_path, 'r') as file:
            template_content = file.read()
        temp["OD_BA_CUST_NM"] = billing.get("OD_BA_CUST_NM")
        temp["OD_BA_CT"] = billing.get("OD_BA_CT")
        temp["OD_BA_PH"] = billing.get("OD_BA_PH")
        temp["OD_BA_CTR_CODE"] = billing.get("OD_BA_CTR_CODE")
        temp["OD_BA_EMAIL"] = billing.get("OD_BA_EMAIL")
        temp["OD_BA_PIN"] = billing.get("OD_BA_PIN")
        temp["OD_BA_ST"] = billing.get("OD_BA_ST")
        temp["CU_OD_ID"] = order.get("CU_OD_ID")
        temp["OD_STR_NM"] = order.get("OD_STR_NM")
        temp["OD_TYPE"] = order.get("OD_TYPE")
        temp["OD_DATE"] = order.get("OD_DATE")
        temp["OMS_OD_STS"] = order.get("OMS_OD_STS")
        temp["OD_DIS_AMT"] = order.get("OD_DIS_AMT")
        temp["OD_NT_AMT"] = order.get("OD_NT_AMT")
        temp["PT_MD_NM"] = order.get("PT_MD_NM")
        temp["OD_TX_AMT"] = order.get("OD_TX_AMT")
        temp["OD_TL_AMT"] = order.get("OD_TL_AMT")
        temp["OD_SHP_AMT"] = order.get("OD_SHP_AMT")
        temp["payment_details"] = transaction.get("OD_PAY_ADDT_INFO")
        temp["items"] = item
        template = Template(template_content)
        rendered_html = template.render(Context(temp))
        html = html + rendered_html
        return html

    def get(self, request, *args, **kwargs):
        # logger.info("Product Get Request data : %s", request.GET)
        CU_OD_ID = request.query_params.get('CU_OD_ID')
        action_type = request.query_params.get('type')
        response = {}
        html = {}
        try:
            if CU_OD_ID is not None:
                order_queryset = OrderMaster.objects.filter(
                    CU_OD_ID=CU_OD_ID).last()
                if order_queryset:
                    prev_order = OrderMaster.objects.filter(
                        OD_ID__lt=order_queryset.OD_ID).last()
                    next_order = OrderMaster.objects.filter(
                        OD_ID__gt=order_queryset.OD_ID).first()
                    next_id = self.retrieve_next_id(next_order)
                    try:
                        prev_id = prev_order.CU_OD_ID
                    except Exception as exp:
                        logger.info("Prev_id Exception : %s", exp)
                        prev_id = None
                    order_details = OrderMasterSerializer(order_queryset)
                    order_item_queryset = OrderItemDetails.objects.filter(
                        OD_ID=order_queryset.OD_ID).order_by("-OD_ITM_ID")
                    item_details_serializer = OrderItemDetailsSerializer(
                        order_item_queryset, many=True)
                    item_details_serializer_data = item_details_serializer.data
                    self.remove_duplicate_picksheet_note(item_details_serializer_data)
                    order_activity = OrderActivitySerilaizer(
                        OrderActivity.objects.filter(OD_ACT_OD_MA_ID=order_queryset).order_by('CRT_DT'), many=True)
                    transaction_details = OrderPaymentDetailsSerializers(
                        OrderPaymentDetails.objects.filter(OD_PAY_OD_id=order_queryset).first())
                    response = {
                        "order_details": order_details.data,
                        "billing_address": self.order_billing(order_id=order_queryset.OD_ID),
                        "shipping_address": self.order_shipping(order_id=order_queryset.OD_ID),
                        "item_details": item_details_serializer_data,
                        "prev_order_id": next_id,
                        "next_order_id": prev_id,
                        "order_activity": order_activity.data,
                        "transaction_detail": transaction_details.data
                    }
                    if action_type == "print":
                        html["data"] = self.order_print(order_details.data, self.order_billing(order_id=order_queryset.OD_ID),
                                                item_details_serializer_data, order_activity.data, transaction_details.data)
                        return Response(html)
                    return Response(response, status=status.HTTP_200_OK)
                else:
                    response["message"] = "Please enter correct id"
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                response["message"] = "Order id does't blank"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response["message"] = str(e)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class OrderDeleteMultipleView(APIView):
    '''Brand multiple status update'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OrderMasterSerializer

    def validate_ids(self, id_list):
        '''order validate id'''
        for each_id in id_list:
            try:
                OrderMaster.objects.get(CU_OD_ID=each_id)
            except (OrderMaster.DoesNotExist, ValidationError):
                return False
        return True

    @swagger_auto_schema(tags=['Order'], operation_description="multiple delete Order",
                         operation_summary="Order multiple delete",
                         request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of Ids',
                                  items=openapi.Items
                                  (type=openapi.TYPE_STRING, description='Order Id'))},
        required=['ids']
    ))
    def delete(self, request):
        '''Order multiple delete'''
        logger.info("Delete Request data : %s", request.data)
        response = {}
        id_list = request.data['ids']
        chk_stat = self.validate_ids(id_list=id_list)
        if chk_stat:
            for each_id in id_list:
                delete_order_from_elastic(settings.ES_ORDER_INDEX, OrderMaster.objects.filter(
                    CU_OD_ID=each_id).first().OD_ID)
                OrderMaster.objects.filter(
                    CU_OD_ID=each_id).delete()
            logger.info("Order Deleted successfully")
            message = "Order Deleted."
            response['message'] = message
            sts = status.HTTP_200_OK

        else:
            response['message'] = invalid_id_key
            sts = status.HTTP_400_BAD_REQUEST

        return Response(response, status=sts)


class InsertState(GenericAPIView):

    def get(self, request, *args, **kwargs):

        magento_token, magento_url = magento_login()
        country = "US"
        magento_country_url = magento_url + \
            f"/rest/default/V1/directory/countries/{country}"
        headers = {"content-type": application_json_key}
        magento_country_info = requests.get(
            url=magento_country_url, headers=headers, auth=magento_token)
        magento_country_info = json.loads(magento_country_info.text)
        if len(magento_country_info.get("available_regions")) > 0:
            state_list = magento_country_info.get("available_regions")
            for each_state in state_list:
                state_name = each_state["name"]
                state_exist_check = State.objects.filter(
                    NM_ST__icontains=state_name, CD_CY_ITU__CD_CY_ITU="US")
                if state_exist_check.exists():
                    state_exist_check.update(MG_ID=each_state["id"])
                else:
                    State.objects.create(NM_ST=state_name, CD_ST=each_state["code"], CD_CY_ITU=ITUCountry.objects.filter(
                        CD_CY_ITU='US').first(), MG_ID=int(each_state["id"]))
            message = "Data inserting"

        else:
            message = "No data found"

        return Response(message, status=status.HTTP_200_OK)


class CratesAPIView(GenericAPIView, CreateModelMixin, ListModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['CRT_CD', 'BR_CD',
                     'DES', 'MTRL_TYPE', 'CLRS__NM_CLR']

    queryset = Crates.objects.all().order_by('-CRT_ID')
    serializer_class = CratesPostSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CratesSerializer
        return CratesPostSerializer

    def __init__(self):
        self.columns = {
            "CRT_STS": "Status",
            "CRT_CD": "Crate Code",
            "BR_CD": "Crate Barcode",
            "STR_ASGN": "Assigned Store",
            "CLRS": "Crate Color",
            "MTRL_TYPE": "Material Type",
            "DES": "Description",
            "CRT_DT": "Created Date & Time",
            "CRT_BY_NM": "Created By",
            "UPDT_DT": "Updated Date & Time",
            "MDF_BY_NM": "Updated By"
            
        }
        self.column_type = {
            "CRT_STS": "status",
            "CRT_CD": "str",
            "BR_CD": "str",
            "STR_ASGN": "str",
            "CLRS": "str",
            "MTRL_TYPE": "str",
            "DES": "str",
            "CRT_DT": "Datetime",
            "CRT_BY_NM": "str",
            "UPDT_DT": "Datetime",
            "MDF_BY_NM": "str"
            
        }

    def get(self, request, *args, **kwargs):
        '''
        search, page_size, page
        '''

        crate_id = self.request.GET.get('CRATE_ID')
        search = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', 10)

        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('search', None)
        copy_request_data.pop('page', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('CRATE_ID', None)

        if crate_id is not None:
            try:
                queryset = Crates.objects.get(CRT_ID=crate_id)
                response_data = CratesSerializer(queryset).data
                response_data.pop('links', None)
            except Crates.DoesNotExist:
                response_data = {"message": "No data found"}
            return Response(response_data)
        if (len(copy_request_data) > 0 and crate_id is None) or (len(search) > 0 or request.GET.get('ordering') is not None):
            response = crates_filter(int(page), int(
                page_size), search, copy_request_data)
            response = {
                "total": response[1],
                "page": int(page),
                "page_size": int(page_size),
                "results": response[0],
                "columns": self.columns,
                "column_type": self.column_type
            }
            return Response(response, status=status.HTTP_200_OK)
        res_data = self.list(request, *args, **kwargs).data
        res_data["page"] = int(page)
        res_data["page_size"] = int(page_size)
        res_data.pop('links', None)
        res_data['columns'] = self.columns
        res_data['column_type'] = self.column_type
        return Response(res_data)

    def post(self, request, *args, **kwargs):

        try:
            data = request.data
            store_ids = data.get('STR_ASGN', [])
            barcode = data.get('BR_CD')
            color = data.get('CLRS')
            state = data.get('CRT_STS')
            crate_code = data.get('CRATE_CD')
            material = data.get('MTRL_TYPE')
            description = data.get('DES', '')
            current_user_id = request.user
            created_by = current_user_id.id
            
            for store_id in store_ids:
                if not Location.objects.filter(id=store_id).exists():
                    return Response({"message":"Store Not Found"}, status=status.HTTP_400_BAD_REQUEST)

            if Crates.objects.filter(CRT_CD__iexact=crate_code).exists():
                response = {
                    "message": f"Crate with Cratecode- {crate_code} already exists",
                    "CRATE_CD": "already exists"
                }
                stat = status.HTTP_409_CONFLICT
            elif Crates.objects.filter(BR_CD__iexact=barcode).exists():
                response = {
                    "message": f"Crate with Barcode- {barcode} already exists",
                    "BR_CD": "already exists"
                }
                stat = status.HTTP_409_CONFLICT
            else:
                crate_data = {
                    'BR_CD': barcode,
                    'CLRS': color,
                    'CRT_STS': state,
                    'CRT_CD': crate_code,
                    'MTRL_TYPE': material,
                    'DES': description,
                    "CRT_BY": created_by,
                }
                crate_serializer = CratesPostSerializer(data=crate_data)
                if crate_serializer.is_valid():
                    crate_instance = crate_serializer.save()

                    for store_id in store_ids:
                        AssociateCrate.objects.create(
                            CRT_ID=crate_instance, STR_ID_id=store_id)
                    response = {"message": "Crate Created Successfully"}
                    stat = status.HTTP_201_CREATED
                else:
                    response = {"message": "Invalid Data"}
                    stat = status.HTTP_400_BAD_REQUEST
            return Response(response, status=stat)

        except Exception as e:
            return Response({"message": repr(e)}, status=status.HTTP_400_BAD_REQUEST)


class CratesUpdateAPIView(GenericAPIView, UpdateModelMixin):
    '''Item Tender Detail'''
    serializer_class = CratesPostSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''retrive method'''
        CRATE_ID = self.kwargs.get('pk')
        query = Crates.objects.filter(
            CRT_ID=CRATE_ID)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj

    def put(self, request, *args, **kwargs):
        '''Update of Crates and Associated Crates'''
        try:
            current_user = request.user
            color = request.data.get("CLRS")
            crate_data = {
                    "CRATE_CD": request.data.get("CRATE_CD"),
                    "BR_CD": request.data.get("BR_CD"),
                    "MTRL_TYPE": request.data.get("MTRL_TYPE"),
                    "CRT_STS": request.data.get("CRT_STS"),
                    "CLRS": color,
                    "DES": request.data.get("DES"),
                    "UPDT_BY":current_user.id
                    }
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=crate_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            store_ids = request.data.get('STR_ASGN', [])
            related_name = 'associatecrate_set'
            related_manager = getattr(instance, related_name)
            related_manager.all().delete()

            for store_id in store_ids:
                AssociateCrate.objects.create(
                    CRT_ID=instance, STR_ID_id=store_id)

            return Response({"message": "Crates Updated Successfully"})
        except Exception as e:
            return Response({"message": repr(e)}, status=status.HTTP_400_BAD_REQUEST)


class CrateStatusUpdate(views.APIView):
    '''crate status update'''

    def validate_ids(self, id_list):
        '''crate validate id'''
        for each_id in id_list:
            try:
                Crates.objects.get(CRT_ID=each_id)
            except (Crates.DoesNotExist, ValidationError):
                return False
        return True

    def put(self, request, *args, **kwargs):
        '''crate multiple status update'''
        id_list = request.data['ids']
        status_val = request.data['status']
        current_user = request.user
        chk_stat = self.validate_ids(id_list=id_list)
        if chk_stat:
            instances = []
            for each_id in id_list:
                obj = Crates.objects.get(CRT_ID=each_id)
                obj.CRT_STS = status_val
                obj.UPDT_BY = current_user
                obj.save()
                instances.append(obj)
            serializer = CratestatusSerializer(instances, many=True)
            return Response(serializer.data, *args, **kwargs)
        else:
            response_data = {}
            response_data["message"] = invalid_id_key
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class CratesDeleteAPIView(GenericAPIView, DestroyModelMixin):

    def validate_ids(self, id):
        '''Crates validate id'''
        for each_id in id:
            try:
                Crates.objects.get(CRT_ID=each_id)
            except (Crates.DoesNotExist, ValidationError):
                return False
        return True

    def delete(self, request):
        '''Crates delete'''
        crate_id = request.data['ids']
        chk_stat = self.validate_ids(id=crate_id)
        if chk_stat:
            for each_id in crate_id:
                str_instance = AssociateCrate.objects.filter(CRT_ID=each_id).all()
                str_instance.delete()
                Crates.objects.filter(CRT_ID=each_id).delete()
            return Response({"message": "Crate Deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            response_data = {}
            response_data["message"] = invalid_id_key
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
