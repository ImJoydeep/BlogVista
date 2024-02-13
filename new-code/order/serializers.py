import logging
import requests
import json
from django.conf import settings
from datetime import datetime, timedelta
from django.db.models import Sum
from rest_framework import serializers
from product.models.models_item import Item, ItemImageMapping
from order.order_elastic import order_save
from store.models import Location
from product.models.models_item_stock import ItemBarcode, ItemManufacturer, ItemSupplier
from taxonomy.taxonomy_magento_integration import magento_login
from product.views.product_es_sell_price import get_regular_price
from item_stock.models import ItemInventory
from celery import shared_task
from order.models import ItemPicklist, ItemShipmentList, OrderBillingAddress, OrderHoldUnholdPreviousStatus, OrderInvoice, OrderItemDetails, OrderMaster, OrderPaymentDetails, OrderShippingAddress, Customer, OrderActivity, \
    Crates, AssociateCrate, PicklistMaster, Reason,PicksheetNote,PicksheetNoteStores,PicksheetNoteItemSKU

on_hold_key = 'on hold'

logger = logging.getLogger(__name__)


class OrderMasterSerializer(serializers.ModelSerializer):
    '''Order Master Serializer'''
    OD_TL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_DIS_AMT = serializers.SerializerMethodField()
    OD_NT_AMT = serializers.SerializerMethodField()
    OD_PD_AMT = serializers.SerializerMethodField()
    OD_SHP_AMT = serializers.SerializerMethodField()
    OD_TX_AMT = serializers.SerializerMethodField()
    OD_SA_PH = serializers.SerializerMethodField()
    OD_ITM_AMT_REF = serializers.SerializerMethodField()
    OD_BA_CT = serializers.SerializerMethodField()
    OD_SA_CT = serializers.SerializerMethodField()
    OD_BA_ST = serializers.SerializerMethodField()
    OD_BA_PIN = serializers.SerializerMethodField()
    OD_SA_PIN = serializers.SerializerMethodField()
    OD_STS = serializers.SerializerMethodField()
    OD_BA_ST = serializers.SerializerMethodField()
    OD_SA_ST = serializers.SerializerMethodField()
    OD_CUS_NM = serializers.SerializerMethodField()
    OMS_OD_STS = serializers.SerializerMethodField(read_only=True)
    OD_RQD_DT = serializers.SerializerMethodField(read_only=True)
    PREV_STATE = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)
    OD_SHP_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHIP_CODE = serializers.SerializerMethodField(read_only=True)
    OD_IS_GEN_PICK = serializers.SerializerMethodField(read_only=True)
    OD_PICK_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHP_STS = serializers.SerializerMethodField(read_only=True)
    OD_CRATE_COUNT = serializers.SerializerMethodField(read_only=True)
    OD_PICK_BY = serializers.SerializerMethodField(read_only=True)
    OD_TOT_QTY = serializers.SerializerMethodField(read_only=True)
    OD_PICKER_ID = serializers.SerializerMethodField(read_only=True)
    PT_MD_NM = serializers.SerializerMethodField(read_only=True)

    def get_PT_MD_NM(self, obj):
        if obj.PT_MD_NM == "checkmo":
            return "Check/Money Order"
        elif obj.PT_MD_NM == "paypal":
            return "Paypal"
        elif obj.PT_MD_NM == "cc":
            return "Credit Card"
        else:
            return obj.PT_MD_NM

    def get_OD_PICKER_ID(self, obj):
        try:
            if ItemShipmentList.objects.filter(OD_ID=obj.OD_ID).first():
                return ItemShipmentList.objects.filter(OD_ID=obj.OD_ID).first().OD_PICK_ID.OD_PICK_BY.id
            return None
        except Exception:
            return None

    def get_OD_TOT_QTY(self, obj):
        try:
            if obj.OMS_OD_STS == "ready_for_pickup":
                return str(int(ItemShipmentList.objects.filter(OD_ID=obj.OD_ID).aggregate(sum_qty=Sum('ITM_SHP_GRN_QTY'))['sum_qty']))
            else:
                return str(int(OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).aggregate(sum_qty=Sum('OD_ITM_QTY'))['sum_qty']))
        except Exception:
            return str(int(OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).aggregate(sum_qty=Sum('OD_ITM_QTY'))['sum_qty']))

    def get_OD_PICK_BY(self, obj):
        try:
            if obj.picklistmaster_set.first():
                return obj.picklistmaster_set.first().OD_PICK_BY.get_full_name()
            else:
                return ""
        except Exception:
            return ""

    def get_OD_SHP_STS(self, obj):
        try:
            if obj.itemshipmentlist_set.first():
                return str(obj.itemshipmentlist_set.first().OD_SHP_ID.OD_SHP_STS)
            return ""
        except Exception:
            return ""

    def get_OD_CRATE_COUNT(self, obj):
        try:
            if obj.itemshipmentlist_set.first():
                return obj.itemshipmentlist_set.first().OD_SHP_ID.OD_CRATE_COUNT
            return None
        except Exception:
            return None

    def get_OD_PICK_ID(self, obj):
        try:
            if obj.picklistmaster_set.first():
                return obj.picklistmaster_set.first().OD_PICK_ID
            return None
        except Exception:
            return None

    def get_OD_SHP_ID(self, obj):
        try:
            if obj.itemshipmentlist_set.first():
                return obj.itemshipmentlist_set.first().OD_SHP_ID.OD_SHP_ID
            return None
        except Exception:
            return None

    def get_OD_IS_GEN_PICK(self, obj):
        try:
            if obj.itemshipmentlist_set.first():
                return obj.itemshipmentlist_set.first().OD_SHP_ID.IS_GENERATED
            return False
        except Exception:
            return False

    def get_OD_SHIP_CODE(self, obj):
        try:
            if obj.itemshipmentlist_set.first():
                return str(obj.itemshipmentlist_set.first().OD_SHP_ID.OD_SHIP_CODE)
            return ""
        except Exception:
            return ""

    def get_OD_STR_NM(self, obj):
        if obj.STR_ID:
            store_name = Location.objects.filter(
                MAG_MAGEWORX_STR_ID=obj.STR_ID)
            if store_name.exists():
                return store_name.first().MAG_MAGEWORX_STR_NM
            else:
                return ""
        else:
            return ""

    def get_PREV_STATE(self, obj):
        if obj.OMS_OD_STS:
            value = ""
            if obj.OMS_OD_STS == on_hold_key:
                previous_state_instance = OrderHoldUnholdPreviousStatus.objects.filter(
                    OD_HD_UH_CRNT_STAT=on_hold_key, OD_HD_UH_OD_ID=obj.CU_OD_ID)
                if previous_state_instance:
                    value = previous_state_instance.first().OD_OMS_STATUS_PREV
            return value
        else:
            return ""

    def get_OD_RQD_DT(self, obj):
        if obj.OD_DATE:
            od_date = str(obj.OD_DATE)[:10]
            date = datetime.strptime(od_date, "%Y-%m-%d")
            modified_date = date + timedelta(days=1)
            return datetime.strftime(modified_date, "%Y-%m-%d")
        else:
            return ""

    def get_OMS_OD_STS(self, obj):
        if obj:
            if obj.OMS_OD_STS in ['new', 'void']:
                return obj.OMS_OD_STS.title()
            elif obj.OMS_OD_STS == 'ready_to_pick':
                shipment_data = ItemShipmentList.objects.filter(
                    OD_ID=obj.OD_ID).first()
                try:
                    if shipment_data and shipment_data.OD_SHP_ID.IS_GENERATED:
                        return "Picking"
                    else:
                        return "Ready to Pick"
                except Exception:
                    return "Ready to Pick"
            elif obj.OMS_OD_STS == 'ready_for_pickup':
                return "Ready for Pickup"
            elif obj.OMS_OD_STS == on_hold_key:
                return "Attention"
            elif obj.OMS_OD_STS == 'complete':
                return "Completed"

    def get_OD_TL_AMT(self, obj):
        return f"{obj.OD_TL_AMT:.2f}"

    def get_OD_DIS_AMT(self, obj):
        if obj.OD_DIS_AMT:
            return f"{abs(obj.OD_DIS_AMT):.2f}"
        else:
            return f"{0:.2f}"

    def get_OD_NT_AMT(self, obj):
        return f"{obj.OD_NT_AMT:.2f}"

    def get_OD_PD_AMT(self, obj):
        temp = OrderPaymentDetails.objects.filter(OD_PAY_OD_id=obj.OD_ID).first()
        try:
            if temp and temp.IS_CAPTURED:
                paid_amount = obj.OD_TL_AMT
                return f"{paid_amount:.2f}"
            return 0.00
        except Exception:
            return 0.00

    def get_OD_SHP_AMT(self, obj):
        if obj.OD_SHP_AMT:
            return f"{obj.OD_SHP_AMT:.2f}"
        else:
            return f"{0:.2f}"

    def get_OD_TX_AMT(self, obj):
        try:
            return f"{obj.OD_TX_AMT:.2f}"
        except Exception:
            return str(0.00)

    def get_OD_SA_PH(self, obj):
        get_phone = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if get_phone:
            return get_phone.OD_SA_PH
        else:
            return None

    def get_OD_ITM_AMT_REF(self, obj):
        amount_refund = OrderItemDetails.objects.filter(
            OD_ITM_ODR_ID=obj.CH_OD_ID).aggregate(
                total_amount=Sum('OD_ITM_AMT_REF'))
        if amount_refund["total_amount"] is not None:
            return "{:.2f}".format(amount_refund["total_amount"])
        return amount_refund["total_amount"]

    def get_OD_BA_CT(self, obj):
        get_city = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=obj.OD_ID).first()
        if get_city:
            return get_city.OD_BA_CT
        else:
            return None

    def get_OD_SA_CT(self, obj):
        get_city = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if get_city:
            return get_city.OD_SA_CT
        else:
            return None

    def get_OD_BA_ST(self, obj):
        get_addess = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=obj.OD_ID).first()
        if get_addess:
            return get_addess.OD_BA_ST
        else:
            return None

    def get_OD_BA_PIN(self, obj):
        get_pincode = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=obj.OD_ID).first()
        if get_pincode:
            return get_pincode.OD_BA_PIN
        else:
            return None

    def get_OD_SA_PIN(self, obj):
        get_pincode = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if get_pincode:
            return get_pincode.OD_SA_PIN
        else:
            return None

    def get_OD_STS(self, obj):
        return obj.OD_STS.title()

    def get_OD_CUS_NM(self, obj):
        return obj.OD_CUS_NM.title()

    def get_OD_BA_ST(self, obj):
        get_billing_addr = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=obj.OD_ID).first()
        if get_billing_addr:
            return get_billing_addr.OD_BA_ST.title()
        else:
            return None

    def get_OD_SA_ST(self, obj):
        get_shipping_addr = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if get_shipping_addr:
            return get_shipping_addr.OD_SA_ST.title()
        else:
            return None

    class Meta:
        model = OrderMaster
        fields = '__all__'


