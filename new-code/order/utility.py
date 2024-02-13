import logging
from copy import deepcopy
import json
import sys
import traceback
import requests
from pyfcm import FCMNotification
from django.conf import settings
from datetime import datetime, timedelta
from django.db import transaction
from celery import shared_task
from django.db.models import Q
from django.contrib.auth.models import User
from accesscontrol.models import OperatorBusinessUnitAssignment
from basics.notification_views import send_pushnotification
from basics.models import NotificationLog
from order.dnb_utility import notify_users
from login_authentication.models import UserDeviceInfo
from order.verify_order_api import shipment_items
from order.order_elastic import order_save
from order.serializers import OrderElasticDataSerializer
from globalsettings.models import BusinessUnitSetting, GlobalSetting
from store.models import Location
from order.serializers import OrderActivitySerilaizer, OrderMasterSerializer
from item_stock.models import ItemInventory
from product.models.models_item import Item
from taxonomy.taxonomy_magento_integration import magento_login
from order.models import Customer, OrderActivity, OrderItemDetails, OrderItemVariation, \
    OrderMaster, OrderBillingAddress, OrderPaymentDetails, OrderShippingAddress, PicklistMaster
from party.models import State
from party.serializers import (PostalCodeSerializer,PartySerializer,PartyRoleAssignmentSerializer,
                          EmailAddressSerializer, TelephoneSerializer, AddressSerializer,
                          PartyContactMethodSerializer)
from rest_framework import status
from party.manufacturer_views import (raise_exception_on_party_serializer,
                                      raise_exception_on_party_role_asgmt_serializer, create_person_or_organization,
                                      raise_exception_on_contact_details)
from party.models import (PartyContactMethod, PartyType,
                          PartyRole, Person)
from rest_framework import serializers
from party.customer_serializers import CustomerSerializer
import pycountry
logger = logging.getLogger(__name__)
push_service = FCMNotification(api_key=settings.FCM_KEY)

application_json_key = "application/json"

def collect_store_name(id):
    if id != 0 and id is not None:
        store_check = Location.objects.filter(MAG_MAGEWORX_STR_ID=id).first()
        return store_check.MAG_MAGEWORX_STR_NM
    else:
        return ""


def status_check(magento_status):
    is_verified = False
    mag_stat = 'pending'
    oms_stat = 'new'
    if magento_status == 'pending':
        mag_stat = 'pending'
        oms_stat = 'new'
        is_verified = False
    elif magento_status == 'processing':
        mag_stat = 'processing'
        oms_stat = 'ready_to_pick'
        is_verified = True
    elif magento_status == 'ready':
        mag_stat = 'ready'
        oms_stat = 'ready_for_pickup'
        is_verified = True
    elif magento_status == 'canceled':
        mag_stat = 'canceled'
        oms_stat = 'void'
        is_verified = True
    elif magento_status == 'holded':
        mag_stat = 'on hold'
        oms_stat = 'on hold'
        is_verified = True
    elif magento_status == 'complete':
        mag_stat = 'complete'
        oms_stat = 'complete'
        is_verified = True
    return mag_stat, oms_stat, is_verified


def calling_magento(method, url_str, payload=None):
    magento_token, magento_url = magento_login()
    headers = {
        "content-type": application_json_key
    }
    if method == "get":
        response = requests.get(
            url=magento_url+url_str, headers=headers, auth=magento_token)
    elif method == "post":
        response = requests.post(
            magento_url+url_str, headers=headers, data=json.dumps(payload), auth=magento_token)
    elif method == "put":
        response = requests.put(
            magento_url+url_str, headers=headers, data=json.dumps(payload), auth=magento_token)
    return response


def collect_payment_method_name(method_name):
    if method_name == "checkmo":
        name = "Check/Money Order"
    elif method_name == "authnetcim":
        name = "Credit Card"
    elif method_name == "paypal":
        name = "Paypal"
    else:
        name = "Free"
    return name


def check_payment_status(order_id):
    magento_token, magento_url = magento_login()
    magento_order_url = magento_url + \
        f"/rest/default/V1/transactions?searchCriteria[filterGroups][0][filters][0][field]=order_id&searchCriteria[filterGroups][0][filters][0][value]={order_id}"
    headers = {
        "content-type": application_json_key
    }
    magento_orders = requests.get(
        url=magento_order_url, headers=headers, auth=magento_token)
    all_response = json.loads(magento_orders.text)
    if len(all_response["items"]) > 0:
        payment_detail = {
            "OD_PAY_TRANS_ID": all_response["items"][0]["transaction_id"],
            "MAGENTO_OD_PAY_ID": all_response["items"][0]["payment_id"],
            "MAGENTO_OD_ID": all_response["items"][0]["order_id"],
            "OD_PAY_TXN_ID": all_response["items"][0]["txn_id"],
            "OD_PAY_PRT_TXN_ID": all_response["items"][0]["parent_txn_id"]
            if all_response["items"][0]["parent_txn_id"] else "",
            "OD_PAY_TXN_TYP": all_response["items"][0]["txn_type"],
            "OD_PAY_ADDT_INFO": all_response["items"][0]["additional_information"],
            "OD_PAY_CRT_DT": all_response["items"][0]["created_at"],
            "ERROR": ""
        }
        OrderPaymentDetails.objects.create(**payment_detail)
        return "Paid"
    else:
        return "Pending"


