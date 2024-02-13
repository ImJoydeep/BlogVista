''' Manufacturer Views '''
import logging
import time
from django.utils import timezone
from copy import deepcopy
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from celery import shared_task
from worker.models import Manufacturer, Vendor
from party.supplier_filter import supplier_filter
from party.contact_details import (
    contact_details_create, contact_details_delete, manufacturer_export)
from party.models import (PartyContactMethod, PartyType,
                          PartyRole, Person, Organization)
from party.serializers import (
    PartySerializer, PartyRoleAssignmentSerializer,
    PersonSerializer, OrganizationSerializer)
from party.supplier_serializers import (VendorSerializer)
from party.manufacturer_serializers import (
    ManufacturerSerializer, ManufacturerListSerializer,
    ManufacturerDataSerializer, ManufacturerRetrieveSerializer)
from party.contact_details_schema import get_contact_details_schema


logger = logging.getLogger(__name__)

mf_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'TYP_PRTY': openapi.Schema(type=openapi.TYPE_STRING, description='Party Type(PR/OR) (PR = Persion, OR = Organization)'),
        'CD_MF': openapi.Schema(type=openapi.TYPE_STRING, description='Manufacturer Code'),
        'FN_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion First Name (Mandetory) if Party Type PR'),
        'MD_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion Middle Name if Party Type PR'),
        'LN_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion Last Name (Mandetory) if Party Type PR'),
        'TY_GND_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion Gender (Male/Female/Others) if Party Type PR'),
        'DC_PRS_BRT': openapi.Schema(type=openapi.TYPE_STRING, description='Person DOB ("YYYY-MM-DD") if Party Type PR'),
        'ID_LGL_STS': openapi.Schema(type=openapi.TYPE_INTEGER, description='Legal Status Type (1/2/3/4/5)  if Party Type OR'),
        'NM_LGL': openapi.Schema(type=openapi.TYPE_STRING, description='Legal Name (Mandetory)  if Party Type OR'),
        'NM_TRD': openapi.Schema(type=openapi.TYPE_STRING, description='Trade Name (Mandetory) if Party Type OR'),
        'ID_DUNS_NBR': openapi.Schema(type=openapi.TYPE_STRING, description='DUNSNumber if Party Type OR (Optional)'),
        'DC_FSC_YR_END': openapi.Schema(type=openapi.TYPE_STRING, description='Fiscal Year End Date ("YYYY-MM-DD") if Party Type OR'),
        'CD_LGL_ORGN_TYP': openapi.Schema(type=openapi.TYPE_STRING, description='Legal Organization Type (LLC/PLC/Partnership/Corporation) if Party Type OR'),
        'URL_PGPH_VN': openapi.Schema(type=openapi.TYPE_STRING, description='Photograph File Name'),
        'SC_MF': openapi.Schema(type=openapi.TYPE_STRING, description='Manufacturer Stataus (A/B)'),
        'contact_details': get_contact_details_schema(),

    }, required=['TYP_PRTY', 'CD_SPR'])
manufacturer_export_messages = "Manufacturer Export"


def raise_exception_on_party_serializer(serializer):
    '''Raise exception on party serializer'''
    if not serializer.is_valid():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Party Type id is not valid!"})


def raise_exception_on_party_role_asgmt_serializer(party_role_asgmt):
    '''Raise exception on party role asgmt serializer'''
    if not party_role_asgmt.is_valid():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Party Role assignment is not valid!"})