class OrderItemListSerializer(serializers.ModelSerializer):
    OD_STS = serializers.SerializerMethodField(read_only=True)
    OD_TYPE = serializers.SerializerMethodField(read_only=True)
    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    OD_ITM = serializers.SerializerMethodField(read_only=True)
    OD_CUS_NM = serializers.SerializerMethodField(read_only=True)
    OD_CUS_EMAIL = serializers.SerializerMethodField(read_only=True)
    OD_QTY = serializers.SerializerMethodField(read_only=True)
    OD_TL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_DATE = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)
    OD_SA_PH = serializers.SerializerMethodField(read_only=True)
    OD_NT_AMT = serializers.SerializerMethodField(read_only=True)
    OD_DIS_AMT = serializers.SerializerMethodField(read_only=True)
    OD_TX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_PD_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_AMT_REF = serializers.SerializerMethodField(read_only=True)
    PT_MD_NM = serializers.SerializerMethodField(read_only=True)
    OD_BA_CT = serializers.SerializerMethodField(read_only=True)
    OD_SA_CT = serializers.SerializerMethodField(read_only=True)
    OD_BA_ST = serializers.SerializerMethodField(read_only=True)
    OD_SA_ST = serializers.SerializerMethodField(read_only=True)
    OD_BA_PIN = serializers.SerializerMethodField(read_only=True)
    OD_SA_PIN = serializers.SerializerMethodField(read_only=True)
    OD_INVC_NUM = serializers.SerializerMethodField(read_only=True)
    OD_SHP_NUM = serializers.SerializerMethodField(read_only=True)
    OD_INST = serializers.SerializerMethodField(read_only=True)

    def get_OD_STS(self, obj):
        order_obj = OrderMaster.objects.filter(OD_ID=obj.OD_ID).first()
        if order_obj:
            return order_obj.OD_STS
        else:
            return None

    def get_OD_TYPE(self, obj):
        order_obj = OrderMaster.objects.filter(OD_ID=obj.OD_ID).first()
        if order_obj:
            return order_obj.OD_TYPE
        else:
            return None

    def get_CU_OD_ID(self, obj):
        order_obj = OrderMaster.objects.filter(OD_ID=obj.OD_ID).first()
        if order_obj:
            return order_obj.CU_OD_ID
        else:
            return ""

    def get_OD_ITM(self, obj):
        order_item = OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).first()
        if order_item:
            if order_item.OD_ITM:
                return order_item.OD_ITM.NM_ITM
            else:
                return order_item.OD_ITM_NM
        else:
            return ""

    def get_OD_CUS_NM(self, obj):
        return obj.OD_CUS_NM.title()

    def get_OD_CUS_EMAIL(self, obj):
        return obj.OD_CUS_EMAIL

    def get_OD_QTY(self, obj):
        order_item_qty = OrderItemDetails.objects.filter(
            OD_ID=obj.OD_ID).first()
        if order_item_qty:
            return order_item_qty.OD_ITM_QTY
        else:
            return None

    def get_OD_TL_AMT(self, obj):
        order_item_total = OrderItemDetails.objects.filter(
            OD_ID=obj.OD_ID).first()
        if order_item_total:
            return order_item_total.OD_ITM_TOTL_AMT
        else:
            return ""

    def get_OD_DATE(self, obj):
        return obj.OD_DATE

    def get_OD_STR_NM(self, obj):
        return obj.OD_STR_NM

    def get_OD_SA_PH(self, obj):
        shipping_details = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if shipping_details:
            return shipping_details.OD_SA_PH
        else:
            return ""

    def get_OD_NT_AMT(self, obj):
        item_order_net_amount = OrderItemDetails.objects.filter(
            OD_ID=obj.OD_ID).first()
        if item_order_net_amount:
            return item_order_net_amount.OD_ITM_NET_AMT
        else:
            return None

    def get_OD_DIS_AMT(self, obj):
        item_discount_amount = OrderItemDetails.objects.filter(
            OD_ID=obj.OD_ID).first()
        if item_discount_amount:
            return item_discount_amount.OD_ITM_DSC_AMT
        else:
            return None

    def get_OD_TX_AMT(self, obj):
        item_tax_amount = OrderItemDetails.objects.filter(
            OD_ID=obj.OD_ID).first()
        if item_tax_amount:
            return item_tax_amount.OD_ITM_TAX_AMT
        else:
            return None

    def get_OD_PD_AMT(self, obj):
        return obj.OD_PD_AMT

    def get_OD_ITM_AMT_REF(self, obj):
        item_ref = OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).first()
        if item_ref:
            return item_ref.OD_ITM_AMT_REF
        else:
            return None

    def get_PT_MD_NM(self, obj):
        return obj.PT_MD_NM

    def get_OD_BA_CT(self, obj):
        billing_details = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=obj.OD_ID).first()
        if billing_details:
            return billing_details.OD_BA_CT
        else:
            return ""

    def get_OD_SA_CT(self, obj):
        shipping_details = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if shipping_details:
            return shipping_details.OD_SA_CT
        else:
            return ""

    def get_OD_BA_ST(self, obj):
        billing_details = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=obj.OD_ID).first()
        if billing_details:
            return billing_details.OD_BA_ST
        else:
            return ""

    def get_OD_SA_ST(self, obj):
        shipping_details = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if shipping_details:
            return shipping_details.OD_SA_ST
        else:
            return ""

    def get_OD_BA_PIN(self, obj):
        billing_details = OrderBillingAddress.objects.filter(
            OD_BA_OD_ID=obj.OD_ID).first()
        if billing_details:
            return billing_details.OD_BA_PIN
        else:
            return ""

    def get_OD_SA_PIN(self, obj):
        shipping_details = OrderShippingAddress.objects.filter(
            OD_SA_OD_ID=obj.OD_ID).first()
        if shipping_details:
            return shipping_details.OD_SA_PIN
        else:
            return ""

    def get_OD_INVC_NUM(self, obj):
        return obj.OD_INVC_NUM

    def get_OD_SHP_NUM(self, obj):
        return obj.OD_SHP_NUM

    def get_OD_INST(self, obj):
        return obj.OD_INST

    class Meta:
        model = OrderItemDetails
        fields = ['OD_STS', 'OD_TYPE', 'CU_OD_ID', 'OD_ITM', 'OD_CUS_NM', 'OD_CUS_EMAIL',
                  'OD_QTY', 'OD_TL_AMT', 'OD_DATE', 'OD_STR_NM', 'OD_SA_PH', 'OD_NT_AMT',
                  'OD_DIS_AMT', 'OD_TX_AMT', 'OD_PD_AMT', 'OD_ITM_AMT_REF', 'PT_MD_NM',
                  'OD_BA_CT', 'OD_SA_CT', 'OD_BA_ST', 'OD_SA_ST', 'OD_BA_PIN', 'OD_SA_PIN',
                  'OD_INVC_NUM', 'OD_SHP_NUM', 'OD_INST']


