''' Supplier Serializer '''
import logging
from rest_framework import serializers
from worker.models import Vendor, Supplier
from .models import (ContactPurposeType, ContactMethodType,
                     PostalCodeReference, Telephone, EmailAddress, Address, PartyContactMethod,
                     State, Organization, Person, ITUCountry)
from .serializers import PartyContactMethodSerializer, AddressSerializer, PartyContactDemoSerializer, contact_details_get

logger = logging.getLogger(__name__)
legal_status_messages = "Legal Status: %s"


class SupplierDataSerializer(serializers.Serializer):
    ''' Supplier Data Demo Serializer Class '''
    TYP_PRTY = serializers.CharField(required=True)
    CD_SPR = serializers.CharField(required=True)
    FN_PRS = serializers.CharField()
    MD_PRS = serializers.CharField(required=False)
    LN_PRS = serializers.CharField()
    TY_GND_PRS = serializers.CharField(required=False)
    DC_PRS_BRT = serializers.CharField(required=False)
    ID_LGL_STS = serializers.CharField(required=False)
    NM_LGL = serializers.CharField()
    NM_TRD = serializers.CharField()
    ID_DUNS_NBR = serializers.CharField(required=False)
    DC_FSC_YR_END = serializers.CharField(required=False)
    CD_LGL_ORGN_TYP = serializers.CharField(required=False)
    URL_PGPH_VN = serializers.CharField(required=False)
    SC_SPR = serializers.CharField()
    contact_details = PartyContactDemoSerializer(many=True)


class VendorSerializer(serializers.ModelSerializer):
    ''' Vendor Serializer '''
    class Meta:
        ''' Meta Class '''
        model = Vendor
        fields = '__all__'


class SupplierSerializer(serializers.ModelSerializer):
    ''' Supplier Serializer '''
    class Meta:
        ''' Meta Class '''
        model = Supplier
        fields = '__all__'


def get_supplier_name(obj):
    ''' Get supplier name '''
    try:
        party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
        party_type = party_id.ID_PRTY_TYP.CD_PRTY_TYP
        if party_type == 'PR':
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.FN_PRS + " " + person.LN_PRS
        else:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.NM_TRD

    except Exception as exp:
        logger.exception(exp)
        return None


def fetch_vendor_multiple_email_address(contact_methods):
    '''Get vendor multiple email address'''
    email_lst = []
    for x in contact_methods:
        if x.ID_EM_ADS is not None:
            email_lst.append(
                x.ID_EM_ADS.EM_ADS_LOC_PRT + '@' + x.ID_EM_ADS.EM_ADS_DMN_PRT)
    if len(email_lst) == 1:
        email_address = str(email_lst[0])
    else:
        email_address = ", ".join(email_lst)
    return email_address


def fetch_vendor_multiple_phone_number(contact_methods):
    '''Get vendor multiple phone number'''
    phone_lst = []
    for x in contact_methods:
        if x.ID_PH is not None:
            phone_lst.append(x.ID_PH.PH_CMPL)
    if len(phone_lst) == 1:
        phone_number = str(phone_lst[0])
    else:
        phone_number = ", ".join(phone_lst)
    return phone_number