def make_boolean(data):
    if data == 0:
        return False
    else:
        return True


def save_configurable_item(order_item, item, order):
    configuration_values = order_item["product_option"]["extension_attributes"]["configurable_item_options"]
    for value in configuration_values:
        temp = {}
        temp["OD_ITM_VAR_OD"] = order
        temp["OD_ITM_VAR_ITM"] = item
        temp["OD_ITM_VAR_OPT_ID"] = value.get("option_id")
        temp["OD_ITM_VAR_OPT_VAL"] = value.get("option_value")
        variable_data = OrderItemVariation(**temp)
        variable_data.save()


def parent_item_insert(order_item, current_order):
    if "parent_item" in order_item:
        order_item = order_item.get("parent_item")
        product_info = Item.objects.filter(
            AS_ITM_SKU=order_item.get("sku")).first()
        save_configurable_item(order_item, product_info, current_order)
    product_info = Item.objects.filter(
        AS_ITM_SKU=order_item.get("sku")).first()
    temp_order_item = {}
    temp_order_item["OD_ID"] = current_order
    temp_order_item["OD_ITM_AMT_REF"] = order_item.get("amount_refunded", 0)
    temp_order_item["OD_ITM"] = product_info
    temp_order_item["OD_ITM_BS_PR"] = order_item.get("base_price", 0)
    temp_order_item["OD_ITM_TOTL_AMT"] = order_item.get("base_row_total", 0)
    temp_order_item["OD_ITM_CRT_DT"] = order_item.get("created_at", '')
    temp_order_item["OD_ITM_DSC_AMT"] = order_item.get("discount_amount", 0)
    temp_order_item["OD_ITM_DSC_INVC"] = order_item.get(
        "discount_invoiced", 0)
    temp_order_item["OD_ITM_DSC_PER"] = order_item.get(
        "discount_percent", 0)
    temp_order_item["OD_ITM_FRE_SHP"] = make_boolean(
        order_item.get("free_shipping"))
    temp_order_item["OD_ITM_DSC_TX_CMPSATN_AMT"] = order_item.get(
        "discount_tax_compensation_amount", 0)
    temp_order_item["OD_ITM_IS_QTY_DCML"] = make_boolean(
        order_item.get("is_qty_decimal"))
    temp_order_item["OD_ITM_IS_VRTL"] = make_boolean(
        order_item.get("is_virtual"))
    temp_order_item["OD_ITM_ID_ITM"] = order_item.get("item_id", 0)
    temp_order_item["OD_ITM_NM"] = order_item.get("name", '')
    temp_order_item["OD_ITM_SKU"] = order_item.get("sku", '')
    temp_order_item["OD_ITM_NO_DSC"] = order_item.get("no_discount", 0)
    temp_order_item["OD_ITM_ODR_ID"] = order_item.get("order_id", 0)
    temp_order_item["OD_ITM_OR_PR"] = order_item.get("original_price", 0)
    temp_order_item["OD_ITM_PRC"] = order_item.get("price", 0)
    temp_order_item["OD_ITM_PRC_INC_TX"] = order_item.get(
        "price_incl_tax", 0)
    temp_order_item["OD_ITM_CL_QTY"] = order_item.get("qty_canceled", 0)
    temp_order_item["OD_ITM_INVC_QTY"] = order_item.get("qty_invoiced", 0)
    temp_order_item["OD_ITM_INVC"] = ""
    temp_order_item["OD_ITM_QTY"] = order_item.get("qty_ordered", 0)
    temp_order_item["OD_ITM_RFND_QTY"] = order_item.get("qty_refunded", 0)
    temp_order_item["OD_ITM_RETN_QTY"] = order_item.get("qty_returned", 0)
    temp_order_item["OD_ITM_SHP_QTY"] = order_item.get("qty_shipped", 0)
    temp_order_item["OD_ITM_QOT_ITM_ID"] = order_item.get(
        "quote_item_id", 0)
    temp_order_item["OD_ITM_ROW_INVOICED"] = order_item.get(
        "row_invoiced", 0)
    temp_order_item["OD_ITM_ROW_TOT"] = order_item.get("row_total", 0)
    temp_order_item["OD_ITM_ROW_TOT_INC_TX"] = order_item.get(
        "row_total_incl_tax", 0)
    temp_order_item["OD_ITM_ROW_WGHT"] = order_item.get("row_weight", 0)
    # "store_id" Its pending as we are storing location but in api we are getting store
    temp_order_item["OD_ITM_TAX_AMT"] = order_item.get("tax_amount", 0)
    temp_order_item["OD_ITM_TAX_INVC_AMT"] = order_item.get(
        "tax_invoiced", 0)
    temp_order_item["OD_ITM_TAX_CL_AMT"] = order_item.get("tax_canceled", 0)
    temp_order_item["OD_ITM_TAX_PER"] = order_item.get("tax_percent", 0)
    temp_order_item["OD_ITM_UPDT_DT"] = order_item.get("updated_at", '')
    temp_order_item["OD_ITM_NET_AMT"] = (order_item.get("qty_ordered", 0) * order_item.get("original_price", 0))\
        + order_item.get("tax_amount", 0) - \
        order_item.get("discount_amount", 0)
    temp_order_item["OD_ITM_QTY_PKD"] = None
    return temp_order_item