def create_person_or_organization(prty_type_code, save_datas, datas, body_datas, created_by):
    '''Create a new person or organization'''
    if prty_type_code == 'PR':
        person_data = {
            "ID_PRTY": save_datas.ID_PRTY,
            "FN_PRS": datas["CUST_FNM"] if datas.get("CUST_FNM") else datas["FN_PRS"],
            "LN_PRS": datas["CUST_LNM"] if datas.get("CUST_LNM") else datas["LN_PRS"],
            "TY_GND_PRS": datas["TY_GND_PRS"],
            "DC_PRS_BRT": datas["DC_PRS_BRT"],
            "PRS_CRT_BY": created_by,
        }
        personserializer = PersonSerializer(data=person_data)
        if not personserializer.is_valid(raise_exception=True):
            transaction.set_rollback(True)
            raise serializers.ValidationError(
                {"message": "Person data validation error!"})
        personserializer.save()
        person_save_data = personserializer.data
        body_datas.update(person_save_data)

    else:
        org_data = {
            "ID_PRTY": save_datas.ID_PRTY,
            "ID_LGL_STS": datas["ID_LGL_STS"],
            "NM_LGL": datas["NM_LGL"],
            "NM_TRD": datas["NM_TRD"],
            "ID_DUNS_NBR": datas['ID_DUNS_NBR'],
            "DC_FSC_YR_END": datas['DC_FSC_YR_END'],
            "CD_LGL_ORGN_TYP": datas["CD_LGL_ORGN_TYP"]
        }
        org_serializer = OrganizationSerializer(data=org_data)
        if not org_serializer.is_valid():
            transaction.set_rollback(True)
            raise serializers.ValidationError(
                {"message": "Organization data validation error!"})

        org_serializer.save()
        organization_save_data = org_serializer.data
        body_datas.update(organization_save_data)
    return body_datas


def insert_data_into_manufacturer(party_role_asign_save, datas, request, created_by, body_datas):
    '''Creation of a new manufacturer'''
    vendor_data = {
        "ID_PRTY_RO_ASGMT": party_role_asign_save.ID_PRTY_RO_ASGMT,
        "URL_PGPH_VN": datas.get('URL_PGPH_VN', None),
        "TY_VN": "MF"
    }
    vendor_serializer = VendorSerializer(data=vendor_data)
    if not vendor_serializer.is_valid():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Vendor serializer data validation error!"})

    vendor_save_data = vendor_serializer.save()
    if vendor_save_data.ID_VN:
        manufacturer_data = {
            "SC_MF": request.data.get('SC_MF'),
            "CD_MF": request.data.get('CD_MF'),
            "ID_VN": vendor_save_data.ID_VN,
            "CRT_BY": created_by
        }
        manufacturerserializer = ManufacturerSerializer(
            data=manufacturer_data)
        if not manufacturerserializer.is_valid():
            transaction.set_rollback(True)
            raise serializers.ValidationError(
                {"message": "Manufacturer data validation error!"})

        manufacturerserializer.save()
        manufacturer_save_data = manufacturerserializer.data
        body_datas.update(manufacturer_save_data)
    body_datas.update(vendor_serializer.data)
    return body_datas


def raise_exception_on_contact_details(contact):
    '''Raise exception on contact details'''
    if contact.get('errors'):
        raise serializers.ValidationError(
            {"message": "Contact details is not valid!"})