class OrderBillingAddressSerializer(serializers.ModelSerializer):

    OD_BA_CUST_NM = serializers.SerializerMethodField(read_only=True)

    def get_OD_BA_CUST_NM(self, obj):
        if obj.OD_BA_FN and obj.OD_BA_LN:
            full_name = f"{obj.OD_BA_FN} {obj.OD_BA_LN}"
        else:
            full_name = obj.OD_BA_OD_ID.OD_CUS_NM
        return full_name

    class Meta:
        model = OrderBillingAddress
        fields = '__all__'


class OrderShippingAddressSerializer(serializers.ModelSerializer):

    OD_SA_CUST_NM = serializers.SerializerMethodField(read_only=True)

    def get_OD_SA_CUST_NM(self, obj):
        if obj.OD_SA_FN and obj.OD_SA_LN:
            full_name = f"{obj.OD_SA_FN} {obj.OD_SA_LN}"
        else:
            full_name = obj.OD_SA_OD_ID.OD_CUS_NM
        return full_name

    class Meta:
        model = OrderShippingAddress
        fields = '__all__'

class PickSheetNoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = PicksheetNote
        fields = '__all__'
class OrderItemDetailsSerializer(serializers.ModelSerializer):

    OD_ITM_DSC_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_NET_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_OR_PR = serializers.SerializerMethodField(read_only=True)
    OD_ITM_TAX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_TOTL_AMT = serializers.SerializerMethodField(read_only=True)
    ITM_VDR_PRT_NO = serializers.SerializerMethodField(read_only=True)
    ITM_MDF_PRT_NO = serializers.SerializerMethodField(read_only=True)
    AS_ITM_SLUG = serializers.SerializerMethodField(read_only=True)
    MMS_NM = serializers.SerializerMethodField(read_only=True)
    ID_CD_BR_ITM = serializers.SerializerMethodField(read_only=True)
    ITM_IMG = serializers.SerializerMethodField(read_only=True)
    ITM_OR_MRP = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_GRN_QTY = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_SORT = serializers.SerializerMethodField(read_only=True)
    ITM_PICK_MRP = serializers.SerializerMethodField(read_only=True)
    ITM_PICK_ID = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_ID = serializers.SerializerMethodField(read_only=True)
    NT_DETAILS = serializers.SerializerMethodField(read_only=True)

    def get_NT_DETAILS(self, obj):
        to_day = datetime.now()
        try:
            store_id = Location.objects.filter(MAG_MAGEWORX_STR_ID=obj.OD_ID.STR_ID).first()
            store_note_list = PicksheetNoteStores.objects.filter(
                STR_ID=store_id.id).values_list("PSN_ID", flat=True)
            sku_note = PicksheetNoteItemSKU.objects.filter(
                ITM_SKU_ID=obj.OD_ITM.ID_ITM, PSN_ID__in=list(set(store_note_list)))
            if sku_note:
                if sku_note.first().PSN_ID.ST_DT and sku_note.first().PSN_ID.EN_DT:
                    note_detail = PicksheetNote.objects.filter(
                        PSN_ID=sku_note.first().PSN_ID.PSN_ID,
                        ST_DT__lte=to_day,
                        EN_DT__gte=to_day,
                        PSN_STS="A")
                else:
                    note_detail = PicksheetNote.objects.filter(
                        PSN_ID=sku_note.first().PSN_ID.PSN_ID,
                        PSN_STS="A")

                serializer = PickSheetNoteSerializer(note_detail, many=True).data
                return serializer
        except Exception:
            return ""

    def get_ITM_SHP_ID(self, obj):
        try:
            if obj:
                return ItemShipmentList.objects.filter(
                    OD_ID=obj.OD_ID, OD_ITM_ID=obj.OD_ITM_ID).first().ITM_SHP_ID
        except Exception:
            return None

    def get_ITM_PICK_ID(self, obj):
        try:
            if obj:
                item_ship = ItemShipmentList.objects.filter(
                    OD_ITM_ID=obj.OD_ITM_ID, OD_ID=obj.OD_ID).first()
                item_pick = ItemPicklist.objects.filter(
                    ITM_ID=item_ship.ITM_ID, OD_PICK_ID=item_ship.OD_PICK_ID).first()
                return item_pick.ITM_PICK_ID
        except Exception:
            return None

    def get_ITM_SHP_GRN_QTY(self, obj):
        try:
            if obj.itemshipmentlist_set.first():
                return obj.itemshipmentlist_set.first().ITM_SHP_GRN_QTY
            return None
        except Exception:
            return None

    def get_ITM_SHP_SORT(self, obj):
        try:
            return ItemShipmentList.objects.filter(
                OD_ITM_ID=obj.OD_ITM_ID).first().ITM_SHP_SORT
        except Exception:
            return None

    def get_ITM_PICK_MRP(self, obj):
        try:
            item_picklist = ItemPicklist.objects.filter(
                OD_PICK_ID=obj.OD_ID.picklistmaster_set.first().OD_PICK_ID,
                ITM_ID=obj.OD_ITM).first()
            if item_picklist:
                return item_picklist.ITM_PICK_MRP
            else:
                return None
        except Exception:
            return None

    def get_ITM_OR_MRP(self, obj):
        try:
            item_picklist = ItemPicklist.objects.filter(
                OD_PICK_ID=obj.OD_ID.picklistmaster_set.first().OD_PICK_ID,
                ITM_ID=obj.OD_ITM).first()
            if item_picklist:
                return item_picklist.ITM_OR_MRP
            else:
                return None
        except Exception:
            return None

    def get_ITM_IMG(self, obj):
        '''Get Item Wise Image'''
        try:
            if obj:
                item_inst = Item.objects.filter(
                    AS_ITM_SKU__iexact=obj.OD_ITM_SKU).first()
                if item_inst:
                    item_image = ItemImageMapping.objects.filter(
                        ID_ITM=item_inst.ID_ITM)
                    if item_image.exists():
                        if item_image.filter(ITM_IMG_DEF=True):
                            return item_image.filter(ITM_IMG_DEF=True).first().ID_ITM_IMG.imagename
                        elif item_image.filter(ITM_IMG_ORD=1):
                            return item_image.filter(ITM_IMG_ORD=1).first().ID_ITM_IMG.imagename
                        else:
                            return ""

                return ""
        except Exception:
            return ""

    def get_ID_CD_BR_ITM(self, obj):
        '''Get the barcode and item'''
        try:
            if obj:
                item_instance = Item.objects.filter(
                    AS_ITM_SKU__iexact=obj.OD_ITM_SKU).first()
                if item_instance:
                    item_barcode = ItemBarcode.objects.filter(
                        ID_ITM=item_instance.ID_ITM)
                    if item_barcode.exists():
                        barcode_list = item_barcode.values_list(
                            'CD_BR_ITM', flat=True)
                        return ','.join(barcode_list)
                    else:
                        return ""
        except Exception:
            return ""

    def get_ITM_VDR_PRT_NO(self, obj):
        if obj.OD_ITM:
            item_supplier_instance = ItemSupplier.objects.filter(
                ID_ITM=obj.OD_ITM.ID_ITM)
            if item_supplier_instance.exists():
                return item_supplier_instance.first().SKU_ITM_SPR
            else:
                return ""
        else:
            return ""

    def get_ITM_MDF_PRT_NO(self, obj):
        if obj.OD_ITM:
            item_manufacturer_instance = ItemManufacturer.objects.filter(
                ID_ITM=obj.OD_ITM.ID_ITM)
            if item_manufacturer_instance.exists():
                return item_manufacturer_instance.first().SKU_ITM_MF
            else:
                return ""
        else:
            return ""

    def get_OD_ITM_DSC_AMT(self, obj):
        if obj.OD_ITM_DSC_AMT:
            return f"{obj.OD_ITM_DSC_AMT:.2f}"
        else:
            return f"{0:.2f}"

    def get_OD_ITM_NET_AMT(self, obj):
        if obj.OD_ITM_NET_AMT:
            return f"{obj.OD_ITM_NET_AMT:.2f}"
        else:
            return f"{0:.2f}"

    def get_OD_ITM_OR_PR(self, obj):
        if obj.OD_ITM_OR_PR:
            return f"{obj.OD_ITM_OR_PR:.2f}"
        else:
            return f"{0:.2f}"

    def get_OD_ITM_TAX_AMT(self, obj):
        if obj.OD_ITM_TAX_AMT:
            return f"{obj.OD_ITM_TAX_AMT:.2f}"
        else:
            return f"{0:.2f}"

    def get_OD_ITM_TOTL_AMT(self, obj):
        if obj.OD_ITM_TOTL_AMT:
            return f"{obj.OD_ITM_TOTL_AMT:.2f}"
        else:
            return f"{0:.2f}"

    def get_AS_ITM_SLUG(self, obj):
        if obj.OD_ITM:
            new_slug = obj.OD_ITM.AS_ITM_SLUG.replace('_', '-')
            return f'{new_slug}.html'

    def get_MMS_NM(self, obj):
        if obj.OD_ITM:
            return obj.OD_ITM.MMS_NM
        return ""

    class Meta:
        model = OrderItemDetails
        fields = '__all__'


class OrderInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderInvoice
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer
        fields = '__all__'


class OrderActivitySerilaizer(serializers.ModelSerializer):

    OD_ACT_CMT = serializers.SerializerMethodField(read_only=True)
    OD_ACT_STATUS = serializers.SerializerMethodField(read_only=True)
    OD_ACT_CRT_BY = serializers.SerializerMethodField(read_only=True)

    def get_OD_ACT_CMT(self, obj):
        return obj.OD_ACT_CMT

    def get_OD_ACT_STATUS(self, obj):
        return obj.OD_ACT_STATUS

    def get_OD_ACT_CRT_BY(self, obj):
        return obj.OD_ACT_CRT_BY

    class Meta:
        model = OrderActivity
        fields = ['OD_ACT_CMT', 'OD_ACT_STATUS',
                  'OD_ACT_CRT_AT', 'OD_ACT_CRT_BY', ]


class OrderHoldUnholdPreviousStatusSerilaizer(serializers.ModelSerializer):
    class Meta:
        model = OrderHoldUnholdPreviousStatus
        fields = '__all__'


class ItemStockOrderSerializer(serializers.ModelSerializer):
    ''' Item List in Create Order Page '''
    PRC = serializers.SerializerMethodField(read_only=True)
    NM_SPR_VENDOR = serializers.SerializerMethodField(read_only=True)
    NM_SPR_PART = serializers.SerializerMethodField(read_only=True)
    ACTL_STK = serializers.SerializerMethodField(read_only=True)

    def get_ACTL_STK(self, obj):
        ''' Actual Stock '''
        actual_stock = 0
        request = self.context['request']
        warehouse_id = request.data['ID_WRH']
        logger.info("Warehouse ID : %s", warehouse_id)
        try:
            actual_stock_obj = ItemInventory.objects.filter(
                AS_ITM_SKU=obj.AS_ITM_SKU, WRH_ID=warehouse_id)
            logger.info("Actual Stock : %s", actual_stock_obj)
            if actual_stock_obj.exists():
                actual_stock = actual_stock_obj.first().ACTL_STK
        except Exception as exp:
            logger.exception(exp)
            actual_stock = 0
        return actual_stock

    def retrieve_price(self, i, price):
        '''Get the price'''
        if (float(i.get('SALE_PRC')) == float(i.get('UNIT_PRC'))) and ((float(i.get('SALE_PRC')) and float(i.get('UNIT_PRC'))) >= float(i.get('MAP_PRC'))):
            price = i.get('SALE_PRC')
        elif (float(i.get('SALE_PRC')) >= float(i.get('MAP_PRC'))) and (float(i.get('UNIT_PRC')) >= float(i.get('MAP_PRC'))):
            if float(i.get('SALE_PRC')) < float(i.get('UNIT_PRC')):
                price = float(i.get('SALE_PRC'))
            else:
                price = float(i.get('UNIT_PRC'))
        elif (float(i.get('SALE_PRC')) < float(i.get('MAP_PRC'))) or (float(i.get('UNIT_PRC')) < float(i.get('MAP_PRC'))):
            price = i.get('MAP_PRC')
        return price

    def get_PRC(self, obj):
        '''Calculate Price'''
        price = 0.00
        try:
            if obj:
                for i in get_regular_price(item_id=obj.STK_ITM_INVTRY_ID.ID_ITM.ID_ITM):
                    if i.get('SALE_PRC', None) is not None and i.get('MAP_PRC') is not None and i.get('UNIT_PRC') is not None:
                        price = self.retrieve_price(i, price)
                        break
        except Exception:
            price = 0.00
        return price

    def get_NM_SPR_VENDOR(self, obj):
        if obj:
            vendor = ItemSupplier.objects.filter(
                ID_ITM=obj.ID_ITM).first()
            if vendor:
                organisation_name = vendor.ID_SPR.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY.organization_party_id.first()
                if organisation_name:
                    vendor_name = organisation_name.NM_TRD
                    return f'{vendor_name}'
        return None

    def get_NM_SPR_PART(self, obj):
        if obj:
            vendor = ItemSupplier.objects.filter(
                ID_ITM=obj.ID_ITM).first()
            if vendor:
                part_no = vendor.SKU_ITM_SPR
                return part_no
        return None

    class Meta:
        model = Item
        fields = ['NM_ITM', 'AS_ITM_SKU', 'ACTL_STK',
                  'PRC', 'ID_ITM', 'NM_SPR_VENDOR', 'NM_SPR_PART']


