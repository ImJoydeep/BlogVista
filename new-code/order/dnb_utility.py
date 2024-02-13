import calendar
import requests
import logging
from pyfcm import FCMNotification
from datetime import datetime
from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import status
from basics.notification_views import send_pushnotification
from accesscontrol.models import OperatorBusinessUnitAssignment
from basics.models import NotificationLog
from login_authentication.models import UserDeviceInfo
from globalsettings.models import BusinessUnitSetting
from store.models import Location
from order.order_elastic import order_save
from order.serializers import OrderElasticDataSerializer
from order.models import Customer, OrderActivity, OrderBillingAddress, OrderItemDetails, OrderMaster, OrderShippingAddress, PicklistMaster
from taxonomy.taxonomy_magento_integration import magento_login
from product.models import Item
from item_stock.models import ItemInventory
logger = logging.getLogger(__name__)
push_service = FCMNotification(api_key=settings.FCM_KEY)



def generate_master_order_id(business_unit_id):
    try:
        global_setting_check = BusinessUnitSetting.objects.filter(
            ID_BSN_UN=business_unit_id).first()
        if global_setting_check:
            first_word = GlobalSetting.objects.filter(
                ID_GB_STNG=global_setting_check.ID_GB_STNG).first()
        dnb_prifix = first_word.OD_ID_STRT_WITH
    except Exception:
        dnb_prifix = "DB"
    last_order = OrderMaster.objects.filter(OD_TYPE="DNB Order").last()
    if last_order:
        order_id_no = last_order.OD_ID
    else:
        order_id_no = int(1)
    cust_order_id = str(dnb_prifix)+str(order_id_no).zfill(5)
    return cust_order_id


def get_store_name(store_id):
    if store_id != 0 and store_id is not None:
        store_name = Location.objects.filter(
            MAG_MAGEWORX_STR_ID=store_id)
        if store_name.exists():
            return store_name.first().MAG_MAGEWORX_STR_NM
        else:
            return ""
    else:
        return ""