def order_items_detail(order_items, current_order):
    for order_item in order_items:
        if order_item.get("product_type") in ["virtual", "simple"]:
            temp_order_item = parent_item_insert(order_item, current_order)
            order_item_data = OrderItemDetails(**temp_order_item)
            order_item_data.save()


def add_payment_order(order):
    payment_change = OrderPaymentDetails.objects.filter(
        MAGENTO_OD_ID=order.CH_OD_ID).first()
    if payment_change:
        payment_change.OD_PAY_OD = order
        payment_change.save()


def check_store_code(id):
    if id != 0 and id is not None:
        store_check = Location.objects.filter(MAG_MAGEWORX_STR_ID=id).first()
        return store_check.MAG_MAGEWORX_STR_CD
    else:
        return ""


def get_store_mageworx_id(id):
    try:
        if id != 0 and id is not None:
            store_check = Location.objects.filter(
                Q(CD_LCN=id) | Q(MAG_MAGEWORX_STR_CD=id)).first()
            return store_check.MAG_MAGEWORX_STR_ID
        else:
            return None
    except Exception:
        return None


def new_order_save(get_response,magento_token, magento_url):
    customer_info = {}
    order_temp = {}

    magento_order_status = get_response.get("status")
    order_status = status_check(magento_order_status)
    order_temp["CU_OD_ID"] = get_response.get("increment_id")
    order_temp["CH_OD_ID"] = get_response.get("entity_id")
    order_temp["PT_MD_NM"] = collect_payment_method_name(
        get_response.get("payment").get("method")) if 'payment' in get_response else ''
    order_temp["OD_CUS_NM"] = get_response.get("customer_firstname") + \
        " " + get_response.get("customer_lastname")
    order_temp["OD_CUS_EMAIL"] = get_response.get("customer_email")
    order_temp["IS_GUST"] = get_response.get("customer_is_guest")
    order_temp["OD_TL_AMT"] = get_response.get("grand_total")
    order_temp["OD_NT_AMT"] = get_response.get("subtotal")
    order_temp["OD_SHP_AMT"] = get_response.get("shipping_amount")
    order_temp["OD_SHIP_DESC"] = get_response.get("shipping_description", '')
    order_temp["OD_PD_AMT"] = get_response.get("grand_total")
    order_temp["OD_TX_AMT"] = get_response.get("tax_amount")
    order_temp["OD_STS"] = order_status[0]
    order_temp["OD_DATE"] = datetime.strptime(
        get_response.get("created_at"), "%Y-%m-%d %H:%M:%S").astimezone()
    order_temp["OD_CUR_COD"] = get_response.get("store_currency_code", '')
    order_temp["OD_IP_ADDR"] = get_response.get("remote_ip", '')
    order_temp["IS_MAIL"] = get_response.get(
        "email_sent") if "email_sent" in get_response else 0
    order_temp["OD_PAY_STS"] = check_payment_status(
        get_response.get("entity_id"))
    order_temp["OD_QTY"] = get_response.get("total_item_count")
    if "mageworx_pickup_location_id" in get_response.get("extension_attributes"):
        order_temp["STR_ID"] = get_response.get(
            "extension_attributes").get("mageworx_pickup_location_id")
        order_temp["OD_TYPE"] = "WebStore-Pickup"
        order_temp["OD_STR_NM"] = collect_store_name(get_response.get(
            "extension_attributes").get("mageworx_pickup_location_id"))

    elif "pickup_location_code" in get_response.get("extension_attributes"):
        order_temp["STR_ID"] = get_store_mageworx_id(get_response.get(
            "extension_attributes").get("pickup_location_code"))
        order_temp["OD_TYPE"] = "WebStore-Pickup"
        order_temp["OD_STR_NM"] = collect_store_name(get_store_mageworx_id(get_response.get(
            "extension_attributes").get("pickup_location_code")))

    else:
        order_temp["STR_ID"] = None
        order_temp["OD_TYPE"] = "Webstore-Delivery"
        order_temp["OD_STR_NM"] = "Default_Store"
    order_temp["OD_PROT_ID"] = get_response.get("protect_code")
    order_temp["OD_DIS_AMT"] = get_response.get("discount_amount")
    order_temp["OD_INST"] = ""
    order_temp["OD_INVC_NUM"] = ""
    order_temp["OD_SHP_NUM"] = ""
    order_temp["IS_VERIFIED"] = order_status[2]
    order_temp["OMS_OD_STS"] = order_status[1]
    customer_email = Customer.objects.filter(
        CUST_EMAIL=get_response.get("customer_email"))
    if not customer_email:
        customer_instance = customer_sync(get_response,magento_token,magento_url)
    else:
        customer_instance = customer_email.first()
    order_temp['OD_CUST'] = customer_instance

    order = OrderMaster(**order_temp)
    order.save()
    add_payment_order(order)

    return order