@shared_task
def update_status_on_verify(channel_id, headers):
    '''Update magento status on verify'''
    magento_token, magento_url = magento_login()
    payload = {
        "entity": {
            "entity_id": channel_id,
            "state": "processing",
            "status": "processing"
        }
    }
    requests.put(
        url=str(magento_url) + '/rest/default/V1/orders/create', headers=headers, data=json.dumps(payload), auth=magento_token)


@shared_task
def update_comment_on_verify(channel_id, status, comment):
    '''Update comment on verify'''
    # Add comment to magento
    magento_token, magento_url = magento_login()
    headers = {
        "content-type": "application/json"
    }
    comment_url = f'/rest/default/V1/orders/{channel_id}/comments'
    payload = {
        "statusHistory": {
            "comment": comment,
            "is_customer_notified": 0,
            "is_visible_on_front": 0,
            "status": str(status)
        }
    }
    requests.post(
        magento_url+comment_url, headers=headers, data=json.dumps(payload), auth=magento_token)


class OrderUpdateSerializer(serializers.ModelSerializer):
    '''Order Update Serialzier'''

    def fetch_comment_status(self, order_instance, order_status):
        '''Fetch comment status'''
        if order_instance.OMS_OD_STS == 'ready_to_pick':
            order_status = 'Ready to Pick'
        if order_instance.OMS_OD_STS == 'new':
            order_status = 'New'
        if order_instance.OMS_OD_STS == 'ready_for_pickup':
            order_status = 'Ready for Pickup'
        if order_instance.OMS_OD_STS == on_hold_key:
            order_status = 'Attention'
        if order_instance.OMS_OD_STS == 'void':
            order_status = 'Void'
        if order_instance.OMS_OD_STS == 'complete':
            order_status = 'Completed'
        return order_status

    def update(self, instance, validated_data):
        '''Update the order objects'''
        request = self.context['request']
        comment = "Order Verified"
        if instance.OMS_OD_STS == 'new':
            instance.OD_STS = 'processing'
            instance.OMS_OD_STS = 'ready_to_pick'
            instance.IS_VERIFIED = True
            instance.save()
            order_status = self.fetch_comment_status(instance, 'New')
            headers = {
                "content-type": "application/json"
            }
            if str(instance.OD_TYPE).lower() != 'dnb order':
                update_status_on_verify.delay(
                    instance.CH_OD_ID, headers)
            if str(instance.OD_TYPE).lower() != 'dnb order':
                update_comment_on_verify.delay(
                    instance.CH_OD_ID, instance.OD_STS, comment)
            OrderActivity.objects.create(
                OD_ACT_OD_MA_ID=instance, OD_ACT_CMT=comment, OD_CUST=instance.OD_CUST, OD_ACT_STATUS=order_status, OD_ACT_CRT_AT=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), OD_ACT_CRT_BY=request.user.get_full_name())
            serialzied_data = OrderElasticDataSerializer(
                instance).data
            order_save(serialzied_data,
                       settings.ES_ORDER_INDEX, instance.OD_ID)
            return instance
        else:
            raise serializers.ValidationError(
                {"message": "Order must be in new state to verify!"})

    class Meta:
        model = OrderMaster
        fields = '__all__'


