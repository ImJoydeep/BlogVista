import io
import os
import PyPDF2
import logging
import pdfkit
from copy import deepcopy
from drf_yasg import openapi
from django.http import HttpResponse
from django.db.models import Q, Sum
from django.conf import settings
from datetime import datetime
from django.db import transaction
from django.template import Template, Context
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import (ListModelMixin)
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.exceptions import ValidationError
from auto_responder.models import EmailTemplate
from order.dnb_utility import send_pick_notification
from globalsettings.models import BusinessUnitSetting, GlobalSetting
from product.models.models_item import Item
from store.models import Location
from order.order_elastic import order_save
from order.serializers_shipment import CratesSerializer, GenerateItemShipmentGetSerializer, ScanPickItemSerializer,\
    ShipmentListSerializer, ItemShipmentListSerializer
from order.shipment_filter import shipment_filter

from order.models import AssociateCrate, Crates, ItemPicklist, ItemShipmentList, OrderActivity, OrderCrates, OrderItemDetails,\
    OrderMaster, ShipmentMaster, PicklistMaster
from order.serializers import GeneratePickListSerializer, OrderElasticDataSerializer, update_comment_on_verify

logger = logging.getLogger(__name__)


def create_next_code(name=None, starts_with_name=None):
    if name == "pick":
        pick_prefix = "PICK"
        pick_last_id = PicklistMaster.objects.last()
        if pick_last_id:
            new_pick_id = int(pick_last_id.OD_PICK_ID)+int(1)
        else:
            new_pick_id = 1
        new_pick_code = pick_prefix+""+str(new_pick_id)
        return new_pick_code
    elif name == "shipment":
        shipment_prefix = starts_with_name if starts_with_name is not None else "SHP"
        last_shipment = ShipmentMaster.objects.last()
        if last_shipment:
            last_shipment_id = int(last_shipment.OD_SHP_ID)+int(1)
        else:
            last_shipment_id = 1
        shipment_id_new = shipment_prefix+""+str(last_shipment_id)
        return shipment_id_new
    return ''


class GeneratePickListPdf(GenericAPIView):
    '''Print General Picking List'''
    serializer_class = GeneratePickListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    response_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'order_ids': openapi.Schema(type=openapi.TYPE_ARRAY,
                                        description='Array of Ids',
                                        items=openapi.Items(type=openapi.TYPE_INTEGER,
                                                            description='Order Ids')),
        },
    )

    def get(self, request, *args, **kwargs):
        try:
            response = {}
            html = ''
            order_id = request.GET.getlist('order_ids')
            order_id = order_id[0].split(',')
            order_info = OrderMaster.objects.filter(CU_OD_ID__in=order_id)
            order_serializer = GeneratePickListSerializer(
                order_info, many=True).data
            template_info = EmailTemplate.objects.filter(
                ET_DS="Generate Picklist Pdf").first()
            file_name = 'picklist.html'
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)
            with open(file_path, 'w') as file:
                file.write(template_info.ET_HTML_TXT)
            with open(file_path, 'r') as file:
                template_content = file.read()
            for order in order_serializer:
                temp = {}
                temp["CU_OD_ID"] = order.get("CU_OD_ID")
                temp["OD_CUS_NM"] = order.get("OD_CUS_NM")
                temp["OD_CUS_EMAIL"] = order.get("OD_CUS_EMAIL")
                temp["CUST_PH"] = order.get("CUST_PH")
                temp["STR_ID"] = order.get("STR_ID")
                temp["OD_STR_NM"] = order.get("OD_STR_NM")
                temp["OD_DATE"] = order.get("OD_DATE")
                temp["OD_TYPE"] = order.get("OD_TYPE")
                temp["OMS_OD_STS"] = order.get("OMS_OD_STS")
                temp["OD_TL_AMT"] = order.get("OD_TL_AMT")
                temp["OD_TX_AMT"] = order.get("OD_TX_AMT")
                temp["OD_NT_AMT"] = order.get("OD_NT_AMT")
                temp["item_info"] = order.get("item_info")
                template = Template(template_content)
                rendered_html = template.render(Context(temp))
                html = html + rendered_html
            response["data"] = html
            response["message"] = "Picklist Created Sucessfully."
            path = os.path.join(settings.MEDIA_ROOT +
                                "/" + str(file_name))
            if os.path.exists(path):
                os.remove(path)
            else:
                logger.info("Picklist html is deleted.")
        except Exception:
            response["data"] = ""
            response["message"] = "Template not Found."
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        return Response(response)


