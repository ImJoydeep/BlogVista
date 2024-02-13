import inflect
from datetime import datetime
from rest_framework import serializers
from order.serializers_shipment import ItemsSerializer
from order.serializers import OrderBillingAddressSerializer, OrderItemDetailsSerializer, OrderMasterSerializer, OrderShippingAddressSerializer
from order.models import ItemShipmentList, OrderInvoice, OrderMaster


class GetOrderInvoiceListSerializer(serializers.ModelSerializer):
    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    CUST_NM = serializers.SerializerMethodField(read_only=True)
    OD_DATE = serializers.SerializerMethodField(read_only=True)
    OD_STR_NM = serializers.SerializerMethodField(read_only=True)
    OD_TL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_TX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_SHP_AMT = serializers.SerializerMethodField(read_only=True)
    OD_NT_AMT = serializers.SerializerMethodField(read_only=True)

    def get_CU_OD_ID(self, obj):
        '''Get the Order Id'''
        order_id = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                order_id = order_instance.CU_OD_ID
            return order_id
        except Exception:
            return order_id

    def get_CUST_NM(self, obj):
        '''Get the Customer Name'''
        customer_name = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                customer_name = order_instance.OD_CUST.CUST_FNM + \
                    ' ' + order_instance.OD_CUST.CUST_LNM
            return customer_name
        except Exception:
            return customer_name

    def get_OD_DATE(self, obj):
        '''Get the Order Id'''
        order_date = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                order_date = order_instance.OD_DATE
            return order_date
        except Exception:
            return order_date

    def get_OD_STR_NM(self, obj):
        '''Get the Order Id'''
        store_name = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                store_name = order_instance.OD_STR_NM
            return store_name
        except Exception:
            return store_name

    def get_OD_TL_AMT(self, obj):
        '''Get the Order Id'''
        order_total_amount = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                order_total_amount = order_instance.OD_TL_AMT
            return order_total_amount
        except Exception:
            return order_total_amount

    def get_OD_TX_AMT(self, obj):
        '''Get the Order Id'''
        order_tax_amount = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                order_tax_amount = order_instance.OD_TX_AMT
            return order_tax_amount
        except Exception:
            return order_tax_amount

    def get_OD_SHP_AMT(self, obj):
        '''Get the Order Id'''
        order_shipping_amount = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                order_shipping_amount = order_instance.OD_SHP_AMT
            return order_shipping_amount
        except Exception:
            return order_shipping_amount

    def get_OD_NT_AMT(self, obj):
        '''Get the Order Id'''
        order_net_amount = None
        try:
            order_instance = OrderMaster.objects.filter(
                OD_ID=obj.OD_INVOE_OD_ID.OD_ID).first()
            if order_instance:
                order_net_amount = order_instance.OD_NT_AMT
            return order_net_amount
        except Exception:
            return order_net_amount

    class Meta:
        model = OrderInvoice
        fields = ['OD_INVOE_INCR_ID', 'CU_OD_ID',
                  'CUST_NM', 'OD_DATE', 'OD_STR_NM', 'OD_TL_AMT', 'OD_TX_AMT', 'OD_SHP_AMT', 'OD_NT_AMT']