class OrderPaymentDetailsSerializers(serializers.ModelSerializer):

    OD_PAY_ADDT_INFO = serializers.SerializerMethodField(read_only=True)

    def get_OD_PAY_ADDT_INFO(self, obj):
        input_string = obj.OD_PAY_ADDT_INFO
        input_string = input_string.strip('[]')
        input_string = input_string.strip("'").replace(r"\\", r"\\")
        json_data = json.loads(input_string)
        return json_data

    class Meta:
        model = OrderPaymentDetails
        fields = '__all__'


class GeneratePickListItems(serializers.Serializer):
    ITM_MDF_PRT_NO = serializers.SerializerMethodField(read_only=True)
    ITM_VDR_PRT_NO = serializers.SerializerMethodField(read_only=True)
    AS_ITM_SKU = serializers.SerializerMethodField(read_only=True)
    NM_ITM = serializers.SerializerMethodField(read_only=True)
    OD_ITM_QTY = serializers.SerializerMethodField(read_only=True)
    OD_ITM_QTY_PKD = serializers.SerializerMethodField(read_only=True)
    OD_ITM_OR_PR = serializers.SerializerMethodField(read_only=True)
    MMS_NM = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderItemDetails
        fields = ('OD_ITM_OR_PR', 'OD_ITM_QTY_PKD', 'OD_ITM_QTY', 'NM_ITM',
                  'AS_ITM_SKU', 'NM_SPR_PART', 'NM_SPR_VENDOR', 'MMS_NM')

    def get_AS_ITM_SKU(self, obj):
        if obj.OD_ITM:
            return obj.OD_ITM.AS_ITM_SKU
        return None

    def get_OD_ITM_QTY(self, obj):
        if obj:
            return int(obj.OD_ITM_QTY)
        return None

    def get_OD_ITM_QTY_PKD(self, obj):
        if obj:
            return obj.OD_ITM_QTY_PKD
        return None

    def get_OD_ITM_OR_PR(self, obj):
        if obj:
            return f"{obj.OD_ITM_OR_PR:.2f}"
        return None

    def get_NM_ITM(self, obj):
        if obj.OD_ITM:
            return obj.OD_ITM.NM_ITM
        return None

    def get_ITM_MDF_PRT_NO(self, obj):
        if obj.OD_ITM:
            item_manufacturer = ItemManufacturer.objects.filter(
                ID_ITM=obj.OD_ITM.ID_ITM)
            if item_manufacturer.exists():
                return item_manufacturer.first().SKU_ITM_MF
            else:
                return ""
        else:
            return ""
        
    def get_ITM_VDR_PRT_NO(self, obj):
        if obj.OD_ITM:
            item_supplier = ItemSupplier.objects.filter(
                ID_ITM=obj.OD_ITM.ID_ITM)
            if item_supplier.exists():
                return item_supplier.first().SKU_ITM_SPR
            else:
                return ""
        else:
            return ""

    def get_MMS_NM(self, obj):
        if obj.OD_ITM:
            return obj.OD_ITM.MMS_NM
        return ""


