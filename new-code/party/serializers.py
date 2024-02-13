''' Party Serializer File '''
import logging
from rest_framework import serializers
from party.models import (ContactPurposeType, ContactMethodType,
                          ISO3166_1Country, ISO3166_2CountrySubdivision, Party, PartyRoleAssignment,
                          Person, ITUCountry,
                          PostalCodeReference, Telephone, EmailAddress, Address, PartyContactMethod,
                          State, LegalStatusType, Organization)
from worker.models import (Worker, Employee)
from position.models import WorkerPositionAssignment
from accesscontrol.models import OperatorGroup, OperatorBusinessUnitAssignment
from workerschedule.models import WorkerAvailability
from accesscontrol.models import WorkerOperatorAssignment
from operators.serializers import OperatorBusinessUnitAssignmentSerializer

logger = logging.getLogger(__name__)
position_obj_messages = "Position Obj : %s"


class ContactPurposeTypeSerializer(serializers.ModelSerializer):
    ''' Contact Purpose Type Serializer Class '''

    class Meta:
        model = ContactPurposeType
        fields = '__all__'


class ContactMethodTypeSerializer(serializers.ModelSerializer):
    ''' Contact Method Type Serislizer Class '''

    class Meta:
        model = ContactMethodType
        fields = '__all__'


class LegalStatusTypeSerializer(serializers.ModelSerializer):
    ''' LegalStatusType Serislizer Class '''

    class Meta:
        ''' Meta Class '''
        model = LegalStatusType
        fields = '__all__'


class ITUCountrySerializer(serializers.ModelSerializer):
    ''' Country Serializer Class '''

    class Meta:
        model = ITUCountry
        fields = "__all__"

    def to_representation(self, instance):
        return {
            'code': instance.CD_CY_ITU,
            'name': instance.NM_CY_ITU
        }


class StateSerializer(serializers.ModelSerializer):
    ''' State Serializer Class '''

    class Meta:
        model = State
        fields = '__all__'

    def to_representation(self, instance):
        return {
            'id': instance.ID_ST,
            'name': instance.NM_ST
        }


class ISO3166_1CountrySerializer(serializers.ModelSerializer):
    ''' Country Serializer Class '''

    class Meta:
        model = ISO3166_1Country
        fields = ['CD_CY_ISO', 'NM_CY', 'CD_CY_ITU']

    def to_representation(self, instance):
        return {
            'code': instance.CD_CY_ISO,
            'name': instance.NM_CY
        }


class ISO3166_2CountrySubdivisionSerializer(serializers.ModelSerializer):
    ''' Country Subdivision Serializer Class '''

    class Meta:
        model = ISO3166_2CountrySubdivision
        fields = ['ID_ISO_3166_2_CY_SBDVN', 'NM_ISO_CY_PRMRY_SBDVN']

    def to_representation(self, instance):
        return {
            'id': instance.ID_ISO_3166_2_CY_SBDVN,
            'name': instance.NM_ISO_CY_PRMRY_SBDVN
        }


class PartySerializer(serializers.ModelSerializer):
    ''' Party Serializer Class '''

    class Meta:
        model = Party
        fields = "__all__"


class PartyRoleAssignmentSerializer(serializers.ModelSerializer):
    ''' Party Role Assignment Serializer Class '''

    class Meta:
        model = PartyRoleAssignment
        fields = "__all__"


class PersonSerializer(serializers.ModelSerializer):
    ''' Person Serializer Class '''

    class Meta:
        model = Person
        fields = "__all__"


class OrganizationSerializer(serializers.ModelSerializer):
    ''' Organization Serializer Class '''

    class Meta:
        ''' Meta Class '''
        model = Organization
        fields = "__all__"


class WorkerSerializer(serializers.ModelSerializer):
    ''' Worker Serializer Class '''

    class Meta:
        model = Worker
        fields = "__all__"