def create_dnb_order(order_data, customer_id, ip, business_unit_data, user=None):

    user_name = user.get_full_name() if user else "Admin"

    business_unit_id = BusinessUnitSetting.objects.filter(
        ID_BSN_UN=business_unit_data).first()
    existing_order = OrderMaster.objects.filter(
        CU_OD_ID__iexact=order_data.get("CU_OD_ID")).first()
    with transaction.atomic():
        master_order = {
            "CU_OD_ID": order_data.get("CU_OD_ID") if "import_flag" in order_data else generate_master_order_id(business_unit_id),
            "OD_DATE": datetime.strptime(order_data.get("OD_DATE"), "%Y-%m-%d %H:%M:%S").astimezone(),
            "OD_STR_NM": get_store_name(order_data.get("OD_STR_ID")),
            "STR_ID": order_data.get("OD_STR_ID"),
            "OD_STS": "pending",
            "OD_CUS_NM": order_data.get("CUST_NAME"),
            "OD_CUS_EMAIL": order_data.get("CUST_EMAIL"),
            "PT_MD_NM": order_data.get("PT_MD_NM"),
            "OD_CUR_COD": "USD",
            "OD_IP_ADDR": ip,
            "OD_PAY_STS": order_data.get("OD_PAY_TRANS_ID", ""),
            "OD_TYPE": "DNB Order",
            "OD_QTY": order_data.get("OD_QTY"),
            "OD_SHP_AMT": float(order_data.get("OD_SHP_AMT", 0.0)),
            "OD_TL_AMT": float(order_data.get("OD_TL_AMT", 0.0)),
            "OD_NT_AMT": float(order_data.get("OD_NT_AMT", 0.0)),
            "OD_DIS_AMT": float(order_data.get("OD_DIS_AMT", 0.0)),
            "OD_PD_AMT": float(order_data.get("OD_TL_AMT", 0.0)),
            "OD_TX_AMT": float(order_data.get("OD_TX_AMT", 0.0)),
            "OD_INST": order_data.get("OD_INST", ""),
            "OD_CUST": customer_id,
            "OD_PROT_ID": "",
            "OD_INVC_NUM": "",
            "OD_SHP_NUM": "",
            "OD_SHIP_DESC": "",
            "IS_VERIFIED": False,
            "OMS_OD_STS": 'new'
        }
        if existing_order:
            changed_order_data = {
                "CU_OD_ID": existing_order.CU_OD_ID,
                "OD_DATE": datetime.strptime(order_data.get("OD_DATE"), "%Y-%m-%d %H:%M:%S").astimezone(),
                "OD_STS": existing_order.OD_STS,
                "OD_TYPE": existing_order.OD_TYPE,
                "IS_VERIFIED": existing_order.IS_VERIFIED,
                "OMS_OD_STS": existing_order.OMS_OD_STS
            }
            logger.info("change data in magento pull: %s", changed_order_data)

        new_order = OrderMaster.objects.create(**master_order)
        if new_order:
            cust_billling = {
                "OD_BA_LN": order_data.get("OD_BA_LN"),
                "OD_BA_MN": "",
                "OD_BA_FN": order_data.get("OD_BA_FN"),
                "OD_BA_EMAIL": order_data.get("OD_BA_EMAIL"),
                "OD_BA_PH": order_data.get("OD_BA_PH"),
                "OD_BA_ST": order_data.get("OD_BA_ST"),
                "OD_BA_CT": order_data.get("OD_BA_CT"),
                "OD_BA_RGN": order_data.get("OD_BA_RGN"),
                "OD_BA_RGN_CODE": "",
                "OD_BA_CTR_CODE": order_data.get("OD_BA_CTR_CODE"),
                "OD_BA_PIN": order_data.get("OD_BA_PIN"),
                "OD_CUST": customer_id,
                "OD_BA_OD_ID": new_order
            }
            OrderBillingAddress.objects.create(**cust_billling)
            cust_shipping = generate_shipping_data(
                order_data, customer_id, new_order)
            OrderShippingAddress.objects.create(**cust_shipping)
            items = order_data["items"]
            for item in items:
                item_instance = Item.objects.filter(
                    AS_ITM_SKU__icontains=item.get("AS_ITM_SKU")).first()
                if item_instance:
                    order_item = {
                        "OD_ID": new_order,
                        "OD_ITM_QTY": item.get("OD_ITM_QTY"),
                        "OD_ITM": item_instance,
                        "OD_ITM_NM": item_instance.NM_ITM,
                        "OD_ITM_OR_PR": item.get("OD_ITM_OR_PR"),
                        "OD_ITM_CRT_DT": "",
                        "OD_ITM_DSC_AMT": item.get("OD_ITM_DSC_AMT"),
                        "OD_ITM_TAX_AMT": item.get("OD_ITM_TAX_AMT"),
                        "OD_ITM_TOTL_AMT": item.get("OD_ITM_TOTL_AMT"),
                        "OD_ITM_INVC": "",
                        "OD_ITM_UPDT_DT": "",
                        "OD_ITM_SKU": item_instance.AS_ITM_SKU,
                        "OD_ITM_NET_AMT": item.get("OD_ITM_NET_AMT")
                    }

                    OrderItemDetails.objects.create(**order_item)
                    inventory = ItemInventory.objects.filter(
                        STK_ITM_INVTRY_ID__ID_ITM__AS_ITM_SKU=item.get("AS_ITM_SKU")).first()
                    inventory.ACTL_STK = inventory.ACTL_STK - \
                        float(order_data.get("OD_QTY"))
                    inventory.VRTL_STK = float(order_data.get("OD_QTY"))
                    inventory.save()
        OrderActivity.objects.create(
            OD_ACT_OD_MA_ID=new_order,
            OD_ACT_CRT_AT=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            OD_CUST=customer_id,
            OD_ACT_STATUS="New",
            OD_ACT_CMT="Order Created",
            OD_ACT_CRT_BY=user_name)
    notify_users(new_order, type="order")
    get_all_serialzied_data = OrderElasticDataSerializer(
        new_order).data
    order_save(get_all_serialzied_data,
               settings.ES_ORDER_INDEX, new_order.OD_ID)

    return new_order


def validate_null(data):
    if data is None:
        data = ''
    return data


