''' Supplier Views '''
import logging
import time
import pandas as pd
from copy import deepcopy
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import filters
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from worker.models import Supplier, Vendor
from party.supplier_filter import supplier_filter
from party.contact_details import contact_details_create, contact_details_delete, supplier_export
from party.models import (PartyContactMethod, PartyType,
                          PartyRole, Person, Organization)
from party.serializers import (
    PartySerializer, PartyRoleAssignmentSerializer, PersonSerializer, OrganizationSerializer)
from party.supplier_serializers import (VendorSerializer, SupplierSerializer,
                                        SupplierDataSerializer, SupplierListSerializer,
                                        SupplierRetrieveSerializer)
from party.contact_details_schema import get_contact_details_schema

logger = logging.getLogger(__name__)
vendor_export_messages = "Vendor Export"

supplier_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'TYP_PRTY': openapi.Schema(type=openapi.TYPE_STRING, description='Party Type(PR/OR) (PR = Persion, OR = Organization)'),
        'CD_SPR': openapi.Schema(type=openapi.TYPE_STRING, description='Supplier Code'),
        'FN_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion First Name if Party Type PR'),
        'MD_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion Middle Name if Party Type PR'),
        'LN_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion Last Name if Party Type PR'),
        'TY_GND_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Persion Gender (Male/Female/Others) if Party Type PR'),
        'DC_PRS_BRT': openapi.Schema(type=openapi.TYPE_STRING, description='Person DOB ("YYYY-MM-DD") if Party Type PR'),
        'ID_LGL_STS': openapi.Schema(type=openapi.TYPE_INTEGER, description='Legal Status Type (1/2/3/4/5)  if Party Type OR'),
        'NM_LGL': openapi.Schema(type=openapi.TYPE_STRING, description='Legal Name  if Party Type OR'),
        'NM_TRD': openapi.Schema(type=openapi.TYPE_STRING, description='Trade Name if Party Type OR'),
        'ID_DUNS_NBR': openapi.Schema(type=openapi.TYPE_STRING, description='DUNSNumber if Party Type OR (Optional)'),
        'DC_FSC_YR_END': openapi.Schema(type=openapi.TYPE_STRING, description='Fiscal Year End Date ("YYYY-MM-DD") if Party Type OR'),
        'CD_LGL_ORGN_TYP': openapi.Schema(type=openapi.TYPE_STRING, description='Legal Organization Type (LLC/PLC/Partnership/Corporation) if Party Type OR'),
        'URL_PGPH_VN': openapi.Schema(type=openapi.TYPE_STRING, description='Photograph File Name'),
        'SC_SPR': openapi.Schema(type=openapi.TYPE_STRING, description='Supplier Stataus (A/B)'),
        'contact_details': get_contact_details_schema(),

    }, required=['TYP_PRTY', 'CD_SPR'])


def supplier_person_or_organization_details_save(party_type_code, save_data, data, created_by, body_data):
    ''' Save Supplier Information for person or organization'''
    if party_type_code == 'PR':
        person_data = {
            "ID_PRTY": save_data.ID_PRTY,
            "FN_PRS": data["FN_PRS"],
            "MD_PRS": data["MD_PRS"],
            "LN_PRS": data["LN_PRS"],
            "TY_GND_PRS": data["TY_GND_PRS"],
            "DC_PRS_BRT": data["DC_PRS_BRT"],
            "PRS_CRT_BY": created_by,
        }
        personserializer = PersonSerializer(data=person_data)
        if personserializer.is_valid(raise_exception=True):
            personserializer.save()
            person_save_data = personserializer.data
            body_data.update(person_save_data)
    else:
        org_data = {
            "ID_PRTY": save_data.ID_PRTY,
            "ID_LGL_STS": data["ID_LGL_STS"],
            "NM_LGL": data["NM_LGL"],
            "NM_TRD": data["NM_TRD"],
            "ID_DUNS_NBR": data['ID_DUNS_NBR'],
            "DC_FSC_YR_END": data['DC_FSC_YR_END'],
            "CD_LGL_ORGN_TYP": data["CD_LGL_ORGN_TYP"]
        }
        orgserializer = OrganizationSerializer(data=org_data)
        if orgserializer.is_valid(raise_exception=True):
            orgserializer.save()
            org_save_data = orgserializer.data
            body_data.update(org_save_data)
    return body_data


