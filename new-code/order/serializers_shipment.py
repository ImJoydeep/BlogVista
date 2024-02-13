from django.db.models import Sum
from rest_framework import serializers
from product.models.models_item_stock import ItemBarcode, ItemManufacturer, ItemSupplier
from product.models.models_item import Item, ItemImageMapping
from order.models import ItemPicklist, OrderCrates, ShipmentMaster, ItemShipmentList
picking_in_progress_key = 'Picking-In Progress'


class ItemShipmentListSerializer(serializers.Serializer):

    OD_ITM_DSC_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_NET_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_OR_PR = serializers.SerializerMethodField(read_only=True)
    NM_ITM = serializers.SerializerMethodField(read_only=True)
    OD_ITM_TAX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_TOTL_AMT = serializers.SerializerMethodField(read_only=True)
    ITM_VDR_PRT_NO = serializers.SerializerMethodField(read_only=True)
    ITM_MDF_PRT_NO = serializers.SerializerMethodField(read_only=True)
    MMS_NM = serializers.SerializerMethodField(read_only=True)
    AS_ITM_SKU = serializers.SerializerMethodField(read_only=True)
    OD_ITM_QTY = serializers.SerializerMethodField(read_only=True)
    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    OD_PICK_NO = serializers.SerializerMethodField(read_only=True)
    OD_SHP_ID = serializers.SerializerMethodField(read_only=True)
    ID_CD_BR_ITM = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHP_STS = serializers.SerializerMethodField(read_only=True)
    OD_PICK_BY = serializers.SerializerMethodField(read_only=True)
    OD_PICK_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHIP_CODE = serializers.SerializerMethodField(read_only=True)
    ITM_PICK_ID = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)
    OD_QTY = serializers.SerializerMethodField(read_only=True)
    OD_TL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_NT_AMT = serializers.SerializerMethodField(read_only=True)
    OD_TX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_DIS_AMT = serializers.SerializerMethodField(read_only=True)
    CRT_DT = serializers.SerializerMethodField(read_only=True)

    def get_OD_STR_NM(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_STR_NM
        return ""

    def get_OD_QTY(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_QTY
        return ""

    def get_OD_TL_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_TL_AMT
        return ""

    def get_OD_NT_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_NT_AMT
        return ""

    def get_OD_TX_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_TX_AMT
        return ""

    def get_OD_DIS_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_DIS_AMT
        return ""

    def get_CRT_DT(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.CRT_DT
        return ""

    def get_ITM_PICK_ID(self, obj):
        if obj.OD_PICK_ID:
            return obj.OD_PICK_ID.itempicklist_set.first().ITM_PICK_ID
        return None

    def get_OD_PICK_ID(self, obj):
        if obj.OD_PICK_ID:
            return obj.OD_PICK_ID.OD_PICK_ID
        return ""

    def get_OD_SHIP_CODE(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.OD_SHIP_CODE
        return ""

    def get_OD_ITM_NET_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_NET_AMT:.2f}'
        else:
            return None

    def get_OD_ITM_DSC_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_DSC_AMT:.2f}'
        else:
            return None

    def get_OD_ITM_TOTL_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_TOTL_AMT:.2f}'
        else:
            return None

    def get_OD_ITM_OR_PR(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_OR_PR:.2f}'
        else:
            return None

    def get_OD_ITM_TAX_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_TAX_AMT:.2f}'
        else:
            return None

    def get_ITM_MDF_PRT_NO(self, obj):
        if obj.ITM_ID:
            item_manufacturer_instance = ItemManufacturer.objects.filter(
                ID_ITM=obj.ITM_ID.ID_ITM)
            if item_manufacturer_instance.exists():
                return item_manufacturer_instance.first().SKU_ITM_MF
            else:
                return ""
        else:
            return ""

    def get_ITM_VDR_PRT_NO(self, obj):
        if obj.ITM_ID:
            item_supplier_instance = ItemSupplier.objects.filter(
                ID_ITM=obj.ITM_ID.ID_ITM)
            if item_supplier_instance.exists():
                return item_supplier_instance.first().SKU_ITM_SPR
            else:
                return ""
        else:
            return ""

    def get_MMS_NM(self, obj):
        if obj.ITM_ID:
            return obj.ITM_ID.MMS_NM
        return ""

    def get_NM_ITM(self, obj):
        if obj.ITM_ID:
            return obj.ITM_ID.NM_ITM
        else:
            return ""

    def get_AS_ITM_SKU(self, obj):
        if obj.ITM_ID:
            return obj.ITM_ID.AS_ITM_SKU
        else:
            return ""

    def get_OD_ITM_QTY(self, obj):
        if obj.OD_ITM_ID:
            return obj.OD_ITM_ID.OD_ITM_QTY
        else:
            return ""

    def get_OD_PICK_NO(self, obj):
        if obj.OD_PICK_ID:
            return obj.OD_PICK_ID.OD_PICK_NO
        else:
            return ""

    def get_OD_SHP_ID(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.OD_SHP_ID
        else:
            return ""

    def get_ID_CD_BR_ITM(self, obj):
        if obj.ID_CD_BR_ITM:
            return obj.ID_CD_BR_ITM.CD_BR_ITM
        return ""

    def get_ITM_SHP_ID(self, obj):
        return obj.ITM_SHP_ID

    def get_OD_SHP_STS(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.OD_SHP_STS
        return ""

    def get_CU_OD_ID(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.CU_OD_ID
        else:
            return ""

    def get_OD_PICK_BY(self, obj):
        if obj.OD_PICK_ID:
            return obj.OD_PICK_ID.OD_PICK_BY.get_full_name()
        return ""

    class Meta:
        model = ItemShipmentList
        fields = '__all__'


class ItemsSerializer(serializers.Serializer):
    OD_ITM_OR_PR = serializers.SerializerMethodField(read_only=True)
    OD_ITM_NET_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_TAX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_TOTL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ITM_DSC_AMT = serializers.SerializerMethodField(read_only=True)
    ITM_VDR_PRT_NO = serializers.SerializerMethodField(read_only=True)
    ITM_MDF_PRT_NO = serializers.SerializerMethodField(read_only=True)
    MMS_NM = serializers.SerializerMethodField(read_only=True)
    NM_ITM = serializers.SerializerMethodField(read_only=True)
    OD_ITM_QTY = serializers.SerializerMethodField(read_only=True)
    AS_ITM_SKU = serializers.SerializerMethodField(read_only=True)
    ID_CD_BR_ITM = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_SORT = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_ID = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_QTY = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_RTN_QTY = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_GRN_QTY = serializers.SerializerMethodField(read_only=True)
    ITM_SHP_GRN_RTN = serializers.SerializerMethodField(read_only=True)
    ITM_PICK_ID = serializers.SerializerMethodField(read_only=True)
    OD_ITM_QTY_PKD = serializers.SerializerMethodField(read_only=True)
    OD_ITM_ID = serializers.SerializerMethodField(read_only=True)
    ITM_PICK_MRP = serializers.SerializerMethodField(read_only=True)
    ITM_IMG = serializers.SerializerMethodField(read_only=True)

    def get_ITM_IMG(self, obj):
        '''Get Item Wise Images'''
        try:
            if obj:
                item_instance = Item.objects.filter(
                    AS_ITM_SKU__iexact=obj.ITM_ID.AS_ITM_SKU).first()
                if item_instance:
                    item_images = ItemImageMapping.objects.filter(
                        ID_ITM=item_instance.ID_ITM)
                    if item_images.exists():
                        if item_images.filter(ITM_IMG_DEF=True):
                            return item_images.filter(ITM_IMG_DEF=True).first().ID_ITM_IMG.imagename
                        elif item_images.filter(ITM_IMG_ORD=1):
                            return item_images.filter(ITM_IMG_ORD=1).first().ID_ITM_IMG.imagename
                        else:
                            return ""

                return ""
        except Exception:
            return ""
    ITM_OR_MRP = serializers.SerializerMethodField(read_only=True)

    def get_ITM_OR_MRP(self, obj):
        item_picklist = ItemPicklist.objects.filter(
            OD_PICK_ID=obj.OD_PICK_ID,
            ITM_ID=obj.ITM_ID).first()
        if item_picklist:
            return item_picklist.ITM_OR_MRP
        else:
            return None

    def get_ITM_PICK_MRP(self, obj):
        item_picklist = ItemPicklist.objects.filter(
            OD_PICK_ID=obj.OD_PICK_ID,
            ITM_ID=obj.ITM_ID).first()
        if item_picklist:
            return item_picklist.ITM_PICK_MRP
        else:
            return None

    def get_OD_ITM_ID(self, obj):
        if obj.OD_ITM_ID:
            return obj.OD_ITM_ID.OD_ITM_ID
        return None

    def get_OD_ITM_QTY_PKD(self, obj):
        if obj.OD_ITM_ID:
            return obj.OD_ITM_ID.OD_ITM_QTY_PKD
        return None

    def get_ITM_PICK_ID(self, obj):
        item_picklist = ItemPicklist.objects.filter(
            OD_PICK_ID=obj.OD_PICK_ID,
            ITM_ID=obj.ITM_ID).first()
        if item_picklist:
            return item_picklist.ITM_PICK_ID
        else:
            return None

    def get_ITM_SHP_GRN_RTN(self, obj):
        return obj.ITM_SHP_GRN_RTN

    def get_ITM_SHP_GRN_QTY(self, obj):
        return obj.ITM_SHP_GRN_QTY

    def get_ITM_SHP_QTY(self, obj):
        return obj.ITM_SHP_QTY

    def get_ITM_SHP_RTN_QTY(self, obj):
        return obj.ITM_SHP_RTN_QTY

    def get_ITM_SHP_ID(self, obj):
        return obj.ITM_SHP_ID

    def get_ITM_SHP_SORT(self, obj):
        return obj.ITM_SHP_SORT

    def get_OD_ITM_DSC_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_DSC_AMT:.2f}'
        else:
            return None

    def get_OD_ITM_NET_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_NET_AMT:.2f}'
        else:
            return None

    def get_OD_ITM_TAX_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_TAX_AMT:.2f}'
        else:
            return None

    def get_OD_ITM_TOTL_AMT(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_TOTL_AMT:.2f}'
        else:
            return None

    def get_OD_ITM_OR_PR(self, obj):
        if obj.OD_ITM_ID:
            return f'{obj.OD_ITM_ID.OD_ITM_OR_PR:.2f}'
        else:
            return None

    def get_ITM_VDR_PRT_NO(self, obj):
        if obj.ITM_ID:
            item_supplier_instance = ItemSupplier.objects.filter(
                ID_ITM=obj.ITM_ID.ID_ITM)
            if item_supplier_instance.exists():
                return item_supplier_instance.first().SKU_ITM_SPR
            else:
                return ""
        else:
            return ""

    def get_ITM_MDF_PRT_NO(self, obj):
        if obj.ITM_ID:
            item_manufacturer_instance = ItemManufacturer.objects.filter(
                ID_ITM=obj.ITM_ID.ID_ITM)
            if item_manufacturer_instance.exists():
                return item_manufacturer_instance.first().SKU_ITM_MF
            else:
                return ""
        else:
            return ""

    def get_AS_ITM_SKU(self, obj):
        if obj.ITM_ID:
            return obj.ITM_ID.AS_ITM_SKU
        else:
            return ""

    def get_MMS_NM(self, obj):
        if obj.ITM_ID:
            return obj.ITM_ID.MMS_NM
        return ""

    def get_NM_ITM(self, obj):
        if obj.ITM_ID:
            return obj.ITM_ID.NM_ITM
        else:
            return ""

    def get_OD_ITM_QTY(self, obj):
        if obj.OD_ITM_ID:
            return obj.OD_ITM_ID.OD_ITM_QTY
        else:
            return ""

    def get_ID_CD_BR_ITM(self, obj):
        '''Get the barcode and item'''
        try:
            if obj.OD_ITM_ID:
                item_instance = Item.objects.filter(
                    AS_ITM_SKU__iexact=obj.OD_ITM_ID.OD_ITM_SKU).first()
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

    class Meta:
        model = ItemShipmentList
        fields = '__all__'