def add_customer_from_magento(party_role_asign_save, party_instance, datas, cust_info, created_by, body_datas):
    '''Creation of a new manufacturer'''
    
    customer_data = {
        "CUST_FNM": cust_info.get('CUST_FNM'),
        "CUST_LNM": cust_info.get('CUST_LNM'),
        "CUST_EMAIL": cust_info.get('CUST_EMAIL'),
        "CUST_PH": cust_info.get('CUST_PH'),
        # "SC_CT": cust_info.get('SC_CT'),
        "ID_PRTY_RO_ASGMT": party_role_asign_save.ID_PRTY_RO_ASGMT,
        "ID_PRTY": party_instance,
        "CRT_BY": created_by,
        "URL_PGPH_CT": datas.get('URL_PGPH_CT', None),
    }
    if Customer.objects.filter(CUST_EMAIL=cust_info.get('CUST_EMAIL')).exists():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Email already Exists!"})
    customer_serializer = CustomerSerializer(
        data=customer_data)
    if not customer_serializer.is_valid():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Invalid Data!"})

    customer_instance = customer_serializer.save()
    customer_save_data = customer_serializer.data
    body_datas.update(customer_save_data)
    return customer_instance


def get_phone_code(country_code):
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if country:
            return '+' + str(country.numeric)
        else:
            return ''
    except Exception:
        return None
    
def save_customer_address(customer_info,address,results,email_adds_id):

    party_type_code = 'PR'
    party_type = PartyType.objects.get(CD_PRTY_TYP=party_type_code)

    party_insert_data = {
        "ID_PRTY_TYP": party_type.ID_PRTY_TYP,
        # "BY_CRT_PRTY": created_by
        }
    party_serializer = PartySerializer(data=party_insert_data)
    raise_exception_on_party_serializer(party_serializer)
    save_datas = party_serializer.save()
    body_datas = party_serializer.data
    
    if save_datas.ID_PRTY:
        party_role = PartyRole.objects.get(TY_RO_PRTY="CUST")
        party_role_ids = party_role.ID_RO_PRTY
        party_role_asgmt_data = {
            "ID_PRTY": save_datas.ID_PRTY,
            "ID_RO_PRTY": party_role_ids}
        
        party_role_asgmt_serializer = PartyRoleAssignmentSerializer(data=party_role_asgmt_data)
        raise_exception_on_party_role_asgmt_serializer(party_role_asgmt_serializer)

        party_role_asign_save = party_role_asgmt_serializer.save()
        body_datas.update(
            party_role_asgmt_serializer.data
                        )
        body_datas = create_person_or_organization(
            party_type_code, save_datas, customer_info, body_datas, None)

        if party_role_asign_save.ID_PRTY_RO_ASGMT:
            customer_instance = add_customer_from_magento(
                party_role_asign_save, save_datas.ID_PRTY, customer_info, customer_info, None, body_datas
                )

    if address.get('telephone'):
        phone_data = {
            "CD_CY_ITU": address.get('country_id'),
            "TA_PH": get_phone_code(address.get('country_id')),
            "TL_PH": address.get('telephone'),
            "PH_CMPL": address.get('telephone')}
        phone = TelephoneSerializer(data=phone_data)
        if not phone.is_valid():
            results['errors'] = phone.errors
            results['status'] = status.HTTP_400_BAD_REQUEST
            return results
        phone_save = phone.save()
        phone_id = phone_save.ID_PH
    if address.get('customer_email'):
        email_data = {
            "EM_ADS_LOC_PRT": str(address.get('customer_email')).split('@')[0],
            "EM_ADS_DMN_PRT": str(address.get('customer_email')).split('@')[1],
            }
        email = EmailAddressSerializer(data=email_data)
        if not email.is_valid():
            results['errors'] = email.errors
            results['status'] = status.HTTP_400_BAD_REQUEST
            return results
        email_save = email.save()
        email_adds_id = email_save.ID_EM_ADS

    logger.info("Email Adds Id : %s",
                email_adds_id)

    if address.get('postcode'):
        postal_address_data = {
            "CD_PSTL": address.get('postcode'),
            "CD_CY_ITU": address.get('country_id')
        }
        postal = PostalCodeSerializer(
            data=postal_address_data)
        if not postal.is_valid():
            results['errors'] = postal.errors
            results['status'] = status.HTTP_400_BAD_REQUEST
            return results
        postal_save = postal.save()
        postal_code_id = postal_save.ID_PSTL_CD
        party_role_asign_save = party_role_asign_save.ID_PRTY_RO_ASGMT
    return customer_instance,phone_id,postal_code_id, party_role_asign_save,email_adds_id