class WorkerAvailabilitySerializer(serializers.ModelSerializer):
    ''' Worker Availability Serializer Class '''
    ID_WRKR_AVLB = serializers.IntegerField(default=None)
    NM_GP_TM = serializers.SerializerMethodField(read_only=True)
    work_location = serializers.SerializerMethodField(read_only=True)

    def get_NM_GP_TM(self, obj):
        ''' Get Time Group Name '''
        if obj.ID_GP_TM:
            time_grp_obj = obj.ID_GP_TM
            time_grp_name = time_grp_obj.NM_GP_TM
            return time_grp_name
        else:
            return None

    def get_work_location(self, obj):
        ''' Get Work Location Name '''
        if obj.ID_LCN:
            location_obj = obj.ID_LCN
            work_location_name = location_obj.NM_LCN
            return work_location_name
        else:
            return None

    class Meta:
        model = WorkerAvailability
        fields = "__all__"


class EmployeeSerializer(serializers.ModelSerializer):
    ''' Employee Serializer Class '''

    class Meta:
        model = Employee
        fields = "__all__"


class PostalCodeSerializer(serializers.ModelSerializer):
    ''' PostalCodeReference Serializer Class '''

    class Meta:
        model = PostalCodeReference
        fields = "__all__"


class TelephoneSerializer(serializers.ModelSerializer):
    ''' Telephone Serializer Class '''

    class Meta:
        model = Telephone
        fields = "__all__"


class EmailAddressSerializer(serializers.ModelSerializer):
    ''' EmailAddress Serializer Class '''

    class Meta:
        model = EmailAddress
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    ''' Telephone Serializer Class '''

    class Meta:
        model = Address
        fields = "__all__"


class PartyContactMethodSerializer(serializers.ModelSerializer):
    ''' PartyContactMethod Serializer Class '''

    class Meta:
        ''' Meta Class'''
        model = PartyContactMethod
        fields = ['ID_PRTY_CNCT_MTH', 'CD_TYP_CNCT_PRPS', 'CD_TYP_CNCT_MTH',
                  'ID_PRTY_RO_ASGMT', 'ID_ADS', 'ID_EM_ADS', 'ID_PH', 'CD_STS', 'ID_WB_STE', 'IS_SHIPPING', 'IS_BILLING']


class PartyContactDemoSerializer(serializers.Serializer):
    CD_TYP_CNCT_PRPS = serializers.CharField(max_length=10)
    CD_TYP_CNCT_MTH = serializers.CharField()
    A1_ADS = serializers.CharField()
    A2_ADS = serializers.CharField(required=False)
    CI_CNCT = serializers.CharField(required=False)
    ST_CNCT = serializers.CharField(required=False)
    CD_CY_ITU = serializers.CharField(required=False)
    PH_CMPL = serializers.CharField(required=False)
    EM_ADS = serializers.CharField(required=False)
    CD_PSTL = serializers.CharField(required=False)
    ID_ST = serializers.IntegerField(required=False)


class EmployeeDataSerializer(serializers.Serializer):
    ''' Employee Data Demo Serializer Class '''

    FN_PRS = serializers.CharField(required=True)
    MD_PRS = serializers.CharField()
    LN_PRS = serializers.CharField(required=True)
    URL_PGPH_WRKR = serializers.CharField(required=True)
    SC_EM = serializers.CharField(required=True)
    contact_details = PartyContactDemoSerializer(many=True)


class WorkerPositionAsgmtSerializer(serializers.ModelSerializer):
    ''' Worker Position Assignment Serializer Class '''
    ID_ASGMT_WRKR_PSN = serializers.IntegerField(default=None)
    position_name = serializers.SerializerMethodField(read_only=True)
    department_name = serializers.SerializerMethodField(read_only=True)
    work_location = serializers.SerializerMethodField(read_only=True)

    def get_work_location(self, obj):
        ''' Get Work Location Name '''
        try:
            position_obj = obj.ID_PST
            logger.info(position_obj_messages, position_obj)
            location_obj = position_obj.ID_LCN
            logger.info("Location Obj : %s", location_obj)
            work_location_name = location_obj.NM_LCN
            return work_location_name
        except Exception as exp:
            logger.info(exp)
            return None

    def get_department_name(self, obj):
        ''' Get Department Name '''
        position_obj = obj.ID_PST
        logger.info(position_obj_messages, position_obj)
        dept_obj = position_obj.department_id
        logger.info("Department Obj : %s", dept_obj)
        department_name = dept_obj.name
        return department_name

    def get_position_name(self, obj):
        ''' Get Position Name '''
        position_obj = obj.ID_PST
        logger.info(position_obj_messages, position_obj.NM_TTL)
        return position_obj.NM_TTL

    class Meta:
        model = WorkerPositionAssignment
        fields = "__all__"