class ShipmentListSerializer(serializers.ModelSerializer):
    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    OD_PICK_NO = serializers.SerializerMethodField(read_only=True)
    OD_SHP_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHP_STS = serializers.SerializerMethodField(read_only=True)
    OD_PICK_BY = serializers.SerializerMethodField(read_only=True)
    OD_PICK_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHIP_CODE = serializers.SerializerMethodField(read_only=True)
    OD_DATE = serializers.SerializerMethodField(read_only=True)
    OD_QTY = serializers.SerializerMethodField(read_only=True)
    OD_PICK_TOTAL_AMT = serializers.SerializerMethodField(read_only=True)
    CRT_DT = serializers.SerializerMethodField(read_only=True)
    OD_CRATE_COUNT = serializers.SerializerMethodField(read_only=True)
    OD_SHP_AMT = serializers.SerializerMethodField(read_only=True)
    OD_PD_AMT = serializers.SerializerMethodField(read_only=True)
    item = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)

    def get_item(self, obj):
        return ItemsSerializer(obj.itemshipmentlist_set.all(), many=True).data

    def get_OD_CRATE_COUNT(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_CRATE_COUNT
        return None

    def get_OD_SHP_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_SHP_AMT
        return None

    def get_OD_PD_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_PD_AMT
        return None

    def get_OD_PICK_TOTAL_AMT(self, obj):
        try:
            if obj.picklistmaster_set.first():
                total_amount = obj.picklistmaster_set.first().OD_PICK_TOTAL_AMT
                return total_amount
            return None
        except Exception:
            return None

    def get_OD_STR_NM(self, obj):
        try:
            if obj:
                return ','.join(ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID__OD_STR_NM').values_list('OD_ID__OD_STR_NM', flat=True))
            return ""
        except Exception:
            return ""

    def get_CRT_DT(self, obj):
        if obj.OD_SHP_ID:
            return obj.CRT_DT
        return ""

    def get_OD_QTY(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_QTY
        return ""

    def get_OD_DATE(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_DATE
        return ""

    def get_ITM_PICK_ID(self, obj):
        try:
            if obj.itemshipmentlist_set.first().OD_PICK_ID:
                return obj.itemshipmentlist_set.first().OD_PICK_ID.itempicklist_set.first().ITM_PICK_ID
            return None
        except Exception:
            return None

    def get_OD_PICK_ID(self, obj):
        try:
            if obj.itemshipmentlist_set.first().OD_PICK_ID:
                return obj.itemshipmentlist_set.first().OD_PICK_ID.OD_PICK_ID
            return ""
        except Exception:
            return ""

    def get_OD_SHIP_CODE(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHIP_CODE
        return ""

    def get_CU_OD_ID(self, obj):
        try:
            if obj:
                return ','.join(ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID').values_list('OD_ID__CU_OD_ID', flat=True))
            else:
                return ""
        except Exception:
            return ""

    def get_OD_PICK_NO(self, obj):
        try:
            if obj.itemshipmentlist_set.first().OD_PICK_ID:
                return obj.itemshipmentlist_set.first().OD_PICK_ID.OD_PICK_NO
            else:
                return ""
        except Exception:
            return ""

    def get_OD_SHP_ID(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID
        else:
            return ""

    def get_OD_SHP_STS(self, obj):
        if obj.OD_SHP_ID:
            if ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID').filter(OD_ID__OMS_OD_STS__in=['ready_to_pick', 'on hold']).exists():
                return picking_in_progress_key
            else:
                return 'Picking-Completed'
        return ""

    def get_OD_PICK_BY(self, obj):
        try:
            if obj.itemshipmentlist_set.first().OD_PICK_ID:
                return obj.itemshipmentlist_set.first().OD_PICK_ID.OD_PICK_BY.get_full_name()
            return ""
        except Exception:
            return ""

    class Meta:
        model = ShipmentMaster
        fields = '__all__'


class GenerateItemShipmentGetSerializer(serializers.ModelSerializer):
    OD_SHP_STS = serializers.SerializerMethodField(read_only=True)
    OD_PICK_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHIP_CODE = serializers.SerializerMethodField(read_only=True)
    OD_NT_AMT = serializers.SerializerMethodField(read_only=True)
    OD_DATE = serializers.SerializerMethodField(read_only=True)
    OD_QTY = serializers.SerializerMethodField(read_only=True)
    OD_TL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_PICK_TOTAL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_DIS_AMT = serializers.SerializerMethodField(read_only=True)
    OD_PICK_BY = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)
    OD_SHP_ACT_QTY = serializers.SerializerMethodField(read_only=True)
    OD_PD_AMT = serializers.SerializerMethodField(read_only=True)
    IS_GENERATED = serializers.SerializerMethodField(read_only=True)
    OD_TX_AMT = serializers.SerializerMethodField(read_only=True)
    CRT_DT = serializers.SerializerMethodField(read_only=True)
    item = serializers.SerializerMethodField(read_only=True)
    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    OD_PICK_NO = serializers.SerializerMethodField(read_only=True)
    OD_SHP_ID = serializers.SerializerMethodField(read_only=True)
    OD_CRATE_COUNT = serializers.SerializerMethodField(read_only=True)
    OD_SHP_AMT = serializers.SerializerMethodField(read_only=True)
    OD_ID_MUL = serializers.SerializerMethodField(read_only=True)
    OD_PICKER_ID = serializers.SerializerMethodField(read_only=True)
    ID_USR = serializers.SerializerMethodField(read_only=True)
    CHK_PICK_COMPLETED = serializers.SerializerMethodField(read_only=True)

    def get_CHK_PICK_COMPLETED(self, obj):
        try:
            if obj.OD_SHP_ID:
                if ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID, OD_ID__CU_OD_ID=self.context.get('order_id')).distinct('OD_ID').filter(OD_ID__OMS_OD_STS__in=['ready_to_pick']).exists():
                    return picking_in_progress_key
                elif ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID, OD_ID__CU_OD_ID=self.context.get('order_id')).distinct('OD_ID').filter(OD_ID__OMS_OD_STS__in=['on hold']).exists():
                    return "Attention"
                else:
                    return 'Picking-Completed'
            return ''
        except Exception:
            return ""

    def get_ID_USR(self, obj):
        try:
            return self.context.get('user').user.id
        except Exception:
            return None

    def get_OD_ID_MUL(self, obj):
        '''Get the multiple order id'''
        if obj.OD_SHP_ID:
            return ','.join(ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID.OD_SHP_ID).distinct('OD_ID').values_list('OD_ID__CU_OD_ID', flat=True))
        return None

    def get_OD_SHP_ACT_QTY(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.OD_SHP_ACT_QTY
        return None

    def get_item(self, obj):
        if obj:
            item_obj = ItemShipmentList.objects.filter(
                OD_SHP_ID=obj.OD_SHP_ID, OD_ID=obj.OD_ID).order_by('-ITM_SHP_ID')
            return ItemsSerializer(item_obj, many=True).data
        else:
            return []

    def get_OD_SHP_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_SHP_AMT
        return None

    def get_OD_CRATE_COUNT(self, obj):
        if obj.OD_SHP_ID:
            return OrderCrates.objects.filter(OD_ID__CU_OD_ID__iexact=self.context.get("order_id")).count()
        return None

    def get_OD_PICK_TOTAL_AMT(self, obj):
        if obj.OD_PICK_ID:
            total_amount = obj.OD_PICK_ID.OD_PICK_TOTAL_AMT
            return total_amount
        return None

    def get_OD_PD_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_PD_AMT
        return None

    def get_OD_STR_NM(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_STR_NM
        return ""

    def get_IS_GENERATED(self, obj):
        '''Returned is generated'''
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.IS_GENERATED
        return False

    def get_CRT_DT(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.CRT_DT
        return ""

    def get_OD_TL_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_TL_AMT
        return None

    def get_OD_TX_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_TX_AMT
        return None

    def get_OD_DIS_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_DIS_AMT
        return None

    def get_OD_QTY(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_QTY
        return None

    def get_OD_NT_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_NT_AMT
        return None

    def get_ITM_PICK_ID(self, obj):
        try:
            if obj.itemshipmentlist_set.first().OD_PICK_ID:
                return obj.itemshipmentlist_set.first().OD_PICK_ID.itempicklist_set.first().ITM_PICK_ID
            return None
        except Exception:
            return None

    def get_OD_DATE(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_DATE
        return ""

    def get_OD_SHIP_CODE(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.OD_SHIP_CODE
        return ""

    def get_OD_PICK_ID(self, obj):
        try:
            if obj.OD_PICK_ID:
                return obj.OD_PICK_ID.OD_PICK_ID
            return None
        except Exception:
            return None

    def get_CU_OD_ID(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.CU_OD_ID
        else:
            return None

    def get_OD_SHP_ID(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.OD_SHP_ID
        else:
            return None

    def get_OD_PICK_NO(self, obj):
        try:
            if obj.OD_PICK_ID:
                return obj.OD_PICK_ID.OD_PICK_NO
            else:
                return ""
        except Exception:
            return ""

    def get_OD_PICK_BY(self, obj):
        try:
            if obj.OD_PICK_ID:
                return obj.OD_PICK_ID.OD_PICK_BY.get_full_name()
            return ""
        except Exception:
            return ""

    def get_OD_PICKER_ID(self, obj):
        try:
            if obj.OD_PICK_ID:
                return obj.OD_PICK_ID.OD_PICK_BY.id
            return ""
        except Exception:
            return ""

    def get_OD_SHP_STS(self, obj):
        if obj.OD_SHP_ID:
            if ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID').filter(OD_ID__OMS_OD_STS='ready_to_pick').exists():
                return picking_in_progress_key
            else:
                return 'Picking-Completed'
        return ""

    class Meta:
        model = ItemShipmentList
        fields = ['CU_OD_ID', 'OD_PICK_NO',
                  'OD_SHP_ID', 'OD_SHP_STS', 'OD_PICK_BY', 'OD_PICK_ID', 'OD_SHIP_CODE', 'OD_DATE', 'OD_QTY', 'OD_TL_AMT', 'OD_PICK_TOTAL_AMT', 'OD_DIS_AMT', 'OD_NT_AMT', 'OD_TX_AMT',
                  'CRT_DT', 'OD_CRATE_COUNT', 'OD_SHP_AMT', 'OD_PD_AMT', 'item', 'OD_STR_NM', 'OD_SHP_ACT_QTY', 'IS_GENERATED',
                  'OD_ID_MUL', 'OD_PICKER_ID', 'ID_USR', 'CHK_PICK_COMPLETED']


class ScanPickItemSerializer(serializers.Serializer):

    product_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ItemShipmentList
        fields = '__all__'

    def get_product_details(self, obj):
        return ItemsSerializer(obj).data


class CratesSerializer(serializers.ModelSerializer):

    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    CRT_CD = serializers.SerializerMethodField(read_only=True)
    BR_CD = serializers.SerializerMethodField(read_only=True)

    def get_BR_CD(self, obj):
        try:
            if obj:
                crt_obj = OrderCrates.objects.filter(
                    CRATE_ID=obj.CRATE_ID).first()
                if crt_obj:
                    return crt_obj.AC_ID.CRT_ID.BR_CD
            return ""
        except Exception:
            return ""

    def get_CU_OD_ID(self, obj):
        return obj.OD_ID.CU_OD_ID

    def get_CRT_CD(self, obj):
        try:
            if obj:
                crt_obj = OrderCrates.objects.filter(
                    CRATE_ID=obj.CRATE_ID).first()
                if crt_obj:
                    return crt_obj.AC_ID.CRT_ID.CRT_CD
            return ""
        except Exception:
            return ""

    class Meta:
        model = OrderCrates
        fields = '__all__'


class GenerateInvoiceSerializer(serializers.ModelSerializer):

    OD_INVOE_INCR_ID = serializers.SerializerMethodField(read_only=True)
    OD_INVOE_CRT_AT = serializers.SerializerMethodField(read_only=True)
    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    OD_CUS_NM = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)
    address_detail = serializers.SerializerMethodField(read_only=True)
    OD_CRATE_COUNT = serializers.SerializerMethodField(read_only=True)
    OD_TYPE = serializers.SerializerMethodField(read_only=True)
    OD_SHP_ID = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ItemShipmentList
        fields = '__all__'

    def get_OD_SHP_ID(self, obj):
        try:
            return obj.itemshipmentlist_set.first().OD_SHP_ID.OD_SHP_ID
        except Exception:
            return None

    def get_CU_OD_ID(self, obj):
        try:
            if obj.OD_ID:
                return obj.CU_OD_ID
            return None
        except Exception:
            return None

    def get_OD_TYPE(self, obj):
        try:
            if obj.OD_ID:
                return obj.OD_TYPE
            return None
        except Exception:
            return None

    def get_OD_INVOE_INCR_ID(self, obj):
        try:
            if obj.orderinvoice_set.first():
                return obj.orderinvoice_set.first().OD_INVOE_INCR_ID
            return None
        except Exception:
            return None

    def get_OD_INVOE_CRT_AT(self, obj):
        try:
            if obj.orderinvoice_set.first():
                return obj.orderinvoice_set.first().OD_INVOE_CRT_AT
            return None
        except Exception:
            return None

    def get_OD_CUS_NM(self, obj):
        try:
            if obj.OD_ID:
                return obj.OD_CUS_NM
            return None
        except Exception:
            return None

    def get_OD_STR_NM(self, obj):
        try:
            if obj.OD_ID:
                return obj.OD_STR_NM
            return None
        except Exception:
            return None

    def get_OD_CRATE_COUNT(self, obj):
        try:
            if obj.itemshipmentlist_set.first().OD_SHP_ID:
                return obj.itemshipmentlist_set.first().OD_SHP_ID.OD_CRATE_COUNT
            return None
        except Exception:
            return None

    def get_address_detail(self, obj):
        try:
            if obj.orderbillingaddress_set.first():
                address = obj.orderbillingaddress_set.first().OD_BA_ST
                city = obj.orderbillingaddress_set.first().OD_BA_CT
                state = obj.orderbillingaddress_set.first().OD_BA_RGN
                country_code = obj.orderbillingaddress_set.first().OD_BA_CTR_CODE
                temp_address = f"{address}, {city}, {state}, {country_code}"
                return temp_address
        except Exception:
            return None