class ManufacturerCreateViews(CreateModelMixin, GenericAPIView):
    ''' Manufacturer Create Views Class '''
    permission_classes = [IsAuthenticated]
    serializer_class = PartySerializer

    @ swagger_auto_schema(tags=['Manufacturer'], operation_description="Create Manufacturer",
                          operation_summary="Create Manufacturer", request_body=mf_schema)
    def post(self, request, import_datas=None):
        ''' Create Manufacturer Party '''
        response = {}
        try:
            if request.data.get('CD_MF') is not None:
                if Manufacturer.objects.filter(CD_MF=request.data.get('CD_MF')).exists():
                    response["message"] = "Manufacture Code does exit. Please try with other code!"
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                response["message"] = "Please enter Manufacture Code!"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if import_datas is not None:
                datas = import_datas.data
                current_user_id = datas.get('user')
                created_by = current_user_id
            else:
                datas = request.data
                current_user_id = request.user
                created_by = current_user_id.id
            logger.info("Request Data : %s", datas)
            with transaction.atomic():
                prty_type_code = datas['TYP_PRTY']
                party_type = PartyType.objects.get(CD_PRTY_TYP=prty_type_code)
                logger.info("Party Type : %s, Party Type ID : %s",
                            party_type, party_type.ID_PRTY_TYP)

                logger.info("Created By : %s", created_by)
                party_insert_data = {
                    "ID_PRTY_TYP": party_type.ID_PRTY_TYP,
                    "BY_CRT_PRTY": created_by,
                }
                serializer = PartySerializer(data=party_insert_data)
                raise_exception_on_party_serializer(serializer)
                save_datas = serializer.save()
                body_datas = serializer.data

                if save_datas.ID_PRTY:
                    party_role = PartyRole.objects.get(TY_RO_PRTY="VND")
                    party_role_ids = party_role.ID_RO_PRTY
                    logger.info("Party Role : %s", party_role_ids)
                    party_role_asgmt_data = {
                        "ID_PRTY": save_datas.ID_PRTY,
                        "ID_RO_PRTY": party_role_ids
                    }
                    party_role_asgmt = PartyRoleAssignmentSerializer(
                        data=party_role_asgmt_data
                    )
                    raise_exception_on_party_role_asgmt_serializer(
                        party_role_asgmt)

                    party_role_asign_save = party_role_asgmt.save()
                    body_datas.update(party_role_asgmt.data)
                    body_datas = create_person_or_organization(
                        prty_type_code, save_datas, datas, body_datas, created_by)

                    if party_role_asign_save.ID_PRTY_RO_ASGMT:
                        body_datas = insert_data_into_manufacturer(
                            party_role_asign_save, datas, request, created_by, body_datas)

                        contact_details = datas.get('contact_details', None)
                        logger.info("Contact Details : %s", contact_details)
                        if contact_details is not None:
                            contact = contact_details_create(
                                datas, party_role_asign_save.ID_PRTY_RO_ASGMT)
                            raise_exception_on_contact_details(contact)

                return Response(body_datas, status=status.HTTP_200_OK)
        except Exception as excep:
            logger.exception(excep)
            return Response({"error": excep.__class__.__name__},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@shared_task
def manufacturer_export_function(page, page_size, search, copy_request_data, ordering, excludes_ids, device_id, device_flag, current_user, file_name, bsn_unit_id, file_type, columns):
    '''Manufacturer export function'''
    response = supplier_filter(
        'manufacturer', int(page), int(page_size), search, copy_request_data, ordering, excludes_ids)
    if len(response[0]) > 0:
        notification_data = {"device_id": device_id, "message_title": manufacturer_export_messages, "message_body": "Manufacturer Export Successfully Done",
                             "notification_type": manufacturer_export_messages, "event_id": None, "user_id": current_user, "file_name": file_name, "export_flag": True}
        location = 'export_files/'+str(file_name)
        if device_id is None or device_id == '':
            device_flag = False
        manufacturer_export(
            response, columns, bsn_unit_id, file_name, location, notification_data, device_flag, file_type)


class ManufacturerListViews(ListModelMixin, GenericAPIView):
    '''Manufacturer List View Class '''
    permission_classes = [IsAuthenticated]
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerListSerializer
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ID_MF', 'SC_MF', 'CD_MF']

    ordering_fields = '__all__'
    ordering = ['-ID_MF']

    def __init__(self):
        self.columns = {
            "SC_MF": "Status", "TYP_PRTY": "Manufacturer Type", "NM_MF": "Manufacturer Name", "CD_MF": "Manufacturer Code",
            "NM_LGL": "Legal Name", "NM_TRD": "Trade Name",
            "PH_CMPL": "Mobile Number", "EM_ADS": "Email Address",
            "CRT_DT": "Created Date & Time", "CRT_BY_NM": "Created By", "MDF_DT": "Updated Date & Time", "MDF_BY_NM": "Updated By"}
        self.column_type = {
            "SC_MF": "status", "TYP_PRTY": "str", "NM_MF": "str", "CD_MF": "str", "NM_LGL": "str",
            "NM_TRD": "str", "PH_CMPL": "str", "EM_ADS": "str",
            "CRT_DT": "Datetime", "CRT_BY_NM": "str", "MDF_DT": "Datetime", "MDF_BY_NM": "str"}

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['columns'] = self.columns
        response.data['column_type'] = self.column_type
        return response

    @ swagger_auto_schema(tags=['Manufacturer'], operation_description="Get all Manufacturer",
                          operation_summary="Get Manufacturer")
    def get(self, request, *args, **kwargs):
        ''' Manufacturer List '''
        logger.info("Manufacturer Get Request Data : %s", request.GET)
        manufacturer_id = request.GET.get('ID_MF')
        excludes_ids = request.GET.get('excludes_ids', None)
        search = request.GET.get('search', '')
        page_size = request.GET.get('page_size', Manufacturer.objects.count())
        page = request.GET.get('page', 1)
        export_flag = request.GET.get('export_flag', 0)
        bsn_unit_id = request.GET.get('ID_BSN_UN', 0)
        device_id = request.GET.get('device_id', None)
        file_type = request.GET.get('type', 'xlsx')
        logger.info("Manufacturer Id : %s", manufacturer_id)
        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('page', None)
        copy_request_data.pop('search', None)
        copy_request_data.pop('ID_MF', None)
        copy_request_data.pop('excludes_ids', None)
        copy_request_data.pop('export_flag', None)
        copy_request_data.pop('ID_BSN_UN', None)
        copy_request_data.pop('device_id', None)
        copy_request_data.pop('type', None)
        if export_flag == '1':
            logger.info(manufacturer_export_messages)
            device_flag = True
            current_user = request.user
            file_name = 'Manufacturer_Export_Data' + \
                str(time.time())+'.'+str(file_type).lower()
            manufacturer_export_function.delay(page, page_size, search, copy_request_data, request.GET.get('ordering'), excludes_ids,
                                               device_id, device_flag, current_user.id, file_name, bsn_unit_id, file_type, self.columns)
            message = {
                "message": "Export processing in background. You will get a file URL on Email as well as Notification."}
            stat = status.HTTP_200_OK
            return Response(message, status=stat)
        if (len(copy_request_data) > 0 and manufacturer_id is None) or (len(search) > 0 or request.GET.get('ordering') is not None):
            logger.info("Filter ANd Search")
            response = supplier_filter(
                'manufacturer', int(page), int(page_size), search, copy_request_data, request.GET.get('ordering'), excludes_ids)
            response = {
                "total": response[1],
                "page": int(page),
                "page_size": int(page_size),
                "results": response[0],
                "columns": self.columns,
                "column_type": self.column_type
            }
            return Response(response, status=status.HTTP_200_OK)
        elif manufacturer_id is None:
            logger.info("Manufacturer ID None")
            return self.list(request, *args, **kwargs)
        else:
            logger.info("Manufacturer ID  Not None")
            queryset = Manufacturer.objects.get(ID_MF=manufacturer_id)
            response_data = ManufacturerRetrieveSerializer(queryset)
            return Response(response_data.data)


class ManufacturerUpdateViews(GenericAPIView):
    ''' Manufacturer Update Views Class '''
    permission_classes = (IsAuthenticated,)
    serializer_class = ManufacturerDataSerializer
    lookup_url_kwarg = "ID_MF"

    def get_queryset(self):
        supplier = self.kwargs.get(self.lookup_url_kwarg)
        query = Manufacturer.objects.filter(
            ID_MF=supplier)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj

    @ swagger_auto_schema(tags=['Manufacturer'], operation_description="Manufacturer Update",
                          operation_summary="Manufacturer Update")
    def put(self, request, *args, **kwargs):
        ''' Update Manufacturer '''
        try:
            response = {}
            requested_data = request.data
            logger.info("Request Data : %s", requested_data)
            manufacturer_id = self.kwargs.get(self.lookup_url_kwarg)
            current_user = request.user
            party_type_codes = requested_data['TYP_PRTY']
            contact_details = requested_data.get('contact_details', [])
            if request.data.get('CD_MF') is not None:
                if Manufacturer.objects.filter(CD_MF=request.data.get('CD_MF')).exclude(ID_MF=manufacturer_id).exists():
                    message = f"Manufacture Code does exist.Please try with other code!!"
                    response["message"] = message
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                message = f"Please enter Manufacture Code!"
                response["message"] = message
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            supplier_obj = Manufacturer.objects.get(ID_MF=manufacturer_id)
            Manufacturer.objects.filter(ID_MF=manufacturer_id).update(
                SC_MF=requested_data.get('SC_MF'), CD_MF=requested_data.get('CD_MF'), MDF_BY=current_user, MDF_DT=timezone.now())
            vendor_objs = supplier_obj.ID_VN
            logger.info("vendor Object : %s", vendor_objs)
            party_object = vendor_objs.ID_PRTY_RO_ASGMT.ID_PRTY
            if party_type_codes == 'PR':
                person_data = {
                    "ID_PRTY": party_object.ID_PRTY,
                    "FN_PRS": requested_data["FN_PRS"],
                    "MD_PRS": requested_data["MD_PRS"],
                    "LN_PRS": requested_data["LN_PRS"],
                    "TY_GND_PRS": requested_data["TY_GND_PRS"],
                    "DC_PRS_BRT": requested_data["DC_PRS_BRT"]
                }
                person_object = Person.objects.get(ID_PRTY=party_object)
                person_serializer = PersonSerializer(
                    instance=person_object, data=person_data)
                if person_serializer.is_valid(raise_exception=True):
                    person_serializer.save()
                    person_save_data = person_serializer.data
                    logger.info("Person data : %s", person_save_data)
            else:
                organization_data = {
                    "ID_PRTY": party_object.ID_PRTY,
                    "ID_LGL_STS": requested_data["ID_LGL_STS"],
                    "NM_LGL": requested_data["NM_LGL"],
                    "NM_TRD": requested_data["NM_TRD"],
                    "ID_DUNS_NBR": requested_data['ID_DUNS_NBR'],
                    "DC_FSC_YR_END": requested_data['DC_FSC_YR_END'],
                    "CD_LGL_ORGN_TYP": requested_data["CD_LGL_ORGN_TYP"]
                }
                org_object = Organization.objects.get(ID_PRTY=party_object)
                org_serializer = OrganizationSerializer(
                    instance=org_object, data=organization_data)
                if org_serializer.is_valid(raise_exception=True):
                    org_serializer.save()
                    org_save_data = org_serializer.data
                    logger.info("organization data : %s", org_save_data)
            if requested_data['URL_PGPH_VN'] is not None:
                Vendor.objects.filter(ID_VN=vendor_objs.ID_VN).update(
                    URL_PGPH_VN=requested_data['URL_PGPH_VN'])

            contact_id_lists = PartyContactMethod.objects.filter(
                ID_PRTY_RO_ASGMT=vendor_objs.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT).values_list('ID_PRTY_CNCT_MTH', flat=True)[::1]

            logger.info("Contact ID List : %s", contact_id_lists)
            contact_details_delete(contact_id_lists, None)
            if contact_details:
                contacts = contact_details_create(
                    requested_data, vendor_objs.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT)
                if contacts.get('errors'):
                    return Response(contacts.get('errors'),
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Manufacturer Update Successfully"}, status=status.HTTP_200_OK)

        except Exception as excep:
            logger.exception(excep)
            return Response({"error": excep.__class__.__name__}, status=status.HTTP_400_BAD_REQUEST)