def generate_shipping_data(order_data, customer_id, new_order):
    cust_shipping = {
        "OD_SA_FN": order_data.get("OD_SA_FN") if order_data.get("OD_SA_FN") else order_data.get("OD_BA_FN"),
        "OD_SA_MN": "",
        "OD_SA_LN": order_data.get("OD_SA_LN") if order_data.get("OD_SA_LN") else order_data.get("OD_BA_LN"),
        "OD_SA_EMAIL": order_data.get("OD_SA_EMAIL") if order_data.get("OD_SA_LN") else order_data.get("OD_BA_LN"),
        "OD_SA_PH": order_data.get("OD_SA_PH") if order_data.get("OD_SA_LN") else order_data.get("OD_BA_LN"),
        "OD_SA_ST": order_data.get("OD_SA_ST") if order_data.get("OD_SA_LN") else order_data.get("OD_BA_LN"),
        "OD_SA_CT": order_data.get("OD_SA_CT") if order_data.get("OD_SA_LN") else order_data.get("OD_BA_LN"),
        "OD_SA_RGN": order_data.get("OD_SA_RGN") if order_data.get("OD_SA_LN") else order_data.get("OD_BA_LN"),
        "OD_SA_RGN_CODE": "",
        "OD_SA_CTR_CODE": order_data.get("OD_SA_CTR_CODE") if order_data.get("OD_SA_CTR_CODE") else order_data.get(
            "OD_BA_CTR_CODE"),
        "OD_SA_PIN": order_data.get("OD_SA_PIN") if order_data.get("OD_SA_PIN") else order_data.get("OD_BA_PIN"),
        "OD_CUST": customer_id,
        "OD_SA_OD_ID": new_order
    }
    return cust_shipping


def calculate_sla(sla):
    week = {}
    delivery_date = ''
    to_day = datetime.now()
    for i in range(sla):
        day = calendar.day_name[(
            to_day + datetime.timedelta(days=i+1)).weekday()]
        week[day] = week[day] + 1 if day in week else 1
    if 'Sunday' in week:
        no_of_sunday = week['Sunday']
        total_no_days_delivery = sla + no_of_sunday
        delivery_date = to_day+datetime.timedelta(days=total_no_days_delivery)
        month = delivery_date.strftime("%B")
        date_num = delivery_date.strftime("%d")
    else:
        total_no_days_delivery = sla
        delivery_date = to_day + \
            datetime.timedelta(days=total_no_days_delivery)
        month = delivery_date.strftime("%B")
        date_num = delivery_date.strftime("%d")

    return month, date_num

def find_store_admin(store_id):
    user_list = []
    store_info = Location.objects.filter(MAG_MAGEWORX_STR_ID=store_id).first()
    usernmae_list = OperatorBusinessUnitAssignment.objects.filter(
        ID_LCN=store_info.id).values_list("ID_OPR__NM_USR", flat=True)
    user_datas = User.objects.filter(username__in=usernmae_list)
    for user in user_datas:
        if user.is_superuser:
            user_list.append(user)
    return user_list

def send_pick_notification(order, type=None, user=None):
    if type == "Picking Stage":
        message_title = "Order in Picking Stage"
        message_body = "Picking"
    elif type == "Ready for Pick-up Stage":
        message_title = "Order in Ready for Pick-up Stage"
        message_body = "Picked"
    
    check_order_master = OrderMaster.objects.filter(CU_OD_ID=order.CU_OD_ID).first()
    if check_order_master:
        store_admin_lists = find_store_admin(check_order_master.STR_ID)
        for admin in store_admin_lists:
            notification_data = {"device_id": "", "message_title": message_title,
                            "message_body": f"Order No: {check_order_master.CU_OD_ID} {message_body} by {user.username.title()}",
                            "notification_type": f"{type}_order", "event_id": None,
                            "user_id": admin.id, "file_name": None, "export_flag": False}
            send_pushnotification(**notification_data)
            device_list = UserDeviceInfo.objects.filter(USR_ID=admin)
            if device_list:
                for device in device_list:
                    notification_info = NotificationLog.objects.filter(ID_USR=admin.id).last()
                    notification_pick_data = {"TYP_NTF": f"{type}_order", "ID_EVNT": None,
                                 "MSG_NTF": f"Order No: {check_order_master.CU_OD_ID} {message_body} by {user.username.title()}",
                                 "TL_NTF": message_title, "ID_DVS": device.DVS_TOKEN,  "ID_USR": device.USR_ID.id,
                                 "NTF_EPRT": False, "NTF_FL_NM": None, "DVC_TYPE": "web", "ST_NTF": "A",
                                 "ID_NTF": notification_info.ID_NTF}
                    push_service.notify_single_device(
                                registration_id=device.DVS_TOKEN,
                                message_title=message_title,
                                message_body=f"Order No: {check_order_master.CU_OD_ID} {message_body} by {user.username.title()}",
                                data_message=notification_pick_data)
                    