class WorkerOperatorAsgmtSerializer(serializers.ModelSerializer):
    ''' Worker Operator Assignment Serializer Class '''
    ID_ASGMT_WRKR_OPR = serializers.IntegerField(default=None)
    operator_name = serializers.SerializerMethodField(read_only=True)
    permission_set = serializers.SerializerMethodField(read_only=True)
    bu_name = serializers.SerializerMethodField(read_only=True)
    bu_details = serializers.SerializerMethodField(read_only=True)

    def get_bu_details(self, obj):
        ''' Get business unit details of this operator'''
        bunit_list = []
        try:
            operator_obj = obj.ID_OPR
            logger.info("Operator obj : %s", operator_obj)

            business_unit = OperatorBusinessUnitAssignment.objects.filter(
                ID_OPR=operator_obj)
            logger.info("Opr Bu Obj : %s", business_unit)
            bunit_list = OperatorBusinessUnitAssignmentSerializer(
                business_unit.all(), many=True).data
            return bunit_list
        except Exception as exp:
            logger.exception("Business Unit Details Exception : %s", exp)
            return []

    def get_bu_name(self, obj):
        ''' Get business unit name of this operator'''
        try:
            operator_obj = obj.ID_OPR
            logger.info("Operator obj : %s", operator_obj)

            business_unit = OperatorBusinessUnitAssignment.objects.filter(
                ID_OPR=operator_obj)
            logger.info("Opr Bu Obj : %s", business_unit)
            bunit_list = ", ".join(
                [x['b_unit_name'] for x in OperatorBusinessUnitAssignmentSerializer(
                    business_unit.all(), many=True).data])
            return bunit_list
        except Exception as exp:
            logger.exception(exp)
            return None

    def get_permission_set(self, obj):
        ''' Get Permission Set '''
        try:
            if obj.ID_OPR:
                operator_obj = obj.ID_OPR
                logger.info("Operator obj permission : %s", operator_obj)
                opr_grp_obj = OperatorGroup.objects.get(ID_OPR=operator_obj)
                logger.info("Operator Group Obj : %s",
                            opr_grp_obj)
                work_group_obj = opr_grp_obj.ID_GP_WRK
                logger.info("Work Group : %s", work_group_obj)
                work_group_name = work_group_obj.NM_GP_WRK
                logger.info("Work Group Name : %s", work_group_name)
                return work_group_name
            else:
                return None
        except Exception as exp:
            logger.exception(exp)
            return None

    def get_operator_name(self, obj):
        ''' Get Operator Name '''
        try:
            operator_obj = obj.ID_OPR
            operator_name = operator_obj.NM_USR
            logger.info("Operator Name : %s", operator_name)
            return operator_name
        except Exception as exp:
            logger.exception(exp)
            return None

    class Meta:
        model = WorkerOperatorAssignment
        fields = "__all__"


class EmployeeUpdateSerializer(serializers.Serializer):
    ''' Employee Update Serializer Class '''
    URL_PGPH_WRKR = serializers.CharField(required=False)
    FN_PRS = serializers.CharField(required=False)
    LN_PRS = serializers.CharField(required=False)
    MD_PRS = serializers.CharField(required=False)
    SC_EM = serializers.CharField(required=True)

    position_details = WorkerPositionAsgmtSerializer(many=True)
    work_availability = WorkerAvailabilitySerializer(many=True)
    operator_details = WorkerOperatorAsgmtSerializer(many=True)
    contact_details = PartyContactMethodSerializer(many=True)

    class Meta:
        model = Employee
        fields = '__all__'


