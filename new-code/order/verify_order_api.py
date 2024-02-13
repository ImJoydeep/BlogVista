from datetime import datetime
import os
import json
import requests
import logging
import json
import ast
from pyfcm import FCMNotification
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.mixins import UpdateModelMixin, CreateModelMixin
from rest_framework.generics import GenericAPIView
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accesscontrol.models import OperatorBusinessUnitAssignment
from order.dnb_utility import send_pick_notification
from login_authentication.models import UserDeviceInfo
from order.authorize_payment import capture_payment
from order.generate_picklist import calculate_tot_qty_tot_amt_net_amt_dis_amt, create_next_code
from order.order_invoice import send_mail_on_order_invoice_create, update_item_data_on_invoice,\
    update_order_data_on_invoice
from order.generate_invoice_html import generate_invoice
from order.order_elastic import order_save
from item_stock.models import ItemInventory
from store.models import InventoryLocation, Location

from order.models import ItemPicklist, ItemShipmentList, OrderActivity, OrderCrates, OrderInvoice,\
    OrderInvoicePicklistType, OrderInvoiceTemplate, OrderItemDetails, OrderMaster, OrderPaymentDetails,\
    PicklistMaster, ShipmentMaster
from order.serializers import OrderElasticDataSerializer, OrderInvoiceSerializer,\
    OrderUpdateSerializer, update_comment_on_verify, update_status_on_verify
from product.models.models_item import Item

from order.models import OrderActivity, OrderBillingAddress, OrderItemDetails,\
    OrderMaster, OrderShippingAddress
from order.serializers import OrderUpdateSerializer
from item_stock.models import ItemInventory
from store.models import InventoryLocation
from taxonomy.taxonomy_magento_integration import magento_login

from auto_responder.email import send_instant_email

from celery import shared_task

logger = logging.getLogger(__name__)

push_service = FCMNotification(api_key=settings.FCM_KEY)

application_json_message = "application/json"
order_type_key = 'dnb order'
order_updated_successfully_message = "Order Updated Successfully"
time_response = "%m/%d/%Y, %H:%M:%S"

comment_response = {
    "200": openapi.Response(
        description="Comment Submitted",
    )
}

verify_response = {
    "200": openapi.Response(
        description="Order Verified Successfully",
    )
}


def shipment_items(order):
    '''Create Shipment on Verify Order'''
    try:
        with transaction.atomic():
            picklist_dict = {
                "OD_PICK_NO": create_next_code(name="pick"),
                "OD_ID": order,
                "OD_PICK_TOTAL_AMT": order.OD_NT_AMT
            }
            pick_list = PicklistMaster.objects.create(**picklist_dict)
            order_items = order.orderitemdetails_set.all()
            for item in order_items:
                item_info = Item.objects.filter(
                    AS_ITM_SKU=item.OD_ITM.AS_ITM_SKU).first()
                pick_items_dict = {
                    "ITM_ID": item_info if item_info else None,
                    "OD_PICK_ID": pick_list,
                    "ITM_QTY_REQST": item.OD_ITM_QTY,
                    "ITM_PICK_MRP": item.OD_ITM_NET_AMT,
                    "ITM_OR_MRP": item.OD_ITM_OR_PR
                }
                ItemPicklist.objects.create(**pick_items_dict)
            return True
    except Exception:
        return False


def common_function_to_save_in_elastic(order_instance):
    '''Common function to save data in elastic'''
    serialized_data = OrderElasticDataSerializer(
        order_instance).data
    order_save(serialized_data,
               settings.ES_ORDER_INDEX, order_instance.OD_ID)

class VerifyOrderView(UpdateModelMixin, GenericAPIView):
    '''Verify Order View Class'''
    lookup_url_kwarg = "OD_ID"
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        order_id = self.kwargs.get(self.lookup_url_kwarg)
        query = OrderMaster.objects.filter(
            OD_ID=order_id)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        qfilter = {}
        obj = get_object_or_404(queryset, **qfilter)
        return obj

    def get_serializer_class(self):
        return OrderUpdateSerializer

    @swagger_auto_schema(tags=['Order'], operation_description="Order Verify API", operation_summary="Order Verify API", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={}
    ), responses=verify_response)
    def update(self, request, *args, **kwargs):
        response = super().update(request, args, kwargs)
        order_id = self.kwargs.get(self.lookup_url_kwarg)
        order_info = OrderMaster.objects.filter(OD_ID=order_id).first()
        is_shipped = shipment_items(order_info)
        if order_info and is_shipped:
            serialzied_data = OrderElasticDataSerializer(
                order_info).data
            order_save(serialzied_data,
                       settings.ES_ORDER_INDEX, order_info.OD_ID)
            return response
        else:
            response["message"] = "Error Occured!!!"
            return response

    def put(self, request, *args, **kwargs):
        '''Verify Order View'''
        response = self.update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            data = {
                "message": "Order Verified Successfully",
                "data": response.data,
                "OD_PICK_ID": PicklistMaster.objects.filter(OD_ID=self.get_queryset().first().OD_ID).first().OD_PICK_ID}
            return Response(data, status=status.HTTP_200_OK)
        return response