def save_supplier_data(vendorserializer, request, created_by, body_data):
    '''Save supplier data'''
    if vendorserializer.is_valid(raise_exception=True):
        vendor_save_data = vendorserializer.save()
        if vendor_save_data.ID_VN:
            supplier_data = {
                "SC_SPR": request.data.get('SC_SPR'),
                "CD_SPR": request.data.get('CD_SPR'),
                "ID_VN": vendor_save_data.ID_VN,
                "CRT_BY": created_by
            }
            supplierserializer = SupplierSerializer(
                data=supplier_data)
            if supplierserializer.is_valid(raise_exception=True):
                supplierserializer.save()
                supplier_save_data = supplierserializer.data
                body_data.update(supplier_save_data)
        body_data.update(vendorserializer.data)
    return body_data


def raise_exception_for_supplier_contact_error(contact_details, data, partyroleasign_save):
    '''Raise exception'''
    if contact_details is not None:
        contact = contact_details_create(
            data, partyroleasign_save.ID_PRTY_RO_ASGMT)
        if contact.get('errors'):
            transaction.set_rollback(True)
            raise serializers.ValidationError(
                {"message": "Contacts data validation error!"})


class SupplierCreateViews(CreateModelMixin, GenericAPIView):
    ''' Supplier Create Views Class '''
    permission_classes = [IsAuthenticated]
    serializer_class = PartySerializer
    serializer_class = SupplierDataSerializer

    @ swagger_auto_schema(tags=['Supplier'], operation_description="Create Supplier",
                          operation_summary="Create Supplier", request_body=supplier_schema)
    def post(self, request, import_data=None):
        ''' Create Supplier Party '''
        body_data = []
        response = {}
        try:
            if request.data.get('CD_SPR') is not None:
                if Supplier.objects.filter(CD_SPR=request.data.get('CD_SPR')).exists():
                    response["message"] = "Vendor Code does exist. Please try with other code!"
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                response["message"] = "Please enter Vendor Code!"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            if import_data is not None:
                data = import_data.data
                current_user = data.get('user')
                created_by = current_user
            else:
                data = request.data
                current_user = request.user
                created_by = current_user.id
            logger.info("Request Data : %s", data)
            with transaction.atomic():
                party_type_code = data['TYP_PRTY']
                partytype = PartyType.objects.get(CD_PRTY_TYP=party_type_code)
                logger.info("Party Type : %s, Party Type ID : %s",
                            partytype, partytype.ID_PRTY_TYP)

                logger.info("Created By : %s", created_by)
                partytbldata = {
                    "ID_PRTY_TYP": partytype.ID_PRTY_TYP,
                    "BY_CRT_PRTY": created_by,
                }
                serializer = PartySerializer(data=partytbldata)
                if serializer.is_valid(raise_exception=True):
                    save_data = serializer.save()
                    body_data = serializer.data
                if save_data.ID_PRTY:
                    partyrole = PartyRole.objects.get(TY_RO_PRTY="SPL")
                    party_role_id = partyrole.ID_RO_PRTY
                    logger.info("Party Role : %s", party_role_id)
                    partyrole_asgmt_data = {
                        "ID_PRTY": save_data.ID_PRTY,
                        "ID_RO_PRTY": party_role_id
                    }
                    partyrole_asgmt = PartyRoleAssignmentSerializer(
                        data=partyrole_asgmt_data
                    )
                    if partyrole_asgmt.is_valid(raise_exception=True):
                        partyroleasign_save = partyrole_asgmt.save()
                        body_data.update(partyrole_asgmt.data)
                    body_data = supplier_person_or_organization_details_save(
                        party_type_code, save_data, data, created_by, body_data)

                    if partyroleasign_save.ID_PRTY_RO_ASGMT:
                        vendordata = {
                            "ID_PRTY_RO_ASGMT": partyroleasign_save.ID_PRTY_RO_ASGMT,
                            "URL_PGPH_VN": data['URL_PGPH_VN'],
                            "TY_VN": "SUP"
                        }
                        vendorserializer = VendorSerializer(data=vendordata)
                        save_supplier_data(
                            vendorserializer, request, created_by, body_data)
                        contact_details = data.get('contact_details', None)
                        logger.info("Contact Details : %s", contact_details)
                        raise_exception_for_supplier_contact_error(
                            contact_details, data, partyroleasign_save)

                return Response(body_data, status=status.HTTP_200_OK)
        except Exception as exp:
            logger.exception(exp)
            return Response({"error": exp.__class__.__name__},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupplierListViews(ListModelMixin, GenericAPIView):
    '''Supplier List View Class '''
    permission_classes = [IsAuthenticated]
    queryset = Supplier.objects.all()
    serializer_class = SupplierListSerializer
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ID_SPR', 'SC_SPR', 'CD_SPR']

    ordering_fields = '__all__'
    ordering = ['-ID_SPR']

    def __init__(self):
        self.columns = {
            "SC_SPR": "Status", "TYP_PRTY": "Vendor Type", "NM_SPR": "Vendor Name", "CD_SPR": "Vendor Code",
            "NM_LGL": "Legal Name", "NM_TRD": "Trade Name",
            "PH_CMPL": "Mobile Number", "EM_ADS": "Email Address",
            "CRT_DT": "Created Date & Time", "CRT_BY_NM": "Created By", "MDF_DT": "Updated Date & Time",
            "MDF_BY_NM": "Updated By"}
        self.column_type = {
            "SC_SPR": "status", "TYP_PRTY": "str", "NM_SPR": "str", "CD_SPR": "str", "NM_LGL": "str",
            "NM_TRD": "str", "PH_CMPL": "str",
            "EM_ADS": "str",
            "CRT_DT": "Datetime", "CRT_BY_NM": "str", "MDF_DT": "Datetime", "MDF_BY_NM": "str"}

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['columns'] = self.columns
        response.data['column_type'] = self.column_type
        return response

    def vendor_export_data(self, response, device_id, device_flag, current_user, file_name, bsn_unit_id, file_type):
        '''Export vendor data'''
        if len(response[0]) > 0:
            notification_data = {"device_id": device_id, "message_title": vendor_export_messages, "message_body": "Vendor Export Successfully Done",
                                 "notification_type": vendor_export_messages, "event_id": None, "user_id": current_user.id, "file_name": file_name, "export_flag": True}
            location = 'export_files/'+str(file_name)
            if device_id is None or device_id == '':
                device_flag = False
            if len(response[0]) > 1000:
                supplier_export.delay(
                    response, self.columns, bsn_unit_id, file_name, location, notification_data, device_flag, file_type)
                message = {
                    "message": "Export processing in background. You will get a file URL on Email as well as Notification."}
                stat = status.HTTP_200_OK
            else:
                supplier_export(response, self.columns, bsn_unit_id,
                                file_name, location, notification_data, device_flag, file_type)
                message = {"file_name": file_name}
                stat = status.HTTP_200_OK
        else:
            message = {}
            message['error'] = {"message": 'No Data Found'}
            stat = status.HTTP_404_NOT_FOUND
        return message, stat

    @ swagger_auto_schema(tags=['Supplier'], operation_description="Get all Supplier",
                          operation_summary="Get Supplier")
    def get(self, request, *args, **kwargs):
        ''' Supplier List '''
        logger.info("Manufacturer Get Request Data : %s", request.GET)
        supplier_id = request.GET.get('ID_SPR')
        search = request.GET.get('search', '')
        page_size = request.GET.get('page_size', Supplier.objects.count())
        page = request.GET.get('page', 1)
        excludes_ids = request.GET.get('excludes_ids', None)
        export_flag = request.GET.get('export_flag', 0)
        bsn_unit_id = request.GET.get('ID_BSN_UN', 0)
        device_id = request.GET.get('device_id', None)
        file_type = request.GET.get('type', 'xlsx')
        logger.info("Supplier Id : %s", supplier_id)
        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('page', None)
        copy_request_data.pop('search', None)
        copy_request_data.pop('ID_SPR', None)
        copy_request_data.pop('excludes_ids', None)
        copy_request_data.pop('export_flag', None)
        copy_request_data.pop('ID_BSN_UN', None)
        copy_request_data.pop('device_id', None)
        copy_request_data.pop('type', None)
        if export_flag == '1':
            logger.info(vendor_export_messages)
            device_flag = True
            current_user = request.user
            file_name = 'Vendor_Export_Data' + \
                str(time.time())+'.'+str(file_type).lower()
            response = supplier_filter(
                'supplier', int(page), int(page_size), search, copy_request_data, request.GET.get('ordering'), excludes_ids)
            message, stat = self.vendor_export_data(
                response, device_id, device_flag, current_user, file_name, bsn_unit_id, file_type)
            return Response(message, status=stat)
        if (len(copy_request_data) > 0 and supplier_id is None) or (len(search) > 0 or request.GET.get('ordering') is not None):
            response = supplier_filter(
                'supplier', int(page), int(page_size), search, copy_request_data, request.GET.get('ordering'), excludes_ids)
            response = {
                "total": response[1],
                "page": int(page),
                "page_size": int(page_size),
                "results": response[0],
                "columns": self.columns,
                "column_type": self.column_type
            }
            return Response(response, status=status.HTTP_200_OK)
        elif supplier_id is None:
            logger.info("Supplier ID None")
            return self.list(request, *args, **kwargs)
        else:
            logger.info("Supplier ID  Not None")
            queryset = Supplier.objects.get(ID_SPR=supplier_id)
            response_data = SupplierRetrieveSerializer(queryset)
            return Response(response_data.data)


class SupplierUpdateViews(GenericAPIView):
    ''' Supplier Update Views Class '''
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierDataSerializer
    lookup_url_kwarg = "ID_SPR"

    def get_queryset(self):
        supplier = self.kwargs.get(self.lookup_url_kwarg)
        query = Supplier.objects.filter(
            ID_SPR=supplier)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj

    @swagger_auto_schema(tags=['Supplier'], operation_description="Supplier Update",
                         operation_summary="Supplier Update")
    def put(self, request, *args, **kwargs):
        ''' Update Supplier '''
        try:
            response = {}
            data = request.data
            logger.info("Request Data : %s", data)
            supplier_id = self.kwargs.get(self.lookup_url_kwarg)
            party_type_code = data['TYP_PRTY']
            contact_details = data.get('contact_details', [])
            if request.data.get('CD_SPR') is not None:
                if Supplier.objects.filter(CD_SPR=request.data.get('CD_SPR')).exclude(ID_SPR=supplier_id).exists():
                    message = f"Vendor Code does exist.Please try with other code!!"
                    response["message"] = message
                    return Response(response, status=status.HTTP_400_BAD_REQUEST)
            else:
                message = f"Please enter Vendor Code!"
                response["message"] = message
                return Response(response, status=status.HTTP_400_BAD_REQUEST)
            supplier_obj = Supplier.objects.get(ID_SPR=supplier_id)
            Supplier.objects.filter(ID_SPR=supplier_id).update(
                SC_SPR=data.get('SC_SPR'), CD_SPR=data.get('CD_SPR'), MDF_BY=request.user)
            vendor_obj = supplier_obj.ID_VN
            logger.info("vendor Object : %s", vendor_obj)
            party_obj = vendor_obj.ID_PRTY_RO_ASGMT.ID_PRTY
            if party_type_code == 'PR':
                person_data = {
                    "ID_PRTY": party_obj.ID_PRTY,
                    "FN_PRS": data["FN_PRS"],
                    "MD_PRS": data["MD_PRS"],
                    "LN_PRS": data["LN_PRS"],
                    "TY_GND_PRS": data["TY_GND_PRS"],
                    "DC_PRS_BRT": data["DC_PRS_BRT"]
                }
                person_obj = Person.objects.get(ID_PRTY=party_obj)
                personserializer = PersonSerializer(
                    instance=person_obj, data=person_data)
                if personserializer.is_valid(raise_exception=True):
                    personserializer.save()
                    person_save_data = personserializer.data
                    logger.info("Person datas : %s", person_save_data)
            else:
                org_data = {
                    "ID_PRTY": party_obj.ID_PRTY,
                    "ID_LGL_STS": data["ID_LGL_STS"],
                    "NM_LGL": data["NM_LGL"],
                    "NM_TRD": data["NM_TRD"],
                    "ID_DUNS_NBR": data['ID_DUNS_NBR'],
                    "DC_FSC_YR_END": data['DC_FSC_YR_END'],
                    "CD_LGL_ORGN_TYP": data["CD_LGL_ORGN_TYP"]
                }
                org_obj = Organization.objects.get(ID_PRTY=party_obj)
                orgserializer = OrganizationSerializer(
                    instance=org_obj, data=org_data)
                if orgserializer.is_valid(raise_exception=True):
                    orgserializer.save()
                    org_save_data = orgserializer.data
                    logger.info("Organization datas : %s", org_save_data)
            Vendor.objects.filter(ID_VN=vendor_obj.ID_VN).update(
                URL_PGPH_VN=data['URL_PGPH_VN'])

            contact_id_list = PartyContactMethod.objects.filter(
                ID_PRTY_RO_ASGMT=vendor_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT).values_list('ID_PRTY_CNCT_MTH', flat=True)[::1]

            logger.info("Contact ID List : %s", contact_id_list)
            contact_details_delete(contact_id_list, None)
            if contact_details:
                contact = contact_details_create(
                    data, vendor_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT)
                if contact.get('errors'):
                    return Response(contact.get('errors'),
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Supplier Update Successfully"}, status=status.HTTP_200_OK)

        except Exception as exp:
            logger.exception(exp)
            return Response({"error": exp.__class__.__name__}, status=status.HTTP_400_BAD_REQUEST)