def contact_details_get(obj):
    ''' Egt Employee Contact Details '''
    party_role_asgmt = obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT
    logger.info("Party Role Assignment ID : %s", party_role_asgmt)
    contact_methods = PartyContactMethod.objects.filter(
        ID_PRTY_RO_ASGMT=party_role_asgmt)
    contact_method_list = PartyContactMethodSerializer(
        contact_methods, many=True).data
    logger.info("Contact Method List : %s", contact_method_list)
    for contacts in contact_method_list:
        address_id = contacts['ID_ADS']
        address = Address.objects.get(ID_ADS=address_id)
        address_data = AddressSerializer(address).data
        logger.info("Address : %s", address_data)
        contacts.update(address_data)
        state_id = address_data.get('ID_ST', None)
        country_id = address_data.get('CD_CY_ITU', None)

        contacts['NM_ST'] = None
        if state_id:
            state_obj = State.objects.get(
                ID_ST=state_id)
            contacts['NM_ST'] = state_obj.NM_ST

        contacts['NM_CY_ITU'] = None
        if country_id:
            country_obj = ITUCountry.objects.get(
                CD_CY_ITU=country_id)
            contacts['NM_CY_ITU'] = country_obj.NM_CY_ITU

        contact_purpose = contacts.get('CD_TYP_CNCT_PRPS', None)
        contacts['NM_TYP_CNCT_PRPS'] = None
        if contact_purpose:
            contact_purpose_obj = ContactPurposeType.objects.get(
                CD_TYP_CNCT_PRPS=contact_purpose)
            contacts['NM_TYP_CNCT_PRPS'] = contact_purpose_obj.NM_TYP_CNCT_PRPS

        contact_method = contacts.get('CD_TYP_CNCT_MTH', None)
        contacts['NM_TYP_CNCT_MTH'] = None
        if contact_method:
            contact_method_obj = ContactMethodType.objects.get(
                CD_TYP_CNCT_MTH=contact_method)
            contacts['NM_TYP_CNCT_MTH'] = contact_method_obj.NM_TYP_CNCT_MTH

        email_ads_id = contacts.get('ID_EM_ADS', None)
        contacts['EM_ADS'] = None
        if email_ads_id:
            email_obj = EmailAddress.objects.get(
                ID_EM_ADS=email_ads_id)
            contacts['EM_ADS'] = email_obj.EM_ADS_LOC_PRT + \
                '@' + email_obj.EM_ADS_DMN_PRT

        phone_id = contacts.get('ID_PH', None)
        contacts['PH_CMPL'] = None
        if phone_id:
            phone_obj = Telephone.objects.get(
                ID_PH=phone_id)
            contacts['PH_CMPL'] = phone_obj.PH_CMPL

        postal_code_id = contacts.get('ID_PSTL_CD', None)
        contacts['CD_PSTL'] = None
        if postal_code_id:
            postal_obj = PostalCodeReference.objects.get(
                ID_PSTL_CD=postal_code_id)
            contacts['CD_PSTL'] = postal_obj.CD_PSTL

    return contact_method_list