class InvoicePdfSerializer(serializers.Serializer):
    order = serializers.SerializerMethodField(read_only=True)
    item = serializers.SerializerMethodField(read_only=True)
    billing_address = serializers.SerializerMethodField(read_only=True)
    shipping_address = serializers.SerializerMethodField(read_only=True)
    OD_INVOE_INCR_ID = serializers.SerializerMethodField(read_only=True)
    amount_in_word = serializers.SerializerMethodField(read_only=True)
    OD_INVOE_CRT_AT = serializers.SerializerMethodField(read_only=True)

    def get_order(self, obj):
        return OrderMasterSerializer(obj).data
    
    def get_item(self, obj):
        order_item_details = obj.orderitemdetails_set.all()
        return OrderItemDetailsSerializer(order_item_details, many=True).data
    
    def get_billing_address(self, obj):
        return OrderBillingAddressSerializer(obj.orderbillingaddress_set.first()).data
    
    def get_shipping_address(self, obj):
        return OrderShippingAddressSerializer(obj.ordershippingaddress_set.first()).data
    
    def get_OD_INVOE_INCR_ID(self, obj):
        try:
            if obj.orderinvoice_set.last():
                return obj.orderinvoice_set.last().OD_INVOE_INCR_ID
            else: 
                return ""
        except Exception:
            return ""
        
    def get_OD_INVOE_CRT_AT(self, obj):
        try:
            if obj.orderinvoice_set.last():
                original_date_string = obj.orderinvoice_set.last().OD_INVOE_CRT_AT
                original_datetime = datetime.strptime(original_date_string, '%Y-%m-%d %H:%M:%S')
                formatted_date_string = original_datetime.strftime('%Y-%m-%d')
                return formatted_date_string
            else: 
                return ""
        except Exception:
            return ""
        
    def get_amount_in_word(self, obj):
        try:
            amount = self.get_order(obj)
            convert_number_to_word = inflect.engine()
            words = convert_number_to_word.number_to_words(
                int(float(amount.get("OD_TL_AMT"))), andword="", comma=False)
            return f"{words.title()} Only."
        except Exception:
            return "Only."
    
    class Meta:
        model = OrderMaster
        fields = ['order', 'item', 'billing_address', 'shipping_address', 'OD_INVOE_INCR_ID', 'OD_INVOE_CRT_AT']


class InvoiceSerializer(serializers.Serializer):
    CU_OD_ID = serializers.SerializerMethodField(read_only=True)
    OD_SHP_ID = serializers.SerializerMethodField(read_only=True)
    OD_PICK_ID = serializers.SerializerMethodField(read_only=True)
    OD_TL_AMT = serializers.SerializerMethodField(read_only=True)
    OD_DIS_AMT = serializers.SerializerMethodField(read_only=True)
    OD_NT_AMT = serializers.SerializerMethodField(read_only=True)
    OD_TX_AMT = serializers.SerializerMethodField(read_only=True)
    OD_SHP_AMT = serializers.SerializerMethodField(read_only=True)
    OD_PD_AMT = serializers.SerializerMethodField(read_only=True)
    item = serializers.SerializerMethodField(read_only=True)

    def get_OD_PICK_ID(self, obj):
        try:
            if obj.OD_PICK_ID:
                return obj.OD_PICK_ID.OD_PICK_ID
            return ""
        except Exception:
            return ""
        
    def get_OD_DIS_AMT(self, obj):
        if obj:
            dis = 0
            for i in ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID'):
                dis += i.OD_ID.OD_DIS_AMT if i.OD_ID.OD_DIS_AMT else 0
            return dis
        return 0.0
        
    def get_OD_PD_AMT(self, obj):
        if obj:
            tot = 0
            for i in ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID'):
                tot += i.OD_ID.OD_PD_AMT
            return tot
        return 0.0
    
    def get_OD_TL_AMT(self, obj):
        if obj:
            tot = 0
            for i in ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID'):
                tot += i.OD_ID.OD_TL_AMT
            return tot
        return 0.0
        
    def get_OD_SHP_ID(self, obj):
        if obj.OD_SHP_ID:
            return obj.OD_SHP_ID.OD_SHP_ID
        else:
            return ""
    
    def get_OD_TX_AMT(self, obj):
        if obj:
            tax = 0
            for i in ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID'):
                tax += i.OD_ID.OD_TX_AMT
            return tax
        return 0.0
    
    def get_OD_NT_AMT(self, obj):
        if obj:
            net = 0
            for i in ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID).distinct('OD_ID'):
                net += i.OD_ID.OD_NT_AMT
            return net
        return 0.0
    
    def get_CU_OD_ID(self, obj):
        if obj:
            return obj.OD_ID.CU_OD_ID
        else:
            return ""
    
    def get_OD_SHP_AMT(self, obj):
        if obj.OD_ID:
            return obj.OD_ID.OD_SHP_AMT
        return None
    
    def get_item(self, obj):
        return ItemsSerializer(ItemShipmentList.objects.filter(OD_SHP_ID=obj.OD_SHP_ID, OD_ID=obj.OD_ID), many=True).data
    