class SupplierListSerializer(serializers.ModelSerializer):
    ''' Supplier List Serializer Class '''
    ID_PRTY_RO_ASGMT = serializers.SerializerMethodField()
    ID_PRTY = serializers.SerializerMethodField()
    TYP_PRTY = serializers.SerializerMethodField()
    NM_SPR = serializers.SerializerMethodField()
    TY_GND_PRS = serializers.SerializerMethodField()
    DC_PRS_BRT = serializers.SerializerMethodField()
    EM_ADS = serializers.SerializerMethodField()
    PH_CMPL = serializers.SerializerMethodField()

    ID_LGL_STS = serializers.SerializerMethodField()
    NM_LGL_STS = serializers.SerializerMethodField()
    NM_LGL = serializers.SerializerMethodField()
    NM_TRD = serializers.SerializerMethodField()
    ID_DUNS_NBR = serializers.SerializerMethodField()
    DC_FSC_YR_END = serializers.SerializerMethodField()
    CD_LGL_ORGN_TYP = serializers.SerializerMethodField()
    NM_LGL_ORGN_TYP = serializers.SerializerMethodField()
    URL_PGPH_VN = serializers.SerializerMethodField()
    CRT_BY_NM = serializers.SerializerMethodField()
    MDF_BY_NM = serializers.SerializerMethodField()

    def get_TYP_PRTY(self, obj):
        ''' Party Type'''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            party_type_id = party_id.ID_PRTY_TYP
            return party_type_id.DE_PRTY_TYP
        except Exception:
            return None

    def get_EM_ADS(self, obj):
        ''' Get Email Address '''
        try:
            party_role_asgmt = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT
            if party_role_asgmt:
                contact_methods = PartyContactMethod.objects.filter(
                    ID_PRTY_RO_ASGMT=party_role_asgmt, CD_STS='A')
                if contact_methods.exists():
                    email_address = fetch_vendor_multiple_email_address(
                        contact_methods)
                    return email_address
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    def get_PH_CMPL(self, obj):
        ''' Get Phone Number '''
        try:
            party_role_asgmt = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT
            if party_role_asgmt:
                contact_methods = PartyContactMethod.objects.filter(
                    ID_PRTY_RO_ASGMT=party_role_asgmt, CD_STS='A')
                if contact_methods.exists():
                    phone_number = fetch_vendor_multiple_phone_number(
                        contact_methods)
                    return phone_number
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    def get_ID_PRTY_RO_ASGMT(self, obj):
        try:
            party_role_asgmt_id = obj.ID_VN.ID_PRTY_RO_ASGMT
            return party_role_asgmt_id.ID_PRTY_RO_ASGMT
        except Exception:
            return None

    def get_ID_PRTY(self, obj):
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            return party_id.ID_PRTY
        except Exception:
            return None

    def get_NM_SPR(self, obj):
        ''' Get Supplier Name '''
        supplier_name = get_supplier_name(obj)
        return supplier_name

    def get_DC_PRS_BRT(self, obj):
        ''' Get Supplier DOB '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.DC_PRS_BRT
        except Exception:
            return None

    def get_TY_GND_PRS(self, obj):
        ''' Get Supplier Gender '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.TY_GND_PRS
        except Exception:
            return None

    def get_NM_TRD(self, obj):
        ''' Get Supplier Trade Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.NM_TRD
        except Exception:
            return None

    def get_NM_LGL(self, obj):
        ''' Get Supplier Legal Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.NM_LGL
        except Exception:
            return None

    def get_DC_FSC_YR_END(self, obj):
        ''' Get Supplier Fiscal date '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.DC_FSC_YR_END
        except Exception:
            return None

    def get_ID_DUNS_NBR(self, obj):
        ''' Get Supplier DUNS Number '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.ID_DUNS_NBR
        except Exception:
            return None

    def get_NM_LGL_STS(self, obj):
        ''' Get Supplier Legal Status Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            logger.info(legal_status_messages, org_obj.ID_LGL_STS.DE_LGL_STS)
            return org_obj.ID_LGL_STS.DE_LGL_STS
        except Exception:
            return None

    def get_ID_LGL_STS(self, obj):
        ''' Get Supplier Legal Status '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            logger.info(legal_status_messages, org_obj.ID_LGL_STS)
            return org_obj.ID_LGL_STS.ID_LGL_STS
        except Exception:
            return None

    def get_CD_LGL_ORGN_TYP(self, obj):
        ''' Get Supplier Fiscal date '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.CD_LGL_ORGN_TYP.CD_LGL_ORGN_TYP
        except Exception:
            return None

    def get_URL_PGPH_VN(self, obj):
        try:
            vendor_id = obj.ID_VN
            return vendor_id.URL_PGPH_VN
        except Exception:
            return None

    def get_NM_LGL_ORGN_TYP(self, obj):
        ''' Get Supplier Fiscal date '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            legal_org_obj = org_obj.CD_LGL_ORGN_TYP
            return legal_org_obj.DE_LGL_ORGN_TYP
        except Exception:
            return None

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
            if obj.MDF_BY:
                return obj.MDF_BY.get_full_name()
            else:
                return ''
        except Exception:
            return ''

    class Meta:
        ''' Meta Class '''
        model = Supplier
        fields = '__all__'