class EmployeeRetrieveSerializer(serializers.ModelSerializer):
    ''' Employee Update Serializer Class '''
    URL_PGPH_WRKR = serializers.SerializerMethodField()
    FN_PRS = serializers.SerializerMethodField()
    LN_PRS = serializers.SerializerMethodField()
    MD_PRS = serializers.SerializerMethodField()

    position_details = serializers.SerializerMethodField(
        read_only=True)
    work_availability = serializers.SerializerMethodField(
        read_only=True)
    operator_details = serializers.SerializerMethodField(read_only=True)
    contact_details = serializers.SerializerMethodField(
        read_only=True)

    def get_FN_PRS(self, obj):
        ''' Get Employee First Name '''
        party_id = obj.ID_WRKR.ID_PRTY_RO_ASGMT.ID_PRTY
        person = Person.objects.get(ID_PRTY=party_id)
        return person.FN_PRS

    def get_LN_PRS(self, obj):
        ''' Get Employee Last Name '''
        party_id = obj.ID_WRKR.ID_PRTY_RO_ASGMT.ID_PRTY
        person = Person.objects.get(ID_PRTY=party_id)
        return person.LN_PRS

    def get_MD_PRS(self, obj):
        ''' Get Employee Middle Name '''
        party_id = obj.ID_WRKR.ID_PRTY_RO_ASGMT.ID_PRTY
        person = Person.objects.get(ID_PRTY=party_id)
        return person.MD_PRS

    def get_URL_PGPH_WRKR(self, obj):
        worker_id = obj.ID_WRKR
        return worker_id.URL_PGPH_WRKR

    def get_contact_details(self, obj):
        ''' Egt Employee Contact Details '''
        return contact_details_get(obj.ID_WRKR)

    def get_position_details(self, obj):
        ''' Position Details '''
        logger.info("Get Position Details")
        logger.info("Position Details Object : %s", obj.ID_WRKR)
        psn_wrkr_obj = WorkerPositionAssignment.objects.filter(
            ID_WRKR=obj.ID_WRKR)

        wrkr_position_list = WorkerPositionAsgmtSerializer(
            psn_wrkr_obj, many=True)
        logger.info("Worker Position : %s", wrkr_position_list.data)
        return wrkr_position_list.data

    def get_work_availability(self, obj):
        ''' Worker Availability '''
        logger.info("Get Worker Availability")
        logger.info("Work Availability Object : %s", obj.ID_WRKR)
        wrkr_avlb_obj = WorkerAvailability.objects.filter(
            ID_WRKR=obj.ID_WRKR)
        wrkr_avlb_list = WorkerAvailabilitySerializer(
            wrkr_avlb_obj, many=True)
        logger.info("Worker Position : %s", wrkr_avlb_list.data)
        return wrkr_avlb_list.data

    def get_operator_details(self, obj):
        ''' Operator Details'''
        logger.info("Get Operator Details")
        logger.info("Operator Details Object : %s", obj.ID_WRKR)
        opr_wrkr_obj = WorkerOperatorAssignment.objects.filter(
            ID_WRKR=obj.ID_WRKR)
        opr_wrkr_list = WorkerOperatorAsgmtSerializer(
            opr_wrkr_obj, many=True)
        logger.info("Operator Worker List : %s", opr_wrkr_list.data)
        return opr_wrkr_list.data

    class Meta:
        model = Employee
        fields = '__all__'


class EmployeeListSerializer(serializers.ModelSerializer):
    ''' Employee List Serializer Class '''
    ID_PRTY_RO_ASGMT = serializers.SerializerMethodField()
    ID_PRTY = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    URL_PGPH_WRKR = serializers.SerializerMethodField()
    EM_ADS = serializers.SerializerMethodField()
    PH_CMPL = serializers.SerializerMethodField()
    position_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    operator = serializers.SerializerMethodField()
    permission_set = serializers.SerializerMethodField()
    ID_USR_CRT = serializers.SerializerMethodField(read_only=True)
    ID_USR_UPDT = serializers.SerializerMethodField(read_only=True)

    def get_permission_set(self, obj):
        ''' Get Operator Permission Set '''
        logger.info(" Get Operator Permission Set ")
        try:
            worker_obj = obj.ID_WRKR
            # logger.info("Worker Obj : %s", worker_obj)
            wrkr_opr_obj = WorkerOperatorAssignment.objects.get(
                ID_WRKR=worker_obj)
            operator_obj = wrkr_opr_obj.ID_OPR
            opr_grp_obj = OperatorGroup.objects.get(ID_OPR=operator_obj)
            # logger.info("Opr Group Obj : %s", opr_grp_obj)
            permission_set = opr_grp_obj.ID_GP_WRK.NM_GP_WRK
            return permission_set
        except Exception as exp:
            logger.exception(exp)
            return None

    def get_operator(self, obj):
        ''' Get Operator '''
        logger.info("===================== Get Operator ===================")
        try:
            worker_obj = obj.ID_WRKR
            # logger.info("Worker Obj : %s", worker_obj)
            wrkr_opr_obj = WorkerOperatorAssignment.objects.get(
                ID_WRKR=worker_obj)
            operator_obj = wrkr_opr_obj.ID_OPR
            operator_name = operator_obj.NM_USR
            # logger.info("Operator Name : %s", operator_name)
            return operator_name
        except Exception as exp:
            logger.exception("Operator Exception : %s", exp)
            return None

    def get_department_name(self, obj):
        ''' Get Department Name '''
        logger.info("Get Departmentname")
        try:
            worker_obj = obj.ID_WRKR
            wrkr_position = WorkerPositionAssignment.objects.filter(
                ID_WRKR=worker_obj)
            if wrkr_position.exists():
                department_lst = list(x.ID_PST.department_id.name
                                      for x in wrkr_position)
                if len(department_lst) == 1:
                    position_name = str(department_lst[0])
                else:
                    position_name = ", ".join(department_lst)
                return position_name
            else:
                return None
        except Exception:
            return None

    def get_position_name(self, obj):
        ''' Get Position Name '''
        logger.info("Get Position Name")
        try:
            worker_obj = obj.ID_WRKR

            wrkr_position = WorkerPositionAssignment.objects.filter(
                ID_WRKR=worker_obj)
            if wrkr_position.exists():
                position_lst = list(x.ID_PST.NM_TTL
                                    for x in wrkr_position)
                if len(position_lst) == 1:
                    position_name = str(position_lst[0])
                else:
                    position_name = ", ".join(position_lst)
                return position_name
            else:
                return None
        except Exception:
            return None

    def get_EM_ADS(self, obj):
        ''' Get Email Address '''
        try:
            party_role_asgmt = obj.ID_WRKR.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT
            if party_role_asgmt:
                contact_methods = PartyContactMethod.objects.filter(
                    ID_PRTY_RO_ASGMT=party_role_asgmt, CD_STS='A').last()
                email_obj = contact_methods.ID_EM_ADS
                return email_obj.EM_ADS_LOC_PRT + '@' + email_obj.EM_ADS_DMN_PRT
            else:
                return None
        except Exception:
            return None

    def get_PH_CMPL(self, obj):
        ''' Get Phone Number '''
        try:
            party_role_asgmt = obj.ID_WRKR.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT
            if party_role_asgmt:
                contact_methods = PartyContactMethod.objects.filter(
                    ID_PRTY_RO_ASGMT=party_role_asgmt, CD_STS='A').last()
                phone_obj = contact_methods.ID_PH
                return phone_obj.PH_CMPL
            else:
                return None
        except Exception:
            return None

    def get_ID_PRTY_RO_ASGMT(self, obj):
        party_role_asgmt_id = obj.ID_WRKR.ID_PRTY_RO_ASGMT
        return party_role_asgmt_id.ID_PRTY_RO_ASGMT

    def get_ID_PRTY(self, obj):
        party_id = obj.ID_WRKR.ID_PRTY_RO_ASGMT.ID_PRTY
        return party_id.ID_PRTY

    def get_employee_name(self, obj):
        ''' Get Employee Name '''
        party_id = obj.ID_WRKR.ID_PRTY_RO_ASGMT.ID_PRTY
        person = Person.objects.get(ID_PRTY=party_id)
        return person.FN_PRS + " " + person.LN_PRS

    def get_URL_PGPH_WRKR(self, obj):
        worker_id = obj.ID_WRKR
        return worker_id.URL_PGPH_WRKR

    def get_ID_USR_CRT(self, obj):
        ''' Get Created User Name '''
        try:
            if obj.ID_USR_CRT:
                return obj.ID_USR_CRT.get_full_name()
            else:
                return ''
        except Exception as user_exp:
            logger.exception("Created User Exception : %s", user_exp)
            return ''

    def get_ID_USR_UPDT(self, obj):
        ''' Get Updated User Name '''
        try:
            if obj.ID_USR_UPDT:
                return obj.ID_USR_UPDT.get_full_name()
            else:
                return ''
        except Exception as user_exp:
            logger.exception("Created User Exception : %s", user_exp)
            return ''

    class Meta:
        model = Employee
        fields = '__all__'
