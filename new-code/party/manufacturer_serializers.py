''' Supplier Serializer '''
import logging
from rest_framework import serializers
from worker.models import Manufacturer
from .supplier_serializers import get_supplier_name, SupplierListSerializer, SupplierRetrieveSerializer
from .serializers import PartyContactDemoSerializer

logger = logging.getLogger(__name__)


class ManufacturerSerializer(serializers.ModelSerializer):
    ''' Manufacturer Serializer '''
    class Meta:
        ''' Meta Class '''
        model = Manufacturer
        fields = '__all__'


class ManufacturerDataSerializer(serializers.Serializer):
    ''' Manufacturer Data Demo Serializer Class '''
    TYP_PRTY = serializers.CharField(required=True)
    CD_MF = serializers.CharField(required=True)
    MD_PRS = serializers.CharField(required=False)
    LN_PRS = serializers.CharField()
    TY_GND_PRS = serializers.CharField(required=False)
    ID_LGL_STS = serializers.CharField(required=False)
    CD_LGL_ORGN_TYP = serializers.CharField(required=False)
    FN_PRS = serializers.CharField()
    NM_LGL = serializers.CharField()
    DC_FSC_YR_END = serializers.CharField(required=False)
    NM_TRD = serializers.CharField()
    URL_PGPH_VN = serializers.CharField(required=False)
    DC_PRS_BRT = serializers.CharField(required=False)
    ID_DUNS_NBR = serializers.CharField(required=False)
    SC_MF = serializers.CharField()
    contact_details = PartyContactDemoSerializer(many=True)


class ManufacturerListSerializer(SupplierListSerializer, serializers.ModelSerializer):
    ''' Manufacturer List Serializer Class '''
    NM_MF = serializers.SerializerMethodField()

    def get_NM_MF(self, obj):
        ''' Get Manufacturer Name '''
        manufacturer_name = get_supplier_name(obj)
        return manufacturer_name

    class Meta:
        ''' Meta Class '''
        model = Manufacturer
        fields = '__all__'


class ManufacturerRetrieveSerializer(SupplierRetrieveSerializer, serializers.ModelSerializer):
    ''' Manufacturer Retrieve Serializer Class '''
    NM_MF = serializers.SerializerMethodField()

    def get_NM_MF(self, obj):
        ''' Get Manufacturer Name '''
        manufacturer_name = get_supplier_name(obj)
        return manufacturer_name

    class Meta:
        ''' Meta Class '''
        model = Manufacturer
        fields = '__all__'