class SupplierRetrieveSerializer(serializers.ModelSerializer):
    ''' Supplier Retrieve Serializer Class '''
    ID_PRTY_RO_ASGMT = serializers.SerializerMethodField()
    ID_PRTY = serializers.SerializerMethodField()
    TYP_PRTY = serializers.SerializerMethodField()
    FN_PRS = serializers.SerializerMethodField()
    LN_PRS = serializers.SerializerMethodField()
    MD_PRS = serializers.SerializerMethodField()
    NM_SPR = serializers.SerializerMethodField()

    TY_GND_PRS = serializers.SerializerMethodField()
    DC_PRS_BRT = serializers.SerializerMethodField()

    ID_LGL_STS = serializers.SerializerMethodField()
    NM_LGL_STS = serializers.SerializerMethodField()
    NM_LGL = serializers.SerializerMethodField()
    NM_TRD = serializers.SerializerMethodField()
    ID_DUNS_NBR = serializers.SerializerMethodField()
    DC_FSC_YR_END = serializers.SerializerMethodField()
    CD_LGL_ORGN_TYP = serializers.SerializerMethodField()
    NM_LGL_ORGN_TYP = serializers.SerializerMethodField()
    URL_PGPH_VN = serializers.SerializerMethodField()

    contact_details = serializers.SerializerMethodField(
        read_only=True)

    def get_NM_SPR(self, obj):
        ''' Get Supplier Name '''
        supplier_name = get_supplier_name(obj)
        return supplier_name

    def get_ID_PRTY_RO_ASGMT(self, obj):
        ''' Get Party Role Assignment '''
        party_role_asgmt_id = obj.ID_VN.ID_PRTY_RO_ASGMT
        return party_role_asgmt_id.ID_PRTY_RO_ASGMT

    def get_ID_PRTY(self, obj):
        ''' Get Party Id '''
        party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
        return party_id.ID_PRTY

    def get_TYP_PRTY(self, obj):
        ''' Party Type'''
        party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
        party_type_id = party_id.ID_PRTY_TYP
        return party_type_id.CD_PRTY_TYP

    def get_FN_PRS(self, obj):
        ''' Get Employee First Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.FN_PRS
        except Exception:
            return None

    def get_LN_PRS(self, obj):
        ''' Get Employee Last Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.LN_PRS
        except Exception:
            return None

    def get_MD_PRS(self, obj):
        ''' Get Employee Middle Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.MD_PRS
        except Exception:
            return None

    def get_TY_GND_PRS(self, obj):
        ''' Get Supplier Gender '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.TY_GND_PRS
        except Exception:
            return None

    def get_DC_PRS_BRT(self, obj):
        ''' Get Supplier DOB '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            person = Person.objects.get(ID_PRTY=party_id)
            return person.DC_PRS_BRT
        except Exception:
            return None

    def get_NM_LGL(self, obj):
        ''' Get Supplier Legal Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.NM_LGL
        except Exception:
            return None

    def get_NM_TRD(self, obj):
        ''' Get Supplier Trade Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.NM_TRD
        except Exception:
            return None

    def get_ID_DUNS_NBR(self, obj):
        ''' Get Supplier DUNS Number '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.ID_DUNS_NBR
        except Exception:
            return None

    def get_DC_FSC_YR_END(self, obj):
        ''' Get Supplier Fiscal date '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.DC_FSC_YR_END
        except Exception:
            return None

    def get_ID_LGL_STS(self, obj):
        ''' Get Supplier Legal Status '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            logger.info(legal_status_messages, org_obj.ID_LGL_STS)
            return org_obj.ID_LGL_STS.ID_LGL_STS
        except Exception:
            return None

    def get_NM_LGL_STS(self, obj):
        ''' Get Supplier Legal Status Name '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            logger.info(legal_status_messages, org_obj.ID_LGL_STS.DE_LGL_STS)
            return org_obj.ID_LGL_STS.DE_LGL_STS
        except Exception:
            return None

    def get_CD_LGL_ORGN_TYP(self, obj):
        ''' Get Supplier Fiscal date '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            return org_obj.CD_LGL_ORGN_TYP.CD_LGL_ORGN_TYP
        except Exception:
            return None

    def get_NM_LGL_ORGN_TYP(self, obj):
        ''' Get Supplier Fiscal date '''
        try:
            party_id = obj.ID_VN.ID_PRTY_RO_ASGMT.ID_PRTY
            org_obj = Organization.objects.get(ID_PRTY=party_id)
            legal_org_obj = org_obj.CD_LGL_ORGN_TYP
            return legal_org_obj.DE_LGL_ORGN_TYP
        except Exception:
            return None

    def get_URL_PGPH_VN(self, obj):
        try:
            vendor_id = obj.ID_VN
            return vendor_id.URL_PGPH_VN
        except Exception:
            return None

    def get_contact_details(self, obj):
        ''' Egt Supplier Contact Details '''
        return contact_details_get(obj.ID_VN)

    class Meta:
        ''' Meta Class '''
        model = Supplier
        fields = '__all__'
