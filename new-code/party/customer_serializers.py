''' Customer Serializer '''
import logging
from rest_framework import serializers
from party.models import Person
from .supplier_serializers import get_supplier_name, SupplierListSerializer, SupplierRetrieveSerializer
from .serializers import PartyContactDemoSerializer, contact_details_get
from order.models import Customer, OrderMaster
from django.db.models import Sum
logger = logging.getLogger(__name__)


class CustomerSerializer(serializers.ModelSerializer):
    ''' Customer Serializer '''
    class Meta:
        ''' Meta Class '''
        model = Customer
        fields = '__all__'


class CustomerListSerializer(serializers.ModelSerializer):
    ''' Customer List Serializer Class '''
    TYP_PRTY = serializers.SerializerMethodField()
    CUST_NM = serializers.SerializerMethodField()
    TY_GND_PRS = serializers.SerializerMethodField()
    DC_PRS_BRT = serializers.SerializerMethodField()
    CRT_BY = serializers.SerializerMethodField()
    UPDT_BY = serializers.SerializerMethodField()
    TL_OD = serializers.SerializerMethodField()
    TL_OD_AMT = serializers.SerializerMethodField()
    LT_OD_AMT = serializers.SerializerMethodField()
    LT_OD_DATE = serializers.SerializerMethodField()
    
    def get_TL_OD(self, obj):
        if obj:
            return OrderMaster.objects.filter(OD_CUST=obj.id).count()
        return None

    def get_TL_OD_AMT(self, obj):
        if obj:
            TL_OD_AMT = OrderMaster.objects.filter(OD_CUST=obj.id)
            if TL_OD_AMT:
                sum_amount = TL_OD_AMT.aggregate(sum_amount=Sum('OD_NT_AMT'))
                return sum_amount['sum_amount']
        return None

    def get_LT_OD_AMT(self, obj):
        if obj:
            last_order = OrderMaster.objects.filter(OD_CUST=obj.id).last()
            if last_order:
                return last_order.OD_NT_AMT
        return None
    
    def get_LT_OD_DATE(self, obj):
        if obj:
            last_order = OrderMaster.objects.filter(OD_CUST=obj.id).last()
            if last_order:
                return last_order.OD_DATE
        return None

    def get_TYP_PRTY(self, obj):
        ''' Party Type'''
        try:
            party_id = obj.ID_PRTY
            party_type_id = party_id.ID_PRTY_TYP
            return party_type_id.DE_PRTY_TYP
        except Exception:
            return None
        
    def get_CUST_NM(self, obj):
        ''' Get Customer Name '''
        supplier_name = obj.CUST_FNM + " " + obj.CUST_LNM
        return supplier_name

    def get_DC_PRS_BRT(self, obj):
        ''' Get Supplier DOB '''
        try:
            party_id = obj.ID_PRTY.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.DC_PRS_BRT
        except Exception:
            return None

    def get_TY_GND_PRS(self, obj):
        ''' Get Supplier Gender '''
        try:
            party_id = obj.ID_PRTY.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.TY_GND_PRS
        except Exception:
            return None

    def get_CRT_BY(self, obj):
        ''' Get Created By Name '''
        try:
            if obj.CRT_BY:
                return obj.CRT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''

    def get_UPDT_BY(self, obj):
        ''' Get Created By Name '''
        try:
            if obj.UPDT_BY:
                return obj.UPDT_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''

    class Meta:
        ''' Meta Class '''
        model = Customer
        fields = '__all__'


class CustomerRetrieveSerializer(CustomerListSerializer):
    ''' Customer Retrieve Serializer Class '''
    contact_details = serializers.SerializerMethodField(
        read_only=True)

    def get_contact_details(self, obj):
        ''' Egt Customer Contact Details '''
        return contact_details_get(obj)

    class Meta:
        ''' Meta Class '''
        model = Customer
        fields = '__all__'

class CustomerStatusSerializer(serializers.ModelSerializer):
    '''PickSheet Note status serializer'''

    def update(self, instance, validated_data):
        instance.CUST_ST = validated_data.get('status', instance.CUST_ST)
        instance.UPDT_BY = validated_data.get('UPDT_BY', instance.UPDT_BY)
        instance.save()
        return instance

    class Meta:
        '''Customer Meta class'''
        model = Customer
        fields = '__all__'
        read_only_fields = ["id", "CUST_ST"]