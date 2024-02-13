from django.conf import settings
import requests
import logging
import json
import logging
from datetime import datetime
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from celery import shared_task
from basics.notification_views import send_pushnotification
from login_authentication.models import UserDeviceInfo
from order.dnb_utility import send_hold_unhold_notification
from order.order_elastic import order_save
from item_stock.models import ItemInventory
from store.models import InventoryLocation
from order.verify_order_api import common_function_to_save_in_elastic, fetch_comment_status
from taxonomy.taxonomy_magento_integration import magento_login
from order.serializers import OrderElasticDataSerializer, OrderHoldUnholdPreviousStatusSerilaizer
from order.models import OrderActivity, OrderHoldUnholdPreviousStatus, OrderItemDetails, OrderMaster, Reason
from taxonomy.taxonomy_magento_integration import magento_login
from auto_responder.email import send_instant_email
from drf_yasg import openapi

logger = logging.getLogger(__name__)


application_json_key = "application/json"


brn_prams = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'order_id': openapi.Schema(type=openapi.TYPE_ARRAY,
                                   description='Array of Ids',
                                   items=openapi.Items(type=openapi.TYPE_STRING,
                                                       description='CU_OD_ID')),
    }
)
on_hold_message = "on hold"
dnb_order_message = 'dnb order'


def on_action_send_mail(order_type, order_master):
    '''Send mail'''
    try:
        send_instant_email(order_type, order_master)
    except Exception:
        logger.info("Exception occurred")


@shared_task
def send_comment_to_magento_on_hold_void_unhold(magento_order_id, comment, magento_status):
    '''Sending the comments on hold void and unhold'''
    # Add comment to magento
    magento_token, magento_url = magento_login()
    headers = {
        "content-type": "application/json"
    }
    comment_url = f'/rest/default/V1/orders/{magento_order_id}/comments'
    payload = {
        "statusHistory": {
            "comment": comment,
            "is_customer_notified": 0,
            "is_visible_on_front": 0,
            "status": "holded" if str(magento_status) == 'on hold' else str(magento_status)
        }
    }
    requests.post(
        magento_url+comment_url, headers=headers, data=json.dumps(payload), auth=magento_token)


def comment_for_void_or_flag(order_master, comment, request):
    '''Comment for void or flag'''
    if comment:
        if str(order_master.OD_TYPE).lower() != dnb_order_message:
            send_comment_to_magento_on_hold_void_unhold.delay(
                order_master.CH_OD_ID, comment, order_master.OD_STS)
        order_status = fetch_comment_status(order_master, 'New')
        OrderActivity.objects.create(
            OD_ACT_OD_MA_ID=order_master, OD_ACT_CMT=comment, OD_CUST=order_master.OD_CUST, OD_ACT_STATUS=order_status, OD_ACT_CRT_AT=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), OD_ACT_CRT_BY=request.user.get_full_name())


class HoldOrderView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def update_status_in_oms_magento(self, order_master, error_list, od_id, comment):
        '''Update status in oms and magento'''
        if order_master.OD_STS == on_hold_message:
            error_list.append({
                "order_id": od_id,
                "message": "Order is already on hold"
            })
        else:
            previous_status_id = OrderHoldUnholdPreviousStatus.objects.filter(
                OD_HD_UH_OD_ID=order_master.CU_OD_ID)
            if previous_status_id.exists():
                previous_status_id.update(
                    OD_HD_UH_CRNT_STAT=on_hold_message, OD_HD_UH_PREV_STAT=order_master.OD_STS, OD_OMS_STATUS_PREV=order_master.OMS_OD_STS, OD_OMS_STATUS_CRNT=on_hold_message)
            else:
                serializer = OrderHoldUnholdPreviousStatusSerilaizer(
                    data={"OD_HD_UH_OD_ID": order_master.CU_OD_ID, "OD_HD_UH_CRNT_STAT": on_hold_message, "OD_HD_UH_PREV_STAT": order_master.OD_STS, "OD_OMS_STATUS_PREV": order_master.OMS_OD_STS, "OD_OMS_STATUS_CRNT": on_hold_message})
                if serializer.is_valid():
                    serializer.save()
            if str(order_master.OD_TYPE).lower() == dnb_order_message:
                order_master.OD_STS = on_hold_message
                order_master.OMS_OD_STS = on_hold_message
                order_master.save()
                comment_for_void_or_flag(order_master, comment, self.request)
                common_function_to_save_in_elastic(order_master)
                order_type = "Flag_Order"
                on_action_send_mail(order_type, order_master)
            else:
                magento_token, magento_url = magento_login()
                api_url = f'rest/default/V1/orders/{order_master.CH_OD_ID}/hold'
                responses = requests.post(
                    url=magento_url+api_url, auth=magento_token)

                if responses.status_code == 200:
                    order_master.OD_STS = on_hold_message
                    order_master.OMS_OD_STS = on_hold_message
                    order_master.save()
                    comment_for_void_or_flag(
                        order_master, comment, self.request)
                    common_function_to_save_in_elastic(order_master)
                    order_type = "Flag_Order"
                    on_action_send_mail(order_type, order_master)
                else:
                    error_list.append({
                        "order_id": od_id,
                        "message": responses.text
                    })
        return error_list

    def multiple_id(self, order_id, comment):
        error_list = []
        status_list = ['complete', 'canceled']
        for od_id in order_id:
            order_master = OrderMaster.objects.filter(CU_OD_ID=od_id).first()
            if order_master:
                if order_master.OD_STS not in status_list:
                    if not comment:
                        comment = "Order is flagged"
                    error_list = self.update_status_in_oms_magento(
                        order_master, error_list, od_id, comment)
                else:
                    error_list.append({
                        "order_id": od_id,
                        "message": "Order status has to be either pending or processing!"
                    })
            else:
                error_list.append({
                    "order_id": od_id,
                    "message": "Order Id not exists!"
                })
        return error_list

    
    @swagger_auto_schema(tags=['Order'], operation_description="Hold Order", operation_summary="Hold Order", request_body=brn_prams)
    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id', [])
        comment = request.data.get('cmt', '')
        flag = request.data.get('flag', 0)
        response = {}
        if order_id:
            if isinstance(order_id, list):
                error_list = self.multiple_id(order_id, comment)
                response['message'] = "Order Hold Successfull"
                stat = status.HTTP_200_OK
                send_hold_unhold_notification(order_id, type="hold", user=request.user)
                if flag == 1:
                    response['message'] = "Order Flagged Successfully"
                if error_list:
                    stat = status.HTTP_400_BAD_REQUEST
                    response['data'] = error_list
                    response['message'] = "Some Orders Couldn't Be Holded Due to Incorrect Data"
                return Response(response, status=stat)
            else:
                return Response({"message": "Invalid input format!. It must be a list"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Order id is empty!"}, status=status.HTTP_400_BAD_REQUEST)


class UnholdOrderView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def update_unhold_in_oms_magento(self, order_master, previous_status_id, error_list, od_id, comment):
        '''Update unhold in oms and magento'''
        if str(order_master.OD_TYPE).lower() == dnb_order_message:
            order_master.OD_STS = previous_status_id.first().OD_HD_UH_PREV_STAT
            order_master.OMS_OD_STS = previous_status_id.first().OD_OMS_STATUS_PREV
            order_master.save()
            comment_for_void_or_flag(order_master, comment, self.request)
            common_function_to_save_in_elastic(order_master)
        else:
            magento_token, magento_url = magento_login()
            api_url = f'/rest/default/V1/orders/{order_master.CH_OD_ID}/unhold'
            responses = requests.post(
                url=magento_url+api_url, auth=magento_token)
            if responses.status_code == 200:
                order_master.OD_STS = previous_status_id.first().OD_HD_UH_PREV_STAT
                order_master.OMS_OD_STS = previous_status_id.first().OD_OMS_STATUS_PREV
                order_master.save()
                comment_for_void_or_flag(order_master, comment, self.request)
                common_function_to_save_in_elastic(order_master)
            else:
                error_list.append({
                    "order_id": od_id,
                    "message": responses.text
                })
        return error_list

    def multiple_id(self, order_id, comment):
        error_list = []
        if not comment:
            comment = "Order is unflagged"
        for od_id in order_id:
            order_master = OrderMaster.objects.filter(CU_OD_ID=od_id).first()
            if order_master:
                previous_status_id = OrderHoldUnholdPreviousStatus.objects.filter(
                    OD_HD_UH_OD_ID=order_master.CU_OD_ID)
                if previous_status_id.exists():
                    error_list = self.update_unhold_in_oms_magento(
                        order_master, previous_status_id, error_list, od_id, comment)
            else:
                error_list.append({
                    "order_id": od_id,
                    "message": "Order Id not exists!"
                })
        return error_list

    @swagger_auto_schema(tags=['Order'], operation_description="Post Unhold Order", operation_summary="Unhold Order", request_body=brn_prams)
    def post(self, request, *args, **kwargs):
        response = {}
        order_id = request.data.get('order_id')
        comment = request.data.get('cmt', '')
        flag = request.data.get('flag', 0)
        if order_id:
            if isinstance(order_id, list):
                error_list = self.multiple_id(order_id, comment)
                response['message'] = "Order UnHold Successfull"
                stat = status.HTTP_200_OK
                send_hold_unhold_notification(order_id, type="unhold", user=request.user)
                if flag == 1:
                    response['message'] = "Order Unflagged Successfully"
                if error_list:
                    stat = status.HTTP_400_BAD_REQUEST
                    response['data'] = error_list
                    response['message'] = "Some Orders Couldn't Be Updated Due to Incorrect Data"
                return Response(response, status=stat)
            else:
                return Response({"message": "Invalid input format!. Must be in list"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Order ID is Blank"}, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def revert_back_stock_to_inventory(self, order_master):
        '''Revert the stock to inventory on cancel'''
        if order_master.OMS_OD_STS == 'ready_for_pickup':
            item_info_data = OrderItemDetails.objects.filter(
                OD_ID=order_master.OD_ID)
            for item in item_info_data:
                if item:
                    warehouseid = InventoryLocation.objects.filter(
                        ID_STR__MAG_MAGEWORX_STR_ID=order_master.STR_ID).only('ID_WRH').first()
                    if warehouseid:
                        item_stock = ItemInventory.objects.filter(
                            WRH_ID=warehouseid.ID_WRH, STK_ITM_INVTRY_ID__ID_ITM__AS_ITM_SKU__iexact=item.OD_ITM_SKU).first()
                        if item_stock:
                            item_stock.VRTL_STK = item_stock.VRTL_STK - item.OD_ITM_QTY_PKD
                            item_stock.ACTL_STK = item_stock.ACTL_STK + item.OD_ITM_QTY_PKD
                            item_stock.save()

    def cancel_order_in_oms_magento(self, order_master, error_list, id, comment):
        '''Cancel the order in oms and magento'''
        if order_master.OD_STS != 'complete':
            if str(order_master.OD_TYPE).lower() == dnb_order_message:
                self.revert_back_stock_to_inventory(order_master)
                order_master.OD_STS = "canceled"
                order_master.OMS_OD_STS = "void"
                order_master.save()
                comment_for_void_or_flag(order_master, comment, self.request)
                common_function_to_save_in_elastic(order_master)
                order_type = "Cancelled"
                on_action_send_mail(order_type, order_master)
            else:
                magento_token, magento_url = magento_login()
                api_url = f'rest/default/V1/orders/{order_master.CH_OD_ID}/cancel'
                responses = requests.post(
                    url=magento_url+api_url, auth=magento_token)
                try:
                    responses_data = json.loads(
                        responses.text)
                except Exception:
                    responses_data = False
                if responses.status_code == 200 and responses_data == True:
                    self.revert_back_stock_to_inventory(order_master)
                    order_master.OD_STS = "canceled"
                    order_master.OMS_OD_STS = "void"
                    order_master.save()
                    comment_for_void_or_flag(
                        order_master, comment, self.request)
                    common_function_to_save_in_elastic(order_master)
                    order_type = "Cancelled"
                    on_action_send_mail(order_type, order_master)
                else:
                    error_list.append({
                        "order_id": id,
                        "message": responses.text
                    })
        else:
            error_list.append({
                "order_id": id,
                "message": "Order cannot be cancelled!"
            })
        return error_list

    def order_void(self, order_id, error_list, comment):
        if not comment:
            comment = "Order voided"
        for id in order_id:
            order_master = OrderMaster.objects.filter(CU_OD_ID=id).first()
            if order_master:
                if order_master.OD_STS == "canceled":
                    error_list.append({
                        "order_id": id,
                        "message": "Order is already cancelled!"
                    })
                else:
                    error_list = self.cancel_order_in_oms_magento(
                        order_master, error_list, id, comment)
            else:
                error_list.append({
                    "order_id": id,
                    "message": "Order id not exist!"
                })
        return error_list

    @swagger_auto_schema(tags=['Order'], operation_description="Post Cancel Order", operation_summary="Post Cancel Order", request_body=brn_prams)
    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id', [])
        reason_id = int(request.data.get("RN_ID"))
        flag = request.data.get('flag', 0)
        response = {}
        error_list = []
        if order_id:
            if isinstance(order_id, list):
                reason_info = Reason.objects.filter(RN_ID=reason_id).first()
                if reason_info:
                    comment = f"{reason_info.RN_CD}: {reason_info.RN_STD}"
                error_list = self.order_void(order_id, error_list, comment)
                response['message'] = "Order Cancel Successfully"
                stat = status.HTTP_200_OK
                send_hold_unhold_notification(order_id, type="Canceled", user=request.user)
                if flag == 1:
                    response['message'] = "Order Voided Successfully"
                if error_list:
                    response['data'] = error_list
                    response['message'] = "Cancellation Error: Some Orders Couldn't Be Cancelled Due to Incorrect Data"
                return Response(response, status=stat)
            else:
                return Response({"message": "Invalid input format!. Must be in list"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Order id is blank"}, status=status.HTTP_400_BAD_REQUEST)