class ShipmentView(ListModelMixin, GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = queryset = ShipmentMaster.objects.filter(
        IS_GENERATED=True).order_by('-OD_SHP_ID')
    serializer_class = ShipmentListSerializer

    def __init__(self):
        self.columns = {
            "OD_SHP_STS": "Status",
            "OD_SHIP_CODE": "Picking Id",
            "MUL_OD_ID": "Order Id",
            "MUL_OD_STR_NM": "Store Name",
            "TOT_PICK_QTY": "Quantity",
            "TOT_AMT": "Total Amount",
            "TOT_NET_AMT": "Net Amount",
            "TOT_TAX_AMT": "Tax Amount",
            "TOT_DIS_AMT": "Discount Amount",
            "CRT_DT": "Shipment Start Date"
        }

        self.column_type = {
            "OD_SHP_STS": "status",
            "OD_SHIP_CODE": "str",
            "MUL_OD_ID": "order_id",
            "MUL_OD_STR_NM": "str",
            "TOT_PICK_QTY": "qty",
            "TOT_AMT": "price-left",
            "TOT_NET_AMT": "price-left",
            "TOT_TAX_AMT": "price-left",
            "TOT_DIS_AMT": "price-left",
            "CRT_DT": "Datetime"
        }

    def get_queryset(self):
        shipping_data = ItemShipmentList.objects.filter(
            OD_SHP_ID_id__in=self.queryset.values_list("OD_SHP_ID", flat=True),\
            OD_ID__OMS_OD_STS__in=["ready_to_pick", "ready_for_pickup", "on hold"]).values_list("OD_SHP_ID", flat=True)
        queryset = self.queryset.filter(OD_SHP_ID__in=list(set(shipping_data)))
        return queryset

    def get(self, request, *args, **kwargs):
        request_data = request.GET
        page = request_data.get('page', 1)
        page_size = request_data.get('page_size', 10)
        page = int(page)
        search = request_data.get('search', '')
        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('search', None)
        copy_request_data.pop('page', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('order_id', None)

        if (len(copy_request_data) > 0) or (len(search) > 0 or request_data.get('ordering') is not None):
            data = shipment_filter(int(page), int(
                page_size), search, copy_request_data, request_data.get('ordering'))
            response = {
                "total": data[1],
                "page": int(page),
                "page_size": int(page_size),
                "results": data[0],
                "columns": self.columns,
                "column_type": self.column_type
            }
            return Response(response)
        else:
            return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data["columns"] = self.columns
        response.data["column_type"] = self.column_type
        return response


class ShipmentDeleteMultipleView(GenericAPIView):
    '''Brand multiple status update'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ShipmentListSerializer

    def validate_ids(self, id_list):
        '''order validate id'''
        for each_id in id_list:
            try:
                ShipmentMaster.objects.get(OD_SHIP_CODE=each_id)
            except (ShipmentMaster.DoesNotExist, ValidationError):
                return False
        return True

    @swagger_auto_schema(tags=['Order'], operation_description="multiple delete Shipment",
                         operation_summary="Shipment multiple delete",
                         request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of Ids',
                                  items=openapi.Items
                                  (type=openapi.TYPE_STRING, description='Shipment Id'))},
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
                ShipmentMaster.objects.filter(
                    OD_SHIP_CODE__iexact=each_id).delete()
                PicklistMaster.objects.filter(
                    OD_SHP_ID__OD_SHIP_CODE__iexact=each_id).delete()
                ItemShipmentList.objects.filter(
                    OD_SHP_ID__OD_SHIP_CODE__iexact=each_id).delete()
                OrderCrates.objects.filter(
                    OD_SHP_ID__OD_SHIP_CODE__iexact=each_id).delete()
            logger.info("Shipment Deleted successfully")
            message = "Shipment Deleted."
            response['message'] = message
            sts = status.HTTP_200_OK

        else:
            response['message'] = "Invalid Id"
            sts = status.HTTP_400_BAD_REQUEST

        return Response(response, status=sts)


def calculate_tot_qty_tot_amt_net_amt_dis_amt(shipment_id):
    '''Calculate total qty, total amt, net amt, disc amt'''
    new_total_net_amount = ItemPicklist.objects.filter(OD_PICK_ID__in=ItemShipmentList.objects.filter(
        OD_SHP_ID=shipment_id).values_list('OD_PICK_ID', flat=True)).aggregate(tot=Sum('ITM_PICK_MRP'))['tot']
    tax_disc_ship_total_amount = OrderMaster.objects.filter(OD_ID__in=ItemShipmentList.objects.filter(
        OD_SHP_ID=shipment_id).values_list('OD_ID', flat=True)).aggregate(tax_amt=Sum('OD_TX_AMT'), disc_amt=Sum('OD_DIS_AMT'), ship_amt=Sum('OD_SHP_AMT'))
    new_tax_amt = tax_disc_ship_total_amount['tax_amt']
    new_disc_amt = abs(tax_disc_ship_total_amount['disc_amt'])
    new_ship_amt = tax_disc_ship_total_amount['ship_amt']
    new_total_amt = new_total_net_amount + new_ship_amt + new_tax_amt
    new_net_amt = new_total_net_amount + new_disc_amt
    tot_qty = ItemShipmentList.objects.filter(OD_SHP_ID=shipment_id).aggregate(
        sum_qty=Sum('ITM_SHP_GRN_QTY'))['sum_qty']
    order_instance = OrderMaster.objects.filter(OD_ID__in=ItemShipmentList.objects.filter(
        OD_SHP_ID=shipment_id).distinct('OD_ID').values_list('OD_ID', flat=True))
    multiple_store_name = ','.join(order_instance.distinct(
        'OD_STR_NM').values_list('OD_STR_NM', flat=True))
    order_id = ','.join(order_instance.distinct(
        'CU_OD_ID').values_list('CU_OD_ID', flat=True))
    return tot_qty, new_net_amt, new_total_amt, new_tax_amt, new_disc_amt, order_id, multiple_store_name


class GeneratePickList(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ship_code = request.GET.get('OD_SHIP_CODE')
        order_id = request.GET.get('CU_OD_ID', '')
        response = {}
        if ship_code and order_id:
            item_shp_instance = ItemShipmentList.objects.filter(
                OD_ID__CU_OD_ID__iexact=order_id, OD_SHP_ID__OD_SHIP_CODE__iexact=ship_code).first()
            order_shipment_serializer = GenerateItemShipmentGetSerializer(
                item_shp_instance, context={"user": request, 'order_id': order_id})
            stat = status.HTTP_200_OK
            response_data = order_shipment_serializer.data
            response['results'] = response_data
        else:
            response['results'] = "Either ship_code / order id not provided!"
            stat = status.HTTP_200_OK
        return Response(response, status=stat)

    def validate_order_ids(self, order_ids):
        '''Validate order ids'''
        for id in order_ids:
            try:
                OrderMaster.objects.get(CU_OD_ID__iexact=id)
            except Exception:
                return False
        return True

    def item_info_get(self, item_info):
        '''Get the item info'''
        if item_info:
            return item_info
        else:
            return None

    def send_mail_for_comment_on_picklist_generate(self, order_instance, comment):
        '''Send mail for comment on picklist generate'''
        if str(order_instance.OD_TYPE).lower() != 'dnb order':
            update_comment_on_verify.delay(
                order_instance.CH_OD_ID, order_instance.OD_STS, comment)

    def post(self, request, *args, **kwargs):
        order_ids = request.data.get('CU_OD_ID', [])
        bsn_id = self.request.GET.get("ID_BSN_UN", 0)
        ship_starts_with = None
        check_order_flag = self.validate_order_ids(order_ids)
        response = {}
        if bsn_id:
            global_obj = GlobalSetting.objects.filter(
                ID_GB_STNG=BusinessUnitSetting.objects.filter(
                ID_BSN_UN=bsn_id).first()).first()
            ship_starts_with = global_obj.PK_OD_STRT_WITH
        if check_order_flag:
            ship_item = ""
            shipment_dict = {
                "OD_SHIP_CODE": create_next_code(name="shipment", starts_with_name=ship_starts_with),
                "OD_SHP_TRK_CMP": '',
                "OD_SHP_ROUT_CODE": '',
                "OD_SHP_STS": "Picking-In Progress",
                "IS_GENERATED": True
            }
            logger.info("Shipping Dict : %s", shipment_dict)
            ship_item = ShipmentMaster.objects.create(**shipment_dict)
            for od_id in order_ids:
                item_ship_instance = ItemShipmentList.objects.filter(
                    OD_SHP_ID__IS_GENERATED=True, OD_ID__CU_OD_ID__icontains=od_id)
                if item_ship_instance.exists():
                    response['message'] = "Shipment already generated for this order!"
                    response['CU_OD_ID'] = order_ids
                    response['OD_ID_MUL'] = ','.join(order_ids)
                    response['OD_SHP_ID'] = item_ship_instance.first(
                    ).OD_SHP_ID.OD_SHP_ID
                    response['OD_SHIP_CODE'] = item_ship_instance.first(
                    ).OD_SHP_ID.OD_SHIP_CODE
                    response['OD_SHP_STS'] = item_ship_instance.first(
                    ).OD_SHP_ID.OD_SHP_STS
                else:
                    logger.info("Shipment creation instance : %s", ship_item)
                    order_instance = OrderMaster.objects.filter(
                        CU_OD_ID__iexact=od_id).first()
                    pick_list = PicklistMaster.objects.filter(
                        OD_ID__CU_OD_ID__iexact=od_id)
                    pick_list.update(OD_SHP_ID=ship_item.OD_SHP_ID,
                                     OD_PICK_BY=request.user.id)
                    order_items = OrderItemDetails.objects.filter(
                        OD_ID__CU_OD_ID__iexact=od_id)
                    for od_itm in order_items:
                        item_info = Item.objects.filter(
                            AS_ITM_SKU=od_itm.OD_ITM.AS_ITM_SKU).first()
                        shipment_items_dict = {
                            "OD_ID": order_instance,
                            "OD_ITM_ID": od_itm,
                            "ITM_ID": self.item_info_get(item_info),
                            "OD_PICK_ID": pick_list.first(),
                            "OD_SHP_ID": ship_item
                        }
                        itemshipment_instance = ItemShipmentList.objects.create(
                            **shipment_items_dict)
                        logger.info("Item Shipment creation instance : %s",
                                    itemshipment_instance)
                    comment = "Picklist Generated"
                    self.send_mail_for_comment_on_picklist_generate(
                        order_instance, comment)
                    OrderActivity.objects.create(
                        OD_ACT_OD_MA_ID=order_instance, OD_ACT_CMT=comment, OD_CUST=order_instance.OD_CUST, OD_ACT_STATUS="Picking", OD_ACT_CRT_AT=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), OD_ACT_CRT_BY=request.user.get_full_name())
                    send_pick_notification(order_instance, type="Picking Stage", user=request.user)
                    get_all_serialzied_data = OrderElasticDataSerializer(
                        order_instance).data
                    order_save(get_all_serialzied_data,
                               settings.ES_ORDER_INDEX, order_instance.OD_ID)
                response['message'] = "Picklist Generated Successfully"
                response['OD_ID_MUL'] = ','.join(order_ids)
                response['CU_OD_ID'] = order_ids
                response['OD_SHP_ID'] = ship_item.OD_SHP_ID
                response['OD_SHIP_CODE'] = ship_item.OD_SHIP_CODE
                response['OD_SHP_STS'] = ship_item.OD_SHP_STS
            tot_qty, new_net_amt, new_total_amt, new_tax_amt, new_disc_amt, order_id, multiple_store_name = calculate_tot_qty_tot_amt_net_amt_dis_amt(
                ship_item.OD_SHP_ID)
            ShipmentMaster.objects.filter(
                OD_SHP_ID=ship_item.OD_SHP_ID).update(MUL_OD_ID=order_id, MUL_OD_STR_NM=multiple_store_name, TOT_PICK_QTY=tot_qty, TOT_AMT=new_total_amt, TOT_NET_AMT=new_net_amt, TOT_TAX_AMT=new_tax_amt, TOT_DIS_AMT=new_disc_amt)
            stat = status.HTTP_200_OK
        else:
            response['message'] = "Order id does not exist!"
            stat = status.HTTP_400_BAD_REQUEST
        return Response(response, status=stat)


class SearchPickedProduct(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        picklist_id = request.GET.get("OD_PICK_ID")
        order_id = request.GET.get("CU_OD_ID")
        picking_items = ItemShipmentList.objects.filter(OD_PICK_ID_id=picklist_id,
                                                        OD_ID__CU_OD_ID=order_id)
        if picking_items:
            serializer = ScanPickItemSerializer(picking_items, many=True)
            return Response({"result": serializer.data}, status=status.HTTP_200_OK)
        return Response({"result": ""}, status=status.HTTP_400_BAD_REQUEST)


complete_order_response = {
    "200": openapi.Response(
        description="Order Completed Successfully",
    ),
    "400": openapi.Response(
        description="Please provide an order ID"
    )
}


class SaveDraft(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def changes_amount_calculate(self, check_order, net_amount, tot_amount):
        '''Change amount calculate'''
        if check_order.first().OD_DIS_AMT:
            net_amount += abs(float(check_order.first().OD_DIS_AMT))
        if check_order.first().OD_SHP_AMT:
            net_amount -= float(check_order.first().OD_SHP_AMT)
            tot_amount += float(check_order.first().OD_SHP_AMT)
        if check_order.first().OD_TX_AMT:
            net_amount -= float(check_order.first().OD_TX_AMT)             
        return net_amount, tot_amount

    @swagger_auto_schema(tags=['Order'], operation_description="Complete Order", operation_summary="Complete Order", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "CRT_ID": openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of Crate ID',
                                     items=openapi.Items(type=openapi.TYPE_INTEGER, description='Id')),
            "CU_OD_ID": openapi.Schema(type=openapi.TYPE_STRING, description='Order Id')
        }
    ), responses=complete_order_response)
    def post(self, request, *args, **kwargs):
        request_datas = request.data.get("item_detail_field")
        for request_data in request_datas:
            order_id = request_data.get("CU_OD_ID")
            shipment_id = request_data.get("OD_SHP_ID")
            picker_id = request_data.get("OD_PICKER_ID")
            shipment_order_products = request_data.get("itemfield", [])
            check_order = OrderMaster.objects.filter(
                CU_OD_ID__iexact=order_id, OMS_OD_STS="ready_to_pick")
            if check_order:
                if len(shipment_order_products) > 0:
                    net_amount = 0.0
                    tot_amount = 0.0
                    for shipment_order in shipment_order_products:
                        tot_amount += float(shipment_order.get('ITM_PICK_MRP'))
                        net_amount += float(shipment_order.get('ITM_PICK_MRP'))
                        update_shipment_order_item = {
                            "ITM_SHP_QTY": shipment_order['OD_ITM_QTY'],
                            "ITM_SHP_SORT": shipment_order['ITM_SHP_SORT'],
                            "ITM_SHP_GRN_QTY": shipment_order['ITM_SHP_GRN_QTY']
                        }
                        ItemShipmentList.objects.filter(OD_ID__CU_OD_ID__iexact=order_id,
                                                        OD_ITM_ID_id=shipment_order.get(
                                                            "OD_ITM_ID"),
                                                        OD_SHP_ID_id=shipment_id).update(**update_shipment_order_item)
                        ItemPicklist.objects.filter(ITM_PICK_ID=shipment_order.get("ITM_PICK_ID"), ITM_ID__AS_ITM_SKU=shipment_order.get('AS_ITM_SKU')).update(
                            ITM_QTY_SORT=shipment_order['ITM_SHP_SORT'],
                            ITM_PICK_MRP=shipment_order['ITM_PICK_MRP'],
                            ITM_OR_MRP=shipment_order['ITM_OR_MRP'])
                    net_amount, tot_amount = self.changes_amount_calculate(
                        check_order, net_amount, tot_amount)
                    order_instance = check_order.first()
                    order_instance.OD_NT_AMT = net_amount
                    order_instance.OD_TL_AMT = float(tot_amount)
                    order_instance.OD_PD_AMT = float(tot_amount)
                    order_instance.save()
                    tot_qty, new_net_amt, new_total_amt, new_tax_amt, new_disc_amt, order_id, multiple_store_name = calculate_tot_qty_tot_amt_net_amt_dis_amt(
                        shipment_id)
                    # Update picker and assign new picker
                    PicklistMaster.objects.filter(OD_PICK_ID__in=ItemShipmentList.objects.filter(
                        OD_SHP_ID_id=shipment_id).values_list('OD_PICK_ID', flat=True)).update(OD_PICK_BY_id=picker_id)
                    all_data_shipment = ItemShipmentList.objects.filter(OD_ID__CU_OD_ID__iexact=order_id,
                                                                        OD_SHP_ID=shipment_id).distinct('OD_ID')
                    ShipmentMaster.objects.filter(
                        OD_SHP_ID=shipment_id).update(MUL_OD_ID=order_id, MUL_OD_STR_NM=multiple_store_name, TOT_PICK_QTY=tot_qty, TOT_AMT=new_total_amt, TOT_NET_AMT=new_net_amt, TOT_TAX_AMT=new_tax_amt, TOT_DIS_AMT=new_disc_amt)
                    serializer = GenerateItemShipmentGetSerializer(
                        all_data_shipment, context={"user": request}, many=True)
                    data = {
                        "message": "Picking product data save successfully.",
                        "api_status": serializer.data
                    }
                    serialzied_data = OrderElasticDataSerializer(
                        check_order.first()).data
                    order_save(serialzied_data,
                               settings.ES_ORDER_INDEX, check_order.first().OD_ID)
                    return Response(data, status=status.HTTP_200_OK)
                else:
                    data = {
                        "message": "Order Products not found.",
                        "api_status": {}
                    }
            else:
                data = {
                    "message": "Unable to Save Draft. Order Moved to Invoice Stage.",
                    "api_status": {}
                }
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class CratesView(GenericAPIView):
    '''Crate View'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Order'], operation_description="Get Crate List", operation_summary="Get Crate List", manual_parameters=[openapi.Parameter('CU_OD_ID', openapi.IN_QUERY,
                                                                                                                                                          description="Order id",
                                                                                                                                                          type=openapi.TYPE_STRING),
                                                                                                                                        openapi.Parameter('search', openapi.IN_QUERY,
                                                                                                                                                          description="Search crate",
                                                                                                                                                          type=openapi.TYPE_STRING)])
    def get(self, request, *args, **kwargs):
        order_id = request.GET.get("CU_OD_ID", "")
        search = request.GET.get("search", "")
        if order_id:
            data_crate = OrderCrates.objects.filter(
                OD_ID__CU_OD_ID__icontains=order_id).distinct('AC_ID')
            if search:
                data_crate = data_crate.filter(
                    AC_ID__CRT_ID__CRT_CD__icontains=search)
            if data_crate:
                crate_data = CratesSerializer(
                    data_crate, context={'CU_OD_ID': order_id}, many=True).data
                result = {
                    "message": "Crate Fetched",
                    "crate_list": crate_data
                }
            else:
                result = {
                    "message": "No Data Found.",
                    "crate_data": []
                }
            return Response(result, status=status.HTTP_200_OK)
        else:
            result = {
                "message": "Order ID cannot not be blank!!!"
            }
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

    def save_crate_details(self, od_inst, crate_list):
        '''Save crate details'''
        message = None
        loc_obj = Location.objects.filter(
            Q(MAG_MAGEWORX_STR_ID=od_inst.first().STR_ID) | Q(id=od_inst.first().STR_ID))
        for crt_id in crate_list:
            crt_obj = OrderCrates.objects.filter(
                AC_ID__CRT_ID=crt_id, AC_ID__STR_ID=loc_obj.first().id)
            if not crt_obj.exists():
                crt_inst = Crates.objects.filter(CRT_ID=crt_id)
                if crt_inst.exists():
                    asso_crt_inst = AssociateCrate.objects.filter(
                        CRT_ID=crt_id, STR_ID=loc_obj.first().id)
                    if asso_crt_inst.exists():
                        OrderCrates.objects.create(OD_ID=od_inst.first(), OD_SHP_ID=ItemShipmentList.objects.filter(
                            OD_ID=od_inst.first().OD_ID).first().OD_SHP_ID, OD_PICK_ID=PicklistMaster.objects.filter(OD_ID=od_inst.first().OD_ID).first(), AC_ID=asso_crt_inst.first())
            else:
                message = str(crt_obj.first().AC_ID.CRT_ID.CRT_CD) + \
                    " code already exists in this store!!!"
                break
        return message

    @swagger_auto_schema(tags=['Order'], operation_description="Complete Order", operation_summary="Complete Order", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "CRT_ID": openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of Crate ID',
                                     items=openapi.Items(type=openapi.TYPE_INTEGER, description='Id')),
            "CU_OD_ID": openapi.Schema(type=openapi.TYPE_STRING, description='Order Id')
        }
    ), responses=complete_order_response)
    def post(self, request, *args, **kwargs):
        response = {}
        request_data = request.data
        crate_list = request_data.get("CRT_ID")
        order_id = request_data.get("CU_OD_ID")
        try:
            if crate_list and order_id:
                od_inst = OrderMaster.objects.filter(CU_OD_ID__iexact=order_id)
                if od_inst.exists():
                    message = self.save_crate_details(od_inst, crate_list)
                    if message:
                        response['message'] = message
                    else:
                        response['message'] = "Crate Created Successfully"
                    stat = status.HTTP_200_OK
                else:
                    response['message'] = "Order id does not exist!!!"
                    stat = status.HTTP_400_BAD_REQUEST
            else:
                response['message'] = "Either crate id / order id not provided!!!"
                stat = status.HTTP_400_BAD_REQUEST
            return Response(response, status=stat)
        except Exception:
            results = {
                "message": "Crate Code is Available. "
            }
            return Response(results, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Order'], operation_description="Complete Order", operation_summary="Complete Order", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "CRT_CD": openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of Crate ID',
                                     items=openapi.Items(type=openapi.TYPE_INTEGER, description='Ids')),
            "CU_OD_ID": openapi.Schema(type=openapi.TYPE_STRING, description='Order Id')
        }
    ), responses=complete_order_response)
    def delete(self, request, *args, **kwargs):
        crate_list = request.data.get("CRT_CD")
        order_id = request.data.get("CU_OD_ID")
        if crate_list and order_id:
            order_instance = OrderMaster.objects.filter(
                CU_OD_ID__iexact=order_id).first()
            if order_instance:
                OrderCrates.objects.filter(
                    AC_ID__STR_ID__MAG_MAGEWORX_STR_NM__iexact=order_instance.OD_STR_NM, AC_ID__CRT_ID__CRT_CD__in=crate_list).delete()
                data_crate = OrderCrates.objects.filter(
                    OD_ID__CU_OD_ID__icontains=order_id).distinct('AC_ID')
                results = {
                    "message": "Crate Deleted Successfully.",
                    "results": CratesSerializer(
                        data_crate, context={'CU_OD_ID': order_id}, many=True).data
                }
            else:
                results = {
                    "message": "Order does not exist!!!",
                    "results": []
                }
            return Response(results, status=status.HTTP_200_OK)
        else:
            results = {
                "message": "Crate ID / Order ID should not be blanked."
            }
            return Response(results, status=status.HTTP_400_BAD_REQUEST)