def customer_sync(order_get_response,  magento_token, magento_url):
    ''' Customer Sync From Order '''
    magento_customer_id = order_get_response.get('customer_id')
    customer_info = {}
    results = {}
    customer_info['CUST_FNM'] = order_get_response.get("customer_firstname")
    customer_info['CUST_LNM'] = order_get_response.get("customer_lastname")
    customer_info['CUST_EMAIL'] = order_get_response.get("customer_email")
    customer_info['CUST_PH'] = ''
    customer_info['TY_GND_PRS'] = ''
    customer_info['DC_PRS_BRT'] = None
    if order_get_response.get("customer_is_guest") == 1:
        customer_info['IS_GUST'] = True
    else:
        customer_info['IS_GUST'] = False
    magento_customer_url = magento_url + \
        f"/rest/default/V1/customers/{magento_customer_id}"

    headers = {
        "content-type": application_json_key
    }
    magento_customer = requests.get(
        url=magento_customer_url, headers=headers, auth=magento_token)
    all_response = json.loads(magento_customer.text)
    customer_address_list = all_response.get('addresses',[])
    address_list = []
    postal_code_id = None
    email_adds_id = None
    customer_instance = None
    address_id = None
    for address in customer_address_list:
        region_code = address.get('region_code', None)
        state_id = State.objects.filter(
            CD_ST=region_code).first() if region_code else None
        logger.info("State ID : %s", state_id)
        address_list.append(
            {
                "FST_NM": address.get('firstname', ''),
                "LST_NM": address.get('lastname', ''),
                "A1_ADS": address.get('street')[0],
                "CI_CNCT": address.get('city'),
                "ID_ST": state_id,
                "CD_CY_ITU": address.get('country_id'),
                "PH_CMPL": address.get('telephone'),
                "CD_PSTL": address.get('postcode'),
                "CD_STS": "A",
                "IS_SHIPPING": address.get('default_shipping', False),
                "IS_BILLING": address.get('default_billing', False)
            }
        )
        ############ ADD CUSTOMER HERE  #######################
        with transaction.atomic():
            customer_instance,phone_id,postal_code_id,party_role_asign_save,email_adds_id = save_customer_address(customer_info,address,results,email_adds_id)

            address_data = {
                "FST_NM": address.get('firstname', ''),
                "LST_NM": address.get('LST_NM', ''),
                "A1_ADS": address.get('street')[0],
                "CI_CNCT": address.get('city'),
                "CD_CY_ITU": address.get('country_id'),
                "ID_ST": state_id,
                "ID_PSTL_CD": postal_code_id
            }
            address_serializer = AddressSerializer(data=address_data)
            if not address_serializer.is_valid():
                results['errors'] = address_serializer.errors
                results['status'] = status.HTTP_400_BAD_REQUEST
                return results
            address_save = address_serializer.save()
            address_id = address_save.ID_ADS

            party_contact_data = {
                "CD_TYP_CNCT_PRPS": address.get('CD_TYP_CNCT_PRPS', None),
                "CD_TYP_CNCT_MTH": address.get('CD_TYP_CNCT_MTH', None),
                "ID_PRTY_RO_ASGMT": party_role_asign_save,
                "ID_ADS": address_id,
                "ID_EM_ADS": email_adds_id,
                "CD_STS": 'A',
                "ID_PH": phone_id,
                "IS_SHIPPING": address.get('IS_SHIPPING', False),
                "IS_BILLING": address.get('IS_BILLING', False)
            }
            logger.info("Party Contact Data : %s",
                        party_contact_data)
            party_contact = PartyContactMethodSerializer(
                data=party_contact_data)
            if not party_contact.is_valid():
                logger.info("Party Contact Error")
                results['errors'] = party_contact.errors
                results['status'] = status.HTTP_400_BAD_REQUEST
                return results
            party_contact.save()
            logger.info(party_contact.data.get('ID_PRTY_CNCT_MTH'))
    return customer_instance


def save_billing_address(get_response, current_order):
    billing_temp = {}
    billing_temp["OD_PRT_ID"] = get_response.get(
        "billing_address").get("parent_id")
    billing_temp["OD_ENT_ID"] = get_response.get(
        "billing_address").get("entity_id")
    billing_temp["OD_BA_FN"] = get_response.get(
        "billing_address").get("firstname")
    billing_temp["OD_BA_MN"] = get_response.get("billing_address").get(
        "middlename") if "middlename" in get_response.get("billing_address") else ''
    billing_temp["OD_BA_LN"] = get_response.get(
        "billing_address").get("lastname")
    billing_temp["OD_BA_EMAIL"] = get_response.get(
        "billing_address").get("email")
    billing_temp["OD_BA_PH"] = get_response.get(
        "billing_address").get("telephone")
    billing_temp["OD_BA_ST"] = ", ".join(
        get_response.get("billing_address").get("street"))
    billing_temp["OD_BA_CT"] = get_response.get("billing_address").get("city")
    billing_temp["OD_BA_RGN"] = get_response.get("billing_address").get(
        "region") if "region" in get_response.get("billing_address") else ''
    billing_temp["OD_BA_RGN_CODE"] = get_response.get("billing_address").get(
        "region_code") if "region_code" in get_response.get("billing_address") else ''
    billing_temp["OD_BA_CTR_CODE"] = get_response.get(
        "billing_address").get("country_id")
    billing_temp["OD_BA_PIN"] = get_response.get(
        "billing_address").get("postcode")
    billing_temp["OD_BA_OD_ID"] = current_order
    billing_temp["OD_BA_RGN_ID"] = get_response.get(
        "billing_address").get("region_id")
    billing_temp["OD_BA_CUS_ADD_ID"] = billing_temp.get("customer_address_id")
    billing = OrderBillingAddress(**billing_temp)
    billing.save()

# @shared_task()


def save_shipping_address(get_response, current_order):
    shipping_dict = get_response["extension_attributes"]["shipping_assignments"][0]["shipping"]["address"]
    shipping_temp = {}
    shipping_temp["OD_PRT_ID"] = shipping_dict.get("parent_id")
    shipping_temp["OD_ENT_ID"] = shipping_dict.get("entity_id")
    shipping_temp["OD_SA_FN"] = shipping_dict.get(
        "firstname", '') if shipping_dict.get("firstname", '') is not None else ""
    shipping_temp["OD_SA_MN"] = shipping_dict.get("middlename", '')
    shipping_temp["OD_SA_LN"] = shipping_dict.get(
        "lastname", '') if shipping_dict.get("lastname", '') is not None else ""
    shipping_temp["OD_SA_EMAIL"] = shipping_dict.get("email", '')
    shipping_temp["OD_SA_PH"] = shipping_dict.get("telephone")
    shipping_temp["OD_SA_ST"] = ", ".join(shipping_dict.get("street", ''))
    shipping_temp["OD_SA_CT"] = shipping_dict.get(
        "city", '') if shipping_dict.get("city", '') is not None else ""
    shipping_temp["OD_SA_RGN"] = shipping_dict.get("region", '')
    shipping_temp["OD_SA_RGN_CODE"] = shipping_dict.get("region_code", '')
    shipping_temp["OD_SA_CTR_CODE"] = shipping_dict.get(
        "country_id", '') if shipping_dict.get("country_id", '') is not None else ""
    shipping_temp["OD_SA_PIN"] = shipping_dict.get(
        "postcode", '') if shipping_dict.get("postcode", '') is not None else ""

    shipping_temp["OD_SA_OD_ID"] = current_order
    shipping_temp["OD_SA_RGN_ID"] = shipping_dict.get("region_id")
    shipping_temp["OD_SA_CUS_ADD_ID"] = shipping_dict.get(
        "customer_address_id") if shipping_dict.get("customer_address_id") is not None else 0
    shipping = OrderShippingAddress(**shipping_temp)
    shipping.save()


def save_order_activity(order, customer, commment, user=None):
    current_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    order_activity = {
        "OD_ACT_OD_MA_ID": order,
        "OD_ACT_CMT": commment,
        "OD_ACT_STATUS": "New",
        "OD_ACT_IS_CUST_NTD": 0,
        "OD_CUST": customer.id if customer else None,
        "OD_ACT_CRT_AT": current_time,
        "OD_ACT_ENT_ID": order.CH_OD_ID,
        "OD_ACT_CRT_BY": user,
        "OD_ACT_IS_VISI_ON_FRT": 0,
    }
    OrderActivity.objects.create(**order_activity)


def create_shipment_picking_id(order_instance):
    '''Create shipment and picking id'''
    if order_instance.OMS_OD_STS != 'new':
        shipment_items(order_instance)


@shared_task
def magento_orders():
    magento_token, magento_url = magento_login()
    to_time = datetime.now()
    from_time = (to_time - timedelta(days=1))
    to_time = to_time.strftime('%Y-%m-%dT%H:%M:%S%z')
    from_time = from_time.strftime('%Y-%m-%dT%H:%M:%S%z')
    magento_order_url = magento_url + \
        f"/rest/V1/orders?searchCriteria[filter_groups][0][filters][0][field]=created_at&searchCriteria[filter_groups][0][filters][0][condition_type]=from&searchCriteria[filter_groups][0][filters][0][value]={from_time}&searchCriteria[filter_groups][1][filters][0][field]=created_at&searchCriteria[filter_groups][1][filters][0][condition_type]=to&searchCriteria[filter_groups][1][filters][0][value]={to_time}"

    headers = {
        "content-type": application_json_key
    }

    magento_orders = requests.get(
        url=magento_order_url, headers=headers, auth=magento_token)
    all_response = json.loads(magento_orders.text)
    all_order = []
    for get_response in all_response.get("items"):
        with transaction.atomic():
            # check item present in database
            flag = 0
            for itm in get_response.get("items"):
                itm_obj = Item.objects.filter(
                    AS_ITM_SKU__icontains=itm.get("sku")).exists()
                if not itm_obj:
                    flag = 1
                    break
            if flag != 1:
                check_order = OrderMaster.objects.filter(
                    CU_OD_ID__iexact=get_response.get("increment_id")).first()
                if not check_order:
                    order_instance = new_order_save(
                        get_response,magento_token,magento_url)
                    current_order = OrderMaster.objects.filter(
                        CU_OD_ID__iexact=get_response.get("increment_id"),
                        CH_OD_ID=get_response.get("entity_id")).first()
                    customer_check = Customer.objects.filter(
                        CUST_EMAIL=all_response.get("customer_email")).first()
                    order_items_detail(
                        get_response.get("items"), current_order)
                    save_billing_address(get_response, current_order)
                    if "address" in get_response["extension_attributes"]["shipping_assignments"][0]["shipping"]:
                        save_shipping_address(get_response, current_order)
                    save_order_activity(
                        current_order, customer_check, "Order Created", "Admin")
                    create_shipment_picking_id(order_instance)
                    notify_users(current_order, type="order")
                    get_all_serialzied_data = OrderElasticDataSerializer(
                        order_instance).data

                    order_save(get_all_serialzied_data,
                               settings.ES_ORDER_INDEX, order_instance.OD_ID)

    return all_order

# magento_orders()


def create_magento_order(order_data):
    magento_base_order_entity = {
        "applied_rule_ids": "1",
        "base_currency_code": "USD",
        "customer_group_id": 1,
        "base_grand_total": order_data.get("OD_TL_AMT"),
        "base_shipping_amount": order_data.get("OD_SHP_AMT"),
        "base_shipping_incl_tax": order_data.get("OD_SHP_AMT"),
        "base_subtotal": order_data.get("OD_NT_AMT"),
        "base_subtotal_incl_tax": order_data.get("OD_TL_AMT"),
        "customer_email": order_data.get("CUST_EMAIL"),
        "email_sent": 1,
        "global_currency_code": "USD",
        "customer_firstname": order_data.get("CUST_NAME").split(" ")[0],
        "customer_lastname": order_data.get("CUST_NAME").split(" ")[-1],
        "customer_is_guest": 0,
        "base_total_due": order_data.get("OD_TL_AMT"),
        "discount_amount": order_data.get("OD_DIS_AMT"),
        "grand_total": order_data.get("OD_TL_AMT"),
        "discount_tax_compensation_amount": 0,
        "is_virtual": 0,
        "order_currency_code": "USD",
        "state": "new",
        "status": "pending",
        "store_id": 1,
        "store_name": "Main Website\nMain Website Store\nDefault Store View",
        "shipping_amount": order_data.get("OD_SHP_AMT"),
        "shipping_description": collect_store_name(order_data.get("OD_STR_ID")),
        "shipping_discount_amount": 0,
        "shipping_discount_tax_compensation_amount": 0,
        "shipping_tax_amount": 0,
        "total_qty_ordered": 10,
        "total_item_count": len(order_data.get("items")),
        "shipping_incl_tax": order_data.get("OD_SHP_AMT"),
        "subtotal": order_data.get("OD_TL_AMT"),
        "subtotal_incl_tax": order_data.get("OD_TL_AMT"),
        "tax_amount": order_data.get("OD_TX_AMT", 0),
        "status_histories": [],
    }
    order_items = []
    for item in order_data.get("items"):
        product = Item.objects.filter(
            AS_ITM_SKU=item.get("AS_ITM_SKU")).first()
        order_item = {
            "amount_refunded": 0,
            "applied_rule_ids": "1",
            "qty_canceled": 0,
            "qty_invoiced": 0,
            "qty_refunded": 0,
            "qty_returned": 0,
            "qty_shipped": 0,
            "row_invoiced": 0,
            "row_total": 0,
            "row_total_incl_tax": 0,
            "row_weight": 0,
            "sku": product.AS_ITM_SKU,
            "qty_ordered": int(item.get("OD_ITM_QTY")),
            "original_price": item.get("OD_ITM_OR_PR"),
            "price_incl_tax": item.get("OD_ITM_OR_PR"),
            "price": item.get("OD_ITM_OR_PR"),
            "tax_amount": item.get("OD_ITM_TAX_AMT"),
            "tax_invoiced": 0,
            "tax_percent": 0,
            "name": item.get("OD_ITM_NM"),
            "discount_amount": item.get("OD_ITM_DSC_AMT"),
            "discount_invoiced": 0,
            "discount_percent": 0,
            "free_shipping": 0,
            "discount_tax_compensation_amount": 0,
            "is_qty_decimal": 0,
            "is_virtual": 0,
            "store_id": 1,
            "product_type": product.AS_ITM_TYPE,

        }
        order_items.append(order_item)
        inventory = ItemInventory.objects.filter(
            STK_ITM_INVTRY_ID__ID_ITM__AS_ITM_SKU=item.get("AS_ITM_SKU")).first()
        inventory.ACTL_STK = inventory.ACTL_STK - \
            float(order_data.get("OD_QTY"))
        inventory.VRTL_STK = float(order_data.get("OD_QTY"))
        inventory.save()
    add_items = {
        "items": order_items
    }
    magento_base_order_entity.update(add_items)
    magento_billing_address = {
        "billing_address": {
            "address_type": "billing",
            "city": order_data.get("OD_BA_CT"),
            "country_id": order_data.get("OD_BA_CTR_CODE"),
            "email": order_data.get("OD_BA_EMAIL"),
            "firstname": order_data.get("OD_BA_FN"),
            "lastname": order_data.get("OD_BA_LN"),
            "postcode": order_data.get("OD_BA_PIN"),
            "region": order_data.get("OD_BA_RGN"),
            "street": [order_data.get("OD_BA_ST")],
            "telephone": order_data.get("CUST_PH")
        }
    }
    magento_base_order_entity.update(magento_billing_address)
    magento_payment_information = {
        "payment": {
            "account_status": None,
            "additional_information": ["Check / Money order"],
            "amount_ordered": order_data.get("OD_TL_AMT"),
            "base_amount_ordered": order_data.get("OD_TL_AMT"),
            "base_shipping_amount": order_data.get("OD_SHP_AMT"),
            "cc_last4": None,
            "shipping_amount": 0,
            "method": "checkmo"
        }
    }
    magento_base_order_entity.update(magento_payment_information)
    magento_shipping = {
        "extension_attributes": {
            "shipping_assignments": [
                {
                    "shipping": {
                        "address": {
                            "address_type": "shipping",
                            "city": order_data.get("OD_SA_CT") if order_data.get("OD_SA_CT") else order_data.get("OD_BA_CT"),
                            "country_id": order_data.get("OD_SA_CTR_CODE") if order_data.get("OD_SA_CTR_CODE") else order_data.get("OD_BA_CTR_CODE"),
                            "email": order_data.get("OD_SA_EMAIL") if order_data.get("OD_SA_EMAIL") else order_data.get("OD_BA_EMAIL"),
                            "firstname": order_data.get("OD_SA_FN") if order_data.get("OD_SA_FN") else order_data.get("OD_BA_FN"),
                            "lastname": order_data.get("OD_SA_LN") if order_data.get("OD_SA_LN") else order_data.get("OD_BA_LN"),
                            "postcode": order_data.get("OD_SA_PIN") if order_data.get("OD_SA_PIN") else order_data.get("OD_BA_PIN"),
                            "region": order_data.get("OD_SA_RGN") if order_data.get("OD_SA_RGN") else order_data.get("OD_BA_RGN"),
                            "street": [order_data.get("OD_SA_ST") if order_data.get("OD_SA_ST") else order_data.get("OD_BA_ST")],
                            "telephone": order_data.get("CUST_PH")
                        },
                        "method": "mageworxpickup_mageworxpickup",
                        "total":
                            {
                                "base_shipping_amount": 0,
                                "base_shipping_discount_amount": 0,
                                "base_shipping_incl_tax": 0,
                                "base_shipping_tax_amount": 0,
                                "shipping_amount": 0,
                                "shipping_discount_amount": 0,
                                "shipping_discount_tax_compensation_amount": 0,
                                "shipping_incl_tax": 0,
                                "shipping_tax_amount": 0
                        }
                    },
                    "items": order_items
                }
            ],
            "payment_additional_info": [
                {
                    "key": "0",
                    "value": "Check / Money order"
                }
            ],
            "mageworx_pickup_location_id": order_data.get("OD_STR_ID"),
            "pickup_location_code": check_store_code(order_data.get("OD_STR_ID")),
            "applied_taxes": [],
            "item_applied_taxes": []
        }
    }
    magento_base_order_entity.update(magento_shipping)
    magento_final_payload = {
        "entity": magento_base_order_entity
    }

    order_post_url_str = "rest/default/V1/orders/create"

    try:
        resposne = calling_magento(
            "put", order_post_url_str, payload=magento_final_payload)

        if resposne.status_code == 200:
            with transaction.atomic():
                magento_orders()
                change_type = OrderMaster.objects.latest('OD_ID')
                change_type.OD_TYPE = "WebStore"
                change_type.save()
            return True
        return False
    except Exception as error:
        trace_back = sys.exc_info()[2]
        line = trace_back.tb_lineno
        logger.info(f"{traceback.format_exc()},\n {line},\n {str(error)}")