def notify_users(order, type=None):
    if type == "order":
        message_title = "New Order Recieved"
        message_body = f"Order No: {order.CU_OD_ID} Customer name: {order.OD_CUS_NM} Total Amount: {order.OD_TL_AMT}"
        notification_type = "new_order"
    store_info = Location.objects.filter(MAG_MAGEWORX_STR_ID= order.STR_ID).first()
    operator_username_list = OperatorBusinessUnitAssignment.objects.filter(
        ID_LCN=store_info.id).values_list("ID_OPR__NM_USR", flat=True)
    user_datas = User.objects.filter(username__in=operator_username_list)
    for user_data in user_datas:
        notification_data = {"device_id": "", "message_title": message_title,
                            "message_body": message_body,
                            "notification_type": notification_type, "event_id": None,
                            "user_id": user_data.id, "file_name": None, "export_flag": False}
        send_pushnotification(**notification_data)
        device_list = UserDeviceInfo.objects.filter(USR_ID=user_data)
        if device_list:
            for device in device_list:
                notification_info = NotificationLog.objects.filter(ID_USR=user_data.id).last()
                send_fcm_notification = {"TYP_NTF": notification_type, "ID_EVNT": None,
                                 "MSG_NTF": message_body,
                                 "TL_NTF": message_title, "ID_DVS": device.DVS_TOKEN,  "ID_USR": device.USR_ID.id,
                                 "NTF_EPRT": False, "NTF_FL_NM": None, "DVC_TYPE": "web", "ST_NTF": "A",
                                 "ID_NTF": notification_info.ID_NTF}
                push_service.notify_single_device(
                    registration_id=device.DVS_TOKEN,
                    message_title=message_title,
                    message_body=message_body,
                    data_message=send_fcm_notification)
        

def send_hold_unhold_notification(order_ids, type=None, user=None):
        try:
            for order_id in order_ids:
                order_master = OrderMaster.objects.filter(CU_OD_ID=order_id).first()
                if order_master:
                    store_admin_list = find_store_admin(order_master.STR_ID)
                    picking_person = PicklistMaster.objects.filter(OD_ID=order_master,
                                                                   OD_ID__OMS_OD_STS__in=["ready_to_pick", "on hold"]).first()
                    if picking_person:
                        picking_person = picking_person.OD_PICK_BY
                        store_admin_list.append(picking_person)
                    elif order_master.OMS_OD_STS != "void":
                        store_info = Location.objects.filter(MAG_MAGEWORX_STR_ID= order_master.STR_ID).first()
                        operator_username_list = OperatorBusinessUnitAssignment.objects.filter(
                            ID_LCN=store_info.id).values_list("ID_OPR__NM_USR", flat=True)
                        user_data = User.objects.filter(username__in=operator_username_list).exclude(is_superuser=True)
                        store_admin_list.extend(user_data)
                    for admin in store_admin_list:
                        notification_data = {"device_id": "", "message_title": f"Order in {type}",
                            "message_body": f"Order No: {order_master.CU_OD_ID} {type.title()} by {user.username.title()}",
                            "notification_type": f"{type}_order", "event_id": None,
                            "user_id": admin.id, "file_name": None, "export_flag": False}
                        send_pushnotification(**notification_data)
                        device_list = UserDeviceInfo.objects.filter(USR_ID=admin)
                        for device in device_list:
                            notification_info = NotificationLog.objects.filter(ID_USR=admin.id).last()
                            notification_nncf_data = {"TYP_NTF": f"{type}_order", "ID_EVNT": None,
                                 "MSG_NTF": f"Order No: {order_master.CU_OD_ID} {type.title()} by {user.username.title()}",
                                 "TL_NTF": f"Order in {type}", "ID_DVS": device.DVS_TOKEN,  "ID_USR": device.USR_ID.id,
                                 "NTF_EPRT": False, "NTF_FL_NM": None, "DVC_TYPE": "web", "ST_NTF": "A",
                                 "ID_NTF": notification_info.ID_NTF}
                            push_service.notify_single_device(
                                registration_id=device.DVS_TOKEN,
                                message_title=f"Order in {type}",
                                message_body=f"Order No: {order_master.CU_OD_ID} {type.title()} by {user.username.title()}",
                                data_message=notification_nncf_data)
        except Exception:
            logger.info(f"Exception in Hold Notification {Exception}")