class GeneratePickListSerializer(serializers.Serializer):

    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    OD_CUS_NM = serializers.SerializerMethodField(read_only=True)
    OD_CUS_EMAIL = serializers.SerializerMethodField(read_only=True)
    CUST_PH = serializers.SerializerMethodField(read_only=True)
    item_info = serializers.SerializerMethodField(read_only=True)
    STR_ID = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)
    OD_DATE = serializers.SerializerMethodField(read_only=True)
    OD_TYPE = serializers.SerializerMethodField(read_only=True)
    OMS_OD_STS = serializers.SerializerMethodField(read_only=True)
    OD_TL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_TX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_NT_AMT = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderMaster
        fields = ('CU_OD_ID', 'OD_CUS_NM', 'OD_CUS_EMAIL', 'CUST_PH',
                  'STR_ID', 'OD_STR_NM', 'OD_DATE', 'OD_TYPE', 'item_info',
                  'OMS_OD_STS', 'OD_TL_AMT', 'OD_TX_AMT', 'OD_NT_AMT')

    def get_item_info(self, obj):
        return GeneratePickListItems(obj.orderitemdetails_set.all(), many=True).data

    def get_CU_OD_ID(self, obj):
        try:
            return obj.CU_OD_ID
        except Exception:
            return ""

    def get_OD_CUS_NM(self, obj):
        try:
            return obj.OD_CUS_NM
        except Exception:
            return ""

    def get_OD_CUS_EMAIL(self, obj):
        try:
            return obj.OD_CUS_EMAIL
        except Exception:
            return ""

    def get_CUST_PH(self, obj):
        try:
            return obj.OD_CUST.CUST_PH
        except Exception:
            return ""

    def get_AS_ITM_SKU(self, obj):
        sku_info = OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).first()
        if sku_info:
            try:
                return sku_info.OD_ITM.AS_ITM_SKU
            except Exception:
                return None
        else:
            return None

    def get_OD_ITM_QTY(self, obj):
        sku_info = OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).first()
        if sku_info:
            try:
                return int(sku_info.OD_ITM_QTY)
            except Exception:
                return None
        else:
            return None

    def get_OD_ITM_QTY_PKD(self, obj):
        sku_info = OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).first()
        if sku_info:
            try:
                return sku_info.OD_ITM_QTY_PKD
            except Exception:
                return None
        else:
            return None

    def get_OD_ITM_OR_PR(self, obj):
        sku_info = OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).first()
        if sku_info:
            try:
                return sku_info.OD_ITM_OR_PR
            except Exception:
                return None
        else:
            return None

    def get_DE_ITM(self, obj):
        sku_info = OrderItemDetails.objects.filter(OD_ID=obj.OD_ID).first()
        if sku_info:
            try:
                return sku_info.OD_ITM.DE_ITM
            except Exception:
                return None
        else:
            return None

    def get_STR_ID(self, obj):
        try:
            return obj.STR_ID
        except Exception:
            return None

    def get_OD_STR_NM(self, obj):
        try:
            return obj.OD_STR_NM
        except Exception:
            return ""

    def get_OD_DATE(self, obj):
        try:
            timestamp = datetime.strptime(obj.OD_DATE, '%Y-%m-%d %H:%M:%S%z')
        except Exception:
            timestamp = datetime.strptime(obj.OD_DATE, '%Y-%m-%d %H:%M:%S.%f')
        formatted_date = timestamp.strftime('%Y-%m-%d')
        return formatted_date

    def get_OD_TYPE(self, obj):
        try:
            return obj.OD_TYPE
        except Exception:
            return ""

    def get_OMS_OD_STS(self, obj):
        status = obj.OMS_OD_STS
        modified_status = status.replace("_", " ")
        return modified_status.title()

    def get_OD_TL_AMT(self, obj):
        return f"{obj.OD_TL_AMT:.2f}"

    def get_OD_TX_AMT(self, obj):
        return f"{obj.OD_TX_AMT:.2f}"

    def get_OD_NT_AMT(self, obj):
        return f"{obj.OD_NT_AMT:.2f}"


class OrderElasticDataSerializer(serializers.ModelSerializer):
    '''Order elastic data serializer'''
    all_data = serializers.SerializerMethodField(read_only=True)
    order_details = serializers.SerializerMethodField(read_only=True)
    billing_address = serializers.SerializerMethodField(read_only=True)
    shipping_address = serializers.SerializerMethodField(read_only=True)
    item_details = serializers.SerializerMethodField(read_only=True)
    order_activity = serializers.SerializerMethodField(read_only=True)
    transaction_detail = serializers.SerializerMethodField(read_only=True)

    def get_all_data(self, obj):
        '''Get all data'''
        return OrderMasterSerializer(obj).data

    def get_order_details(self, obj):
        '''Get order data'''
        return OrderMasterSerializer(obj).data

    def get_billing_address(self, obj):
        '''Get order billing address data'''
        return OrderBillingAddressSerializer(obj.orderbillingaddress_set.first()).data

    def get_shipping_address(self, obj):
        '''Get order data'''
        return OrderShippingAddressSerializer(obj.ordershippingaddress_set.first()).data

    def get_item_details(self, obj):
        '''Get order items data'''
        order_item_details = obj.orderitemdetails_set.all()
        return OrderItemDetailsSerializer(order_item_details, many=True).data

    def get_order_activity(self, obj):
        '''Get order activity data'''
        return OrderActivitySerilaizer(obj.orderactivity_set.all(), many=True).data

    def get_transaction_detail(self, obj):
        '''Get order data'''
        return OrderPaymentDetailsSerializers(obj.orderpaymentdetails_set.first()).data

    class Meta:
        model = OrderMaster
        fields = ['all_data', 'order_details', 'billing_address',
                  'shipping_address', 'item_details', 'order_activity', 'transaction_detail']


class CratesPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crates
        fields = '__all__'


class CratesSerializer(serializers.ModelSerializer):
    CLRS = serializers.SerializerMethodField(read_only=True)
    CLRS_ID = serializers.SerializerMethodField(read_only=True)
    STR_ASGN = serializers.SerializerMethodField(read_only=True)
    STR_IDS = serializers.SerializerMethodField(read_only=True)
    CRT_BY_NM = serializers.SerializerMethodField()
    MDF_BY_NM = serializers.SerializerMethodField()

    class Meta:
        model = Crates
        fields = '__all__'

    def get_CLRS(self, obj):
        return obj.CLRS.NM_CLR if obj.CLRS else None

    def get_CLRS_ID(self, obj):
        return obj.CLRS.ID_CLR if obj.CLRS else None

    def get_STR_ASGN(self, obj):
        if obj:
            return ",".join(obj.associatecrate_set.all().values_list('STR_ID__NM_LCN', flat=True))
        return ""

    def get_STR_IDS(self, obj):
        if obj:
            return obj.associatecrate_set.all().values_list('STR_ID__id', flat=True)
        return []
    
    def get_CRT_BY_NM(self, obj):
        try:
            if obj.CRT_BY:
                return obj.CRT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''

    def get_MDF_BY_NM(self, obj):

        try:
            if obj.UPDT_BY:
                return obj.UPDT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''


class CratestatusSerializer(serializers.ModelSerializer):
    '''Crates status serializer'''

    def update(self, instance, validated_data):
        instance.CRT_STS = validated_data.get('status', instance.CRT_STS)
        instance.UPDT_BY = validated_data.get('UPDT_BY', instance.UPDT_BY)
        instance.save()
        return instance

    class Meta:
        '''Crates Meta class'''
        model = Crates
        fields = ["CRT_ID", "CRT_STS"]
        read_only_fields = ["CRT_ID", "CRT_STS"]


class AssociateCratesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociateCrate
        fields = '__all__'


class ReasonSerializer(serializers.ModelSerializer):
    CRT_BY_NM = serializers.SerializerMethodField()
    MDF_BY_NM = serializers.SerializerMethodField()
    
    
    def get_CRT_BY_NM(self, obj):
        ''' Get Created By Name '''
        try:
            if obj.CRT_BY:
                return obj.CRT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''

    def get_MDF_BY_NM(self, obj):
        try:
            if obj.UPDT_BY:
                return obj.UPDT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''
    class Meta:
        model = Reason
        fields = '__all__'


class ReasonPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reason
        fields = '__all__'


class ReasonStatusSerializer(serializers.ModelSerializer):
    '''Reason status serializer'''

    def update(self, instance, validated_data):
        instance.RN_STS = validated_data.get('status', instance.RN_STS)
        instance.UPDT_BY = validated_data.get('UPDT_BY', instance.UPDT_BY)
        instance.save()
        return instance
    
    class Meta:
        model = Reason
        fields = '__all__'

class PickSheetSerializer(serializers.ModelSerializer):
    ITM_SKU_ID = serializers.SerializerMethodField(read_only=True)
    STR_NM = serializers.SerializerMethodField(read_only=True)
    STR_ID = serializers.SerializerMethodField(read_only=True)
    CRT_BY_NM = serializers.SerializerMethodField()
    MDF_BY_NM = serializers.SerializerMethodField()
    
    class Meta:
        model = PicksheetNote
        fields = '__all__'

    def get_STR_NM(self, obj):
        if obj:
            return (obj.picksheetnotestores_set.all().values_list('STR_ID__NM_LCN', flat=True))
        return ""

    def get_STR_ID(self, obj):
        if obj:
            return obj.picksheetnotestores_set.all().values_list('STR_ID__id', flat=True)
        return []
    
    def get_CRT_BY_NM(self, obj):
        ''' Get Created By Name '''
        try:
            if obj.CRT_BY:
                return obj.CRT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''

    def get_MDF_BY_NM(self, obj):
        ''' Get Created By Name '''
        try:
            if obj.UPDT_BY:
                return obj.UPDT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''
        
    def get_ITM_SKU_ID(self, obj):
        if obj:
            return list(obj.picksheetnoteitemsku_set.all().values_list('ITM_SKU_ID__AS_ITM_SKU', flat=True))
        return []

    
class PickSheetGetSerializer(serializers.ModelSerializer):
    ITM_SKU_ID = serializers.SerializerMethodField(read_only=True)
    STR_NM = serializers.SerializerMethodField(read_only=True)
    STR_ID = serializers.SerializerMethodField(read_only=True)
    PSN_VIS = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PicksheetNote
        fields = '__all__'

    def get_STR_NM(self, obj):
        if obj:
            return (obj.picksheetnotestores_set.all().values_list('STR_ID__NM_LCN', flat=True))
        return ""

    def get_STR_ID(self, obj):
        if obj:
            return obj.picksheetnotestores_set.all().values_list('STR_ID__id', flat=True)

    def get_PSN_VIS(self, obj):

        if obj:
            return obj.PSN_VIS.split(",")
        else:
            return []
        
    def get_ITM_SKU_ID(self, obj):
        if obj:
            return obj.picksheetnoteitemsku_set.all().values_list('ITM_SKU_ID', flat=True)
        return ""
    

class PickSheetPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PicksheetNote
        fields = '__all__'

class PickSheetStatusSerializer(serializers.ModelSerializer):
    '''PickSheet Note status serializer'''

    def update(self, instance, validated_data):
        instance.PSN_STS = validated_data.get('status', instance.PSN_STS)
        instance.UPDT_BY = validated_data.get('UPDT_BY', instance.UPDT_BY)
        instance.save()
        return instance

    class Meta:
        '''Reason Meta class'''
        model = Reason
        fields = ["PSN_ID", "PSN_STS"]
        read_only_fields = ["PSN_ID", "PSN_STS"]


class PickSheetStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = PicksheetNoteStores
        fields = '__all__'

class PickSheetSKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = PicksheetNoteItemSKU
        fields = '__all__'
        
class PickSheetItemSKUSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['ID_ITM', 'AS_ITM_SKU']