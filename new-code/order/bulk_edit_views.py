import requests
import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from store.models import Location
from order.common_functions import check_email
from taxonomy.taxonomy_magento_integration import magento_login

from order.models import AssociateCrate, OrderBillingAddress, OrderCrates, OrderMaster, OrderShippingAddress


def bulk_edit_order_update_in_magento(request_data, order_number):
    '''Bulk edit order update in magento'''
    headers = {"content-type": 'application/json'}
    magento_token, magento_url = magento_login()
    url = f"/rest/default/V1/orders?searchCriteria[filterGroups][0][filters][0][field]=increment_id&searchCriteria[filterGroups][0][filters][0][value]={order_number.CU_OD_ID}"
    get_data = requests.get(url=magento_url+url,
                            headers=headers, auth=magento_token)
    magento_data = json.loads(
        get_data.text)
    if magento_data.get('items'):
        check_mail = check_email(order_number.OD_CUS_EMAIL)
        if check_mail[0]:
            get_magento_data = magento_data.get('items')[0]
            if request_data.get("BLNG"):
                billing_obj = request_data.get("BLNG")
                get_magento_data['billing_address'] = {
                    "address_type": "billing",
                    "city": billing_obj.get("OD_BA_CT"),
                    "country_id": billing_obj.get("OD_BA_CTR_CODE"),
                    "customer_address_id": get_magento_data.get("billing").get("customer_address_id"),
                    "email":  billing_obj.get("OD_BA_EMAIL"),
                    "entity_id": get_magento_data.get("billing").get("entity_id"),
                    "firstname": billing_obj.get("OD_BA_FN"),
                    "lastname": billing_obj.get("OD_BA_LN"),
                    "parent_id": get_magento_data.get("billing").get("parent_id"),
                    "postcode": billing_obj.get("OD_BA_PIN"),
                    "region": billing_obj.get("OD_BA_RGN"),
                    "region_code": billing_obj.get("OD_BA_RGN_CODE"),
                    "region_id": billing_obj.get("OD_BA_RGN_ID"),
                    "street": [
                        billing_obj.get("OD_BA_ST")
                    ],
                    "telephone": billing_obj.get("OD_BA_PH")
                }
            payload = {
                "entity": get_magento_data
            }
            payload = json.dumps(payload)


class BulkEditOrder(GenericAPIView):
    '''Bulk edit order'''
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def cre_payload_for_bulk_edit_order(self, billing_address, order_instance, response, shipping_address):
        '''Create a bulk edit order'''
        if billing_address:
            order_billing_instance = OrderBillingAddress.objects.filter(
                OD_BA_OD_ID=order_instance.OD_ID).first()
            if order_billing_instance:
                order_billing_instance.OD_BA_ST = billing_address.get(
                    'OD_BA_ST', None)
                order_billing_instance.OD_BA_FN = billing_address.get(
                    "OD_BA_FN", None)
                order_billing_instance.OD_BA_LN = billing_address.get(
                    "OD_BA_LN", None)
                order_billing_instance.OD_BA_CT = billing_address.get(
                    "OD_BA_CT", None)
                order_billing_instance.OD_BA_CTR_CODE = billing_address.get(
                    "OD_BA_CTR_CODE", None)
                order_billing_instance.OD_BA_RGN = billing_address.get(
                    "OD_BA_RGN", None)
                order_billing_instance.OD_BA_PIN = billing_address.get(
                    "OD_BA_PIN", None)
                order_billing_instance.OD_BA_EMAIL = billing_address.get(
                    "OD_BA_EMAIL", None)
                order_billing_instance.OD_BA_PH = billing_address.get(
                    "OD_BA_PH", None)
                order_billing_instance.OD_BA_RGN_CODE = billing_address.get(
                    "OD_BA_RGN_CODE", None)
                order_billing_instance.OD_BA_RGN_ID = billing_address.get(
                    "OD_BA_RGN_ID", None)
                order_billing_instance.save()
            response['message'] = "Order bulk billing address updated."
        if shipping_address:
            order_shipping_instance = OrderShippingAddress.objects.filter(
                OD_SA_OD_ID=order_instance.OD_ID).first()
            if order_shipping_instance:
                order_shipping_instance.OD_SA_ST = shipping_address.get(
                    "OD_SA_ST")
                order_shipping_instance.OD_SA_FN = shipping_address.get(
                    "OD_SA_FN", None)
                order_shipping_instance.OD_SA_LN = shipping_address.get(
                    "OD_SA_LN", None)
                order_shipping_instance.OD_SA_CT = shipping_address.get(
                    "OD_SA_CT", None)
                order_shipping_instance.OD_SA_CTR_CODE = shipping_address.get(
                    "OD_SA_CTR_CODE", None)
                order_shipping_instance.OD_SA_RGN = shipping_address.get(
                    "OD_SA_RGN", None)
                order_shipping_instance.OD_SA_PIN = shipping_address.get(
                    "OD_SA_PIN", None)
                order_shipping_instance.OD_SA_EMAIL = shipping_address.get(
                    "OD_SA_EMAIL", None)
                order_shipping_instance.OD_SA_PH = shipping_address.get(
                    "OD_SA_PH", None)
                order_shipping_instance.OD_SA_RGN_CODE = shipping_address.get(
                    "OD_SA_RGN_CODE", None)
                order_shipping_instance.OD_SA_RGN_ID = shipping_address.get(
                    "OD_SA_RGN_ID", None)
                order_shipping_instance.save()
            response['message'] = "Order bulk shipping address updated."

    def post(self, request, *args, **kwargs):
        '''Bulk update order views'''
        order_list = request.data.get("CU_OD_ID", [])
        billing_address = request.data.get("BLNG", None)
        shipping_address = request.data.get("SHPG", None)
        response = {}
        try:
            for od_num in order_list:
                order_instance = OrderMaster.objects.filter(
                    CU_OD_ID=od_num).first()
                if order_instance:
                    self.cre_payload_for_bulk_edit_order(
                        billing_address, order_instance, response, shipping_address)
                    bulk_edit_order_update_in_magento(
                        request.data, order_instance)
            sts = status.HTTP_200_OK
        except Exception as e:
            response['message'] = str(e)
        return Response(response, status=sts)


class GetCountryStateList(GenericAPIView):
    '''Get country state list'''

    def get(self, request, *args, **kwargs):
        '''Get country state list api'''
        headers = {"content-type": 'application/json'}
        magento_token, magento_url = magento_login()
        url = "/rest/default/V1/directory/countries/US"
        get_country_state_list = requests.get(url=magento_url+url,
                                              headers=headers, auth=magento_token)
        data = json.loads(
            get_country_state_list.text)
        if get_country_state_list.status_code == 200:
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(data, status=get_country_state_list.status_code)


class ExcludeCrateList(GenericAPIView):
    '''Exclude Crate list'''
    @swagger_auto_schema(tags=['Order'], operation_description="Get Excluded Crate List", operation_summary="Get Excluded Crate List", manual_parameters=[openapi.Parameter('STR_NM', openapi.IN_QUERY, description="Store id",
                                                                                                                                                                            type=openapi.TYPE_STRING)])
    def get(self, request, *args, **kwargs):
        '''Get the exclude crate list api'''
        store_name = request.GET.get('STR_NM', '')
        response = {}
        if store_name:
            response_list = OrderCrates.objects.filter(
                AC_ID__in=AssociateCrate.objects.filter(STR_ID__in=Location.objects.filter(Q(Q(MAG_MAGEWORX_STR_NM__icontains=store_name) | Q(NM_LCN__icontains=store_name)), CD_LCN_TYP__DE_LCN_TYP='STR').values_list('id', flat=True)).values_list('AC_ID', flat=True)).values_list('AC_ID__CRT_ID__CRT_ID', flat=True)
            response['list'] = response_list
            stat = status.HTTP_200_OK
        else:
            response['message'] = "Store name not provided!!!"
            stat = status.HTTP_400_BAD_REQUEST
        return Response(response, status=stat)