class VerifyMultipleOrderView(GenericAPIView):
    '''Verify Bulk Orders'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_ids = request.data.get("order_id", [])
        response = {}
        comment = "Order Verified"
        for order in order_ids:
            order_obj = OrderMaster.objects.filter(
                CU_OD_ID__iexact=order).first()
            if order_obj:
                if order_obj.OMS_OD_STS == 'new':
                    order_obj.OD_STS = 'processing'
                    order_obj.OMS_OD_STS = 'ready_to_pick'
                    order_obj.IS_VERIFIED = True
                    order_obj.save()
                order_status = fetch_comment_status(order_obj, 'New')
                headers = {
                    "content-type": "application/json"
                }
                if str(order_obj.OD_TYPE).lower() != order_type_key:
                    update_status_on_verify.delay(order_obj.CH_OD_ID, headers)
                if str(order_obj.OD_TYPE).lower() != order_type_key:
                    update_comment_on_verify.delay(
                        order_obj.CH_OD_ID, order_obj.OD_STS, comment)
                OrderActivity.objects.create(
                    OD_ACT_OD_MA_ID=order_obj, OD_ACT_CMT=comment, OD_CUST=order_obj.OD_CUST,
                    OD_ACT_STATUS=order_status, OD_ACT_CRT_AT=datetime.now().strftime(time_response),
                    OD_ACT_CRT_BY=request.user.get_full_name())
                shipment_items(order_obj)
                serialzied_data = OrderElasticDataSerializer(
                    order_obj).data
                order_save(serialzied_data,
                           settings.ES_ORDER_INDEX, order_obj.OD_ID)
        response["message"] = "Order Verified Successfully."
        return Response(response, status=status.HTTP_200_OK)


def fetch_comment_status(order_instance, order_status):
    '''Fetch comment status'''
    if order_instance.OMS_OD_STS == 'new':
        order_status = 'New'
    if order_instance.OMS_OD_STS == 'ready_to_pick':
        order_status = 'Ready to Pick'
    if order_instance.OMS_OD_STS == 'ready_for_pickup':
        order_status = 'Ready for Pickup'
    if order_instance.OMS_OD_STS == 'void':
        order_status = 'Void'
    if order_instance.OMS_OD_STS == 'on hold':
        order_status = 'Attention'
    if order_instance.OMS_OD_STS == 'complete':
        order_status = 'Completed'
    return order_status


class CommentOrder(UpdateModelMixin, GenericAPIView):
    '''Comment Order Class'''
    lookup_url_kwarg = "OD_ID"
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Order'], operation_description="Order Comment API", operation_summary="Order Comment API", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "cmt": openapi.Schema(type=openapi.TYPE_STRING, description='Comment')
        }
    ), responses=comment_response)
    def put(self, request, *args, **kwargs):
        '''Comment Order'''
        order_id = str(self.kwargs.get(self.lookup_url_kwarg))
        comments = request.data.get('cmt', '')
        order_status = "New"
        if order_id:
            order_instance = OrderMaster.objects.filter(
                CU_OD_ID__iexact=order_id).first()
            if order_instance and comments:
                if str(order_instance.OD_TYPE).lower() != order_type_key:
                    send_comment_to_magento.delay(
                        order_instance.CH_OD_ID, order_instance.OD_STS, comments)
                order_status = fetch_comment_status(
                    order_instance, order_status)
                OrderActivity.objects.create(
                    OD_ACT_OD_MA_ID=order_instance, OD_ACT_CMT=comments, OD_CUST=order_instance.OD_CUST, OD_ACT_STATUS=order_status, OD_ACT_CRT_AT=datetime.now().strftime(time_response), OD_ACT_CRT_BY=request.user.get_full_name())
                common_function_to_save_in_elastic(order_instance)
        return Response({"message": "Comment Submitted"}, status=status.HTTP_200_OK)


order_picking_response = {
    "200": openapi.Response(
        description=order_updated_successfully_message,
    ),
    "400": openapi.Response(
        description="Order id is missing!!!"
    )
}


@shared_task
def send_comment_to_magento(channel_id, order_status, comment):
    '''Send comment to magento'''
    magento_token, magento_url = magento_login()
    # Add comment to magento
    headers = {
        "content-type": application_json_message
    }
    comment_url = f'/rest/default/V1/orders/{channel_id}/comments'
    payload = {
        "statusHistory": {
            "comment": comment,
            "is_customer_notified": 0,
            "is_visible_on_front": 0,
            "status": str(order_status)
        }
    }
    requests.post(
        magento_url+comment_url, headers=headers, data=json.dumps(payload), auth=magento_token)


@shared_task
def change_status_in_magento_for_ready_for_pickup(order_type, channel_id):
    '''Change status in magento on ready for pickup'''
    magento_token, magento_url = magento_login()
    headers = {
        "content-type": application_json_message
    }
    if str(order_type).lower() != order_type_key:
        payload = {
            "entity": {
                "entity_id": channel_id,
                "state": "ready",
                "status": "ready"
            }
        }
        requests.put(
            url=str(magento_url) + '/rest/default/V1/orders/create', headers=headers, data=json.dumps(payload), auth=magento_token)


class CompletePickingView(CreateModelMixin, GenericAPIView):
    '''Complete Picking Order View Class'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def order_item_update(self, item_data, order_instance):
        '''Order item update'''
        for item in item_data:
            item_instance = OrderItemDetails.objects.filter(
                OD_ITM_ID=item.get('OD_ITM_ID')).first()
            if item_instance:
                item_instance.OD_ITM_QTY_PKD = item.get(
                    'OD_ITM_QTY_PKD', item_instance.OD_ITM_QTY_PKD)
                item_instance.OD_ITM_OR_PR = item.get(
                    'OD_ITM_OR_PR', item_instance.OD_ITM_OR_PR)
                item_instance.OD_ITM_NET_AMT = item.get(
                    'ITM_PICK_MRP', item_instance.OD_ITM_NET_AMT)
                item_instance.save()
                warehouse_id = InventoryLocation.objects.filter(
                    ID_STR__MAG_MAGEWORX_STR_ID=order_instance.STR_ID).only('ID_WRH').first()
                if warehouse_id:
                    item_stock = ItemInventory.objects.filter(
                        WRH_ID=warehouse_id.ID_WRH, STK_ITM_INVTRY_ID__ID_ITM__AS_ITM_SKU__iexact=item.get('OD_ITM_SKU')).first()
                    if item_stock:
                        item_stock.VRTL_STK = item_stock.VRTL_STK + item_instance.OD_ITM_QTY_PKD
                        item_stock.ACTL_STK = item_stock.ACTL_STK - item_instance.OD_ITM_QTY_PKD
                        item_stock.save()
        if str(order_instance.OD_TYPE).lower() != order_type_key:
            change_status_in_magento_for_ready_for_pickup.delay(
                order_instance.OD_TYPE, order_instance.CH_OD_ID)

    def update_comment_in_oms_and_magento(self, orderinstance, comment, request):
        '''Update comment in oms and also in magento'''
        if comment:
            order_status = fetch_comment_status(orderinstance, 'New')
            if str(orderinstance.OD_TYPE).lower() != order_type_key:
                send_comment_to_magento.delay(
                    orderinstance.CH_OD_ID, orderinstance.OD_STS, comment)
            OrderActivity.objects.create(
                OD_ACT_OD_MA_ID=orderinstance,
                OD_ACT_CMT=comment,
                OD_CUST=orderinstance.OD_CUST,
                OD_ACT_STATUS=order_status,
                OD_ACT_CRT_AT=datetime.now().strftime(time_response),
                OD_ACT_CRT_BY=request.user.get_full_name())

    def changed_data(self, request, order_instance, requested_data, comment):
        tot_amount = 0.0
        net_amount = 0.0
        sku = []
        for item in requested_data.get("itemfield"):
            if item.get('AS_ITM_SKU') and item.get('AS_ITM_SKU') not in sku :
                tot_amount += float(item.get('ITM_PICK_MRP'))
                net_amount += float(item.get('ITM_PICK_MRP'))
                sku.append(item.get('AS_ITM_SKU'))
        if order_instance.OD_DIS_AMT:
            net_amount += abs(float(order_instance.OD_DIS_AMT))
        if order_instance.OD_SHP_AMT:
            tot_amount += float(order_instance.OD_SHP_AMT)
            net_amount -= float(order_instance.OD_SHP_AMT)
        if order_instance.OD_TX_AMT:
            net_amount -= float(order_instance.OD_TX_AMT)
        order_instance.OD_QTY = len(sku)
        order_instance.OD_TL_AMT = tot_amount
        order_instance.OD_NT_AMT = net_amount
        order_instance.OD_PD_AMT = tot_amount
        order_instance.save()
        payment_update = OrderPaymentDetails.objects.filter(
            OD_PAY_OD=order_instance.OD_ID).first()
        if payment_update:
            if payment_update.OD_PAY_OD.PT_MD_NM != 'Check/Money Order' or payment_update.OD_PAY_OD.PT_MD_NM != '':
                data_list = ast.literal_eval(payment_update.OD_PAY_ADDT_INFO)
                order_payment_json = json.loads(data_list[0])
                order_payment_json.update({"amount": tot_amount})
                new_dict = [json.dumps(order_payment_json)]
                payment_update.OD_PAY_ADDT_INFO = new_dict
                payment_update.save()

    def shipment_update(self, order_instance, requested_data):
        for item in requested_data.get("itemfield"):
            total_quantity = 0
            total_scan_quantity = 0
            item_shipment_change = {
                "ITM_SHP_QTY": item.get("ITM_SHP_QTY"),
                "ITM_SHP_RTN_QTY": item.get("ITM_SHP_RTN_QTY", 0)
            }
            if isinstance(item.get("ITM_SHP_GRN_QTY"), int):
                item_shipment_change["ITM_SHP_GRN_QTY"] = item["ITM_SHP_GRN_QTY"]
            if isinstance(item.get("ITM_SHP_SORT"), int):
                item_shipment_change["ITM_SHP_SORT"] = item["ITM_SHP_SORT"]
            ItemShipmentList.objects.filter(
                OD_ID__CU_OD_ID__iexact=order_instance.CU_OD_ID, OD_ITM_ID_id=item.get("OD_ITM_ID"), ITM_SHP_ID=item.get("ITM_SHP_ID"), ITM_ID__AS_ITM_SKU=item.get('AS_ITM_SKU'), OD_SHP_ID_id=requested_data.get('OD_SHP_ID')).update(**item_shipment_change)
            total_quantity += item.get("OD_ITM_QTY")
            total_scan_quantity += item.get("ITM_SHP_GRN_QTY")
            pick_list = {
                "ITM_QTY_REQST": total_quantity,
                "ITM_QTY_PCKD": total_scan_quantity,
                "ITM_QTY_SORT": item.get("ITM_SHP_SORT"),
                "ITM_PICK_MRP": item.get("ITM_PICK_MRP"),
                "ITM_OR_MRP": item.get('ITM_OR_MRP')
            }
            ItemPicklist.objects.filter(
                ITM_PICK_ID=item.get("ITM_PICK_ID"), ITM_ID__AS_ITM_SKU=item.get('AS_ITM_SKU')).update(**pick_list)
            OrderItemDetails.objects.filter(
                OD_ITM__AS_ITM_SKU=item.get('AS_ITM_SKU'), OD_ITM_ID=item.get('OD_ITM_ID')).update(OD_ITM_QTY_PKD=item.get('OD_ITM_QTY_PKD'))

        ShipmentMaster.objects.filter(
            OD_SHP_ID=requested_data.get("OD_SHP_ID")).update(
            OD_SHP_ACT_QTY=len(requested_data.get("itemfield")),
            OD_SHP_STS='Picking-Completed')
        tot_qty, new_net_amt, new_total_amt, new_tax_amt, new_disc_amt, order_id, multiple_store_name = calculate_tot_qty_tot_amt_net_amt_dis_amt(
            requested_data.get("OD_SHP_ID"))
        logger.info("Total qty: %s, net amount : %s, total amount : %s, tax amount : %s, discount amount : %s, order_id : %s, store name: %s",
                    tot_qty, new_net_amt, new_total_amt, new_tax_amt, new_disc_amt, order_id, multiple_store_name)
        ShipmentMaster.objects.filter(
            OD_SHP_ID=requested_data.get("OD_SHP_ID")).update(TOT_PICK_QTY=tot_qty, TOT_AMT=new_total_amt, TOT_NET_AMT=new_net_amt, TOT_TAX_AMT=new_tax_amt, TOT_DIS_AMT=new_disc_amt)

    def create_ready_for_pickup(self, order):
        items = OrderItemDetails.objects.filter(OD_ID=order)
        item_json = []
        for item in items:
            temp = {}
            temp["order_item_id"] = item.OD_ITM_ID_ITM 
            temp["qty"] = item.OD_ITM_QTY_PKD
            item_json.append(temp)
        magento_token, magento_url = magento_login()
        shipment_url = f"/rest/default/V1/order/{order.CH_OD_ID}/ship"
        headers = {
        "content-type": application_json_message
        }
        payload = {
            "items": item_json,
            "arguments": {
                "extension_attributes": {
                }
            }
        }
        shipment_response = requests.post(
        url=str(magento_url) + shipment_url, headers=headers, data=json.dumps(payload), auth=magento_token)
        if shipment_response.status_code == 200:
            return True
        elif shipment_response == 401:
            logger.info(f"Error in shipment: {shipment_response.text}")
            return False
        else:
            return False

    def after_capturing(self, request, item_data, order_instance, requested_data, comment):
        response = {}
        self.order_item_update(item_data, order_instance)
        order_instance.OMS_OD_STS = "ready_for_pickup"
        order_instance.OD_STS = "ready"
        order_instance.save()
        self.update_comment_in_oms_and_magento(
            order_instance, comment, request)
        self.shipment_update(order_instance, requested_data)
        response['message'] = order_updated_successfully_message
        common_function_to_save_in_elastic(order_instance)
        send_pick_notification(order_instance, type="Ready for Pick-up Stage", user=request.user)
        order_type = "Ready_for_Pickup"
        self.create_ready_for_pickup(order_instance)
        try:
            send_instant_email(order_type, order_instance)
        except Exception as e:
            logger.info("Email send exception : %s", e)
        return response

    @swagger_auto_schema(tags=['Order'], operation_description="Complete Picking", operation_summary="Complete Picking", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "CU_OD_ID": openapi.Schema(type=openapi.TYPE_STRING, description='Order Id'),
            "cmt": openapi.Schema(type=openapi.TYPE_STRING, description='Comment'),
            "is_item_change": openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Flag for changes in item (true/false)'),
            "OD_DIS_AMT": openapi.Schema(type=openapi.TYPE_NUMBER, description='Discount Amount'),
            "OD_NT_AMT": openapi.Schema(type=openapi.TYPE_NUMBER, description='Subtotal Amount'),
            "OD_TX_AMT": openapi.Schema(type=openapi.TYPE_NUMBER, description='Tax Amount'),
            "OD_TL_AMT": openapi.Schema(type=openapi.TYPE_NUMBER, description='Total Amount'),
            "item_data": openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of item list',
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                "OD_ITM_ID": openapi.Schema(type=openapi.TYPE_INTEGER, description='Order Item Id'),
                                                "OD_ITM_QTY_PKD": openapi.Schema(type=openapi.TYPE_NUMBER, description='Quantity Picked'),
                                                "OD_ITM_OR_PR": openapi.Schema(type=openapi.TYPE_NUMBER, description='Price per item'),
                                                "OD_ITM_NET_AMT": openapi.Schema(type=openapi.TYPE_NUMBER, description='Net Amount'),
                                                "AS_ITM_SKU": openapi.Schema(type=openapi.TYPE_STRING, description='Item SKU')
                                            }
                                        )
                                        )
        }
    ), responses=order_picking_response)
    def post(self, request, *args, **kwargs):
        '''Complete picking View'''
        data_list = request.data
        response = {}
        comment = request.data.get('cmt', '')
        if not comment:
            comment = "Picking Completed"
        for requested_data in data_list["item_detail_field"]:
            order_id = requested_data.get('CU_OD_ID', [])
            item_data = requested_data.get('itemfield', [])
            if order_id:
                order_instance = OrderMaster.objects.filter(
                    CU_OD_ID__iexact=order_id, OMS_OD_STS="ready_to_pick").first()
                if order_instance:
                    with transaction.atomic():
                        self.changed_data(request, order_instance,
                            requested_data, comment)
                    capture_status = capture_payment(order_instance.CU_OD_ID)
                    if (capture_status.get("status") and order_instance.OD_TYPE != "DNB Order") or\
                        order_instance.OD_TYPE == "DNB Order" or order_instance.PT_MD_NM == 'Check/Money Order':
                        response = self.after_capturing(request, item_data, order_instance, requested_data, comment)
                        stat = status.HTTP_200_OK
                        response["message"] = response.get("message")
                        return Response(response, status=stat)
                    else:
                        response["message"] = capture_status.get("message")
                        stat = status.HTTP_400_BAD_REQUEST
                        return Response(response, status=stat)
                else:
                    response['message'] = "Order ID does not exist or status not in ready to pick state!"
                    stat = status.HTTP_400_BAD_REQUEST
                    return Response(response, status=stat)
            
            response['message'] = "Order ID is missing!!!"
            stat = status.HTTP_400_BAD_REQUEST
        return Response(response, status=stat)


@shared_task
def update_stock_in_magento_for_complete_order(channel_id):
    '''Update stock in Magento for complete order'''
    magento_token, magento_url = magento_login()
    headers = {
        "content-type": application_json_message
    }
    payload = {
        "entity": {
            "entity_id": channel_id,
            "state": "complete",
            "status": "complete"
        }
    }
    requests.put(
        url=str(magento_url) + '/rest/default/V1/orders/create', headers=headers, data=json.dumps(payload), auth=magento_token)


complete_order_response = {
    "200": openapi.Response(
        description="Order Completed Successfully",
    ),
    "400": openapi.Response(
        description="Please provide an order ID"
    )
}


class CompleteOrderView(CompletePickingView, CreateModelMixin, GenericAPIView):
    '''Verify Order View Class'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def retrieve_source_list(self, item_stock, items):
        '''Retrieve source list'''
        if item_stock:
            item_stock.STK_QTY = item_stock.STK_QTY - items.OD_ITM_QTY_PKD
            item_stock.VRTL_STK = item_stock.VRTL_STK - items.OD_ITM_QTY_PKD
            item_stock.save()

    def update_inventory(self, item_datas, order_instance):
        '''Update inventory'''
        for items in item_datas:
            if items:
                warehouseids = InventoryLocation.objects.filter(
                    ID_STR__MAG_MAGEWORX_STR_ID=order_instance.STR_ID).only('ID_WRH').first()
                if warehouseids:
                    item_stock = ItemInventory.objects.filter(
                        WRH_ID=warehouseids.ID_WRH, STK_ITM_INVTRY_ID__ID_ITM__AS_ITM_SKU__iexact=items.OD_ITM_SKU).first()
                    self.retrieve_source_list(
                        item_stock, items)
        update_stock_in_magento_for_complete_order.delay(
            order_instance.CH_OD_ID)
        
    def release_crate(self, order):
        crate_list = OrderCrates.objects.filter(OD_ID=order)
        for crate in crate_list:
            if crate.OD_ID.OD_STS=="complete":
                crate.delete()

    @swagger_auto_schema(tags=['Order'], operation_description="Complete Order", operation_summary="Complete Order", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "CU_OD_ID": openapi.Schema(type=openapi.TYPE_STRING, description='Order Id'),
            "cmt": openapi.Schema(type=openapi.TYPE_STRING, description='Comment')
        }
    ), responses=complete_order_response)
    def post(self, request, *args, **kwargs):
        '''Complete order View'''
        order_id = request.data.get('CU_OD_ID', None)
        comment = request.data.get('cmt', '')
        response = {}
        if order_id:
            order_instance = OrderMaster.objects.filter(
                CU_OD_ID__iexact=order_id).first()
            if order_instance and order_instance.OMS_OD_STS == "ready_for_pickup":
                order_instance.OD_STS = "complete"
                order_instance.OMS_OD_STS = "complete"
                order_instance.save()
                item_datas = OrderItemDetails.objects.filter(
                    OD_ID=order_instance.OD_ID)
                self.update_inventory(item_datas, order_instance)
                self.update_comment_in_oms_and_magento(
                    order_instance, comment, request)
                self.release_crate(order_instance)
                common_function_to_save_in_elastic(order_instance)
                response['message'] = "Order Completed Successfully"
                stat = status.HTTP_200_OK
            else:
                response['message'] = "Sorry, we couldn't find your order or it's not in the 'Ready for Pickup' state."
                stat = status.HTTP_400_BAD_REQUEST
        else:
            response['message'] = "Please provide an order ID"
            stat = status.HTTP_400_BAD_REQUEST
        return Response(response, status=stat)
