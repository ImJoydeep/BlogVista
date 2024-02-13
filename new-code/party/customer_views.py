import logging
import time
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
from rest_framework import mixins
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from party.supplier_filter import supplier_filter
from party.contact_details import (
    contact_details_create, contact_details_delete, manufacturer_export)
from party.models import (PartyContactMethod, PartyType,
                          PartyRole, Person)
from party.serializers import (
    PartySerializer, PartyRoleAssignmentSerializer,
    PersonSerializer, OrganizationSerializer)
from party.manufacturer_serializers import (
    ManufacturerSerializer, ManufacturerListSerializer,
    ManufacturerDataSerializer, ManufacturerRetrieveSerializer)
from party.contact_details_schema import get_contact_details_schema
from party.manufacturer_views import (raise_exception_on_party_serializer,
                                      raise_exception_on_party_role_asgmt_serializer, create_person_or_organization,
                                      raise_exception_on_contact_details)
from party.customer_serializers import (
    CustomerSerializer, CustomerListSerializer, CustomerRetrieveSerializer, CustomerStatusSerializer)
from order.models import Customer,OrderMaster
from party.customer_filter import customer_filter
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)

customer_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'CUST_FNM': openapi.Schema(type=openapi.TYPE_STRING, description='Customer First Name (Mandetory)'),
        'CUST_LNM': openapi.Schema(type=openapi.TYPE_STRING, description='Customer Last Name (Mandetory) '),
        'TY_GND_PRS': openapi.Schema(type=openapi.TYPE_STRING, description='Customer Gender (Male/Female/Others) '),
        'DC_PRS_BRT': openapi.Schema(type=openapi.TYPE_STRING, description='Customer DOB ("YYYY-MM-DD")'),
        'CUST_EMAIL': openapi.Schema(type=openapi.TYPE_STRING, description='Customer Email ID'),
        'CUST_PH': openapi.Schema(type=openapi.TYPE_STRING, description='Customer Phone Number'),
        'CUST_ST': openapi.Schema(type=openapi.TYPE_STRING, description='Customer Stataus (A/I)'),
        'contact_details': get_contact_details_schema(),

    }, required=['TYP_PRTY'])


def insert_data_into_customer(party_role_asign_save, party_instance, datas, request, created_by, body_datas):
    '''Creation of a new manufacturer'''
    
    customer_data = {
        "CUST_FNM": request.data.get('CUST_FNM'),
        "CUST_LNM": request.data.get('CUST_LNM'),
        "CUST_EMAIL": request.data.get('CUST_EMAIL'),
        "CUST_PH": request.data.get('CUST_PH'),
        # "SC_CT": request.data.get('SC_CT'),
        "ID_PRTY_RO_ASGMT": party_role_asign_save.ID_PRTY_RO_ASGMT,
        "ID_PRTY": party_instance,
        "CRT_BY": created_by,
        "URL_PGPH_CT": datas.get('URL_PGPH_CT', None),
    }
    if Customer.objects.filter(CUST_EMAIL__iexact=request.data.get('CUST_EMAIL')).exists():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Email already Exists!"})
    if Customer.objects.filter(CUST_PH__iexact=request.data.get('CUST_PH')).exists():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Phone Number already Exists!"})
    customer_serializer = CustomerSerializer(
        data=customer_data)
    if not customer_serializer.is_valid():
        transaction.set_rollback(True)
        raise serializers.ValidationError(
            {"message": "Invalid Data!"})

    customer_serializer.save()
    customer_save_data = customer_serializer.data
    body_datas.update(customer_save_data)
    return body_datas


class CustomerCreateViews(CreateModelMixin,ListModelMixin, GenericAPIView):
    ''' Customer Create Views Class '''
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return CustomerListSerializer
        return PartySerializer

    queryset = Customer.objects.all()
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['CUST_EMAIL', 'CUST_PH', 'CUST_FNM', 'CUST_LNM']
    filterset_fields = ['id']
    ordering = ['-id']
    ordering_fields = '__all__'

    @ swagger_auto_schema(tags=['Customer'], operation_description="Get all Customer",
                          operation_summary="Get Customer")
    def get(self, request, *args, **kwargs):
        ''' Customer List '''
        logger.info("Customer Get Request Data : %s", request.GET)
        customer_id = self.request.GET.get('id')
        if customer_id is None:
            logger.info("Customer ID None")
            return self.list(request, *args, **kwargs)
        else:
            logger.info("Customer ID is Not None")
            queryset = Customer.objects.get(id=customer_id)
            response_data = CustomerRetrieveSerializer(queryset)
            return Response(response_data.data)

    @ swagger_auto_schema(tags=['Customer'], operation_description="Create Customer",
                          operation_summary="Create Customer", request_body=customer_schema)
    def post(self, request, import_data=None):
        ''' Create Customer Party '''
        created_by = None
        try:
            if import_data is not None:
                datas = import_data.data
                current_user_id = datas.get('user')
                created_by = current_user_id
            else:
                datas = request.data
                current_user_id = request.user
                created_by = current_user_id.id
            logger.info("Created By : %s", created_by)
            logger.info("Request Data : %s", datas)
            with transaction.atomic():
                party_type_code = 'PR'
                party_type = PartyType.objects.get(CD_PRTY_TYP=party_type_code)
                logger.info("Party Type : %s, Party Type ID : %s",
                            party_type, party_type.ID_PRTY_TYP)

                party_insert_data = {
                    "ID_PRTY_TYP": party_type.ID_PRTY_TYP,
                    "BY_CRT_PRTY": created_by,
                }
                party_serializer = PartySerializer(data=party_insert_data)
                raise_exception_on_party_serializer(party_serializer)
                save_datas = party_serializer.save()
                body_datas = party_serializer.data

                if save_datas.ID_PRTY:
                    party_role = PartyRole.objects.get(TY_RO_PRTY="CUST")
                    party_role_ids = party_role.ID_RO_PRTY
                    logger.info("Party Role : %s", party_role_ids)
                    party_role_asgmt_data = {
                        "ID_PRTY": save_datas.ID_PRTY,
                        "ID_RO_PRTY": party_role_ids
                    }
                    party_role_asgmt_serializer = PartyRoleAssignmentSerializer(
                        data=party_role_asgmt_data
                    )
                    raise_exception_on_party_role_asgmt_serializer(
                        party_role_asgmt_serializer)

                    party_role_asign_save = party_role_asgmt_serializer.save()
                    body_datas.update(party_role_asgmt_serializer.data)
                    body_datas = create_person_or_organization(
                        party_type_code, save_datas, datas, body_datas, created_by)

                    if party_role_asign_save.ID_PRTY_RO_ASGMT:
                        body_datas = insert_data_into_customer(
                            party_role_asign_save, save_datas.ID_PRTY, datas, request, created_by, body_datas)

                        contact_details = datas.get('contact_details', None)
                        logger.info("Contact Details : %s", contact_details)
                        if contact_details is not None:
                            contact = contact_details_create(
                                datas, party_role_asign_save.ID_PRTY_RO_ASGMT)
                            raise_exception_on_contact_details(contact)
                        body_datas['contact_details'] = datas.get('contact_details', None)
                        body_datas['message'] = "Customer Created Successfully"
                return Response(body_datas, status=status.HTTP_200_OK)
        except Exception as excep:
            logger.exception("Customer Create Exception : %s", excep)
            return Response(excep.args[0],
                            status=status.HTTP_400_BAD_REQUEST)


class CustomerListViews(GenericAPIView, ListModelMixin):
    '''Customer List View Class '''
    permission_classes = [IsAuthenticated]
    queryset = Customer.objects.all()
    serializer_class = CustomerListSerializer
    filter_backends = [DjangoFilterBackend,filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['id']
    search_fields = ['CUST_EMAIL', 'CUST_PH', 'CUST_FNM', 'CUST_LNM']
    ordering_fields = '__all__'
    ordering = ['-id']

    def __init__(self):
        self.columns = {
            "CUST_ST": "Status", "CUST_NM": "Customer Name",
            "CUST_PH": "Mobile Number", "CUST_EMAIL": "Email Address",
            "CRT_DT": "Created Date & Time", "CRT_BY": "Created By", "UPDT_DT": "Updated Date & Time", "UPDT_BY": "Updated By","TL_OD":"Total Orders","TL_OD_AMT":"Total Orders Amount",
            "LT_OD_AMT":"Last Order Amount","LT_OD_DATE":"Last Order Date"}
        self.column_type = {
            "CUST_ST": "status",  "CUST_NM": "str", "CUST_PH": "str", "CUST_EMAIL": "str",
            "CRT_DT": "Datetime","CRT_BY": "str", "UPDT_DT": "Datetime", "UPDT_BY": "str","TL_OD":"str","TL_OD_AMT":"price",
            "LT_OD_AMT":"price","LT_OD_DATE":"Datetime"}
    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        return response

    @ swagger_auto_schema(tags=['Customer'], operation_description="Get all Customer",
                          operation_summary="Get Customer")
    def get(self, request, *args, **kwargs):
        ''' Customer List '''
        logger.info("Customer Get Request Data : %s", request.GET)
        search = request.GET.get('search', '')
        customer_id = self.request.GET.get('id')
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', Customer.objects.count())
        logger.info("Customer Id : %s", customer_id)
        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('search', None)
        copy_request_data.pop('id', None)
        copy_request_data.pop('page', None)
        
        if (len(copy_request_data) > 0 and customer_id is None) or (len(search) > 0 or request.GET.get('ordering') is not None):
            response = customer_filter(int(page), int(
                page_size), search, copy_request_data, request.GET.get('ordering'))
            response = {
                "total": response[1],
                "page": int(page),
                "results": response[0],
                "page_size": int(page_size),
                "columns": self.columns,
                "column_type": self.column_type
            }
            return Response(response, status=status.HTTP_200_OK)

        if customer_id is None:
            logger.info("Customer ID None")
            result = self.list(request, *args, **kwargs).data
            result["page"] = int(page)
            result["page_size"] = int(page_size)
            result['columns'] = self.columns
            result['column_type'] = self.column_type
            return Response(result)
        else:
            logger.info("Customer ID Not None")
            queryset = Customer.objects.get(id=customer_id)
            response_data = CustomerRetrieveSerializer(queryset)
            return Response(response_data.data)


class CustomerUpdateViews(GenericAPIView):
    ''' Customer Update Views Class '''
    permission_classes = (IsAuthenticated,)
    serializer_class = ManufacturerDataSerializer

    def get_queryset(self):
        customer_id = self.kwargs.get('pk')
        query = Customer.objects.filter(
            id=customer_id)
        return query
    

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj

    @ swagger_auto_schema(tags=['Customer'], operation_description="Customer Update",
                          operation_summary="Customer Update")
    def put(self, request, *args, **kwargs):
        ''' Update Customer '''
        if Customer.objects.filter(CUST_EMAIL=request.data.get('CUST_EMAIL')).exclude(id=self.kwargs.get('pk')).exists():
            return Response({"message": "Email already Exists!"},status=status.HTTP_400_BAD_REQUEST)
        
        if Customer.objects.filter(CUST_PH=request.data.get('CUST_PH')).exclude(id=self.kwargs.get('pk')).exists():
            return Response({"message": "Phone Number already Exists!"},status=status.HTTP_400_BAD_REQUEST)
        try:
            response = {}
            requested_data = request.data
            logger.info("Customer Update Request Data : %s", requested_data)
            customer_id = self.kwargs.get('pk')
            current_user = request.user
            contact_details = requested_data.get('contact_details', [])
            customer_obj = Customer.objects.get(id=customer_id)
            Customer.objects.filter(id=customer_id).update(
                CUST_FNM=requested_data.get('CUST_FNM'), 
                CUST_LNM=requested_data.get('CUST_LNM'), 
                CUST_EMAIL=requested_data.get('CUST_EMAIL'),
                CUST_PH=requested_data.get('CUST_PH'),
                CUST_ST=requested_data.get('CUST_ST'),
                UPDT_BY=current_user)

            party_object = customer_obj.ID_PRTY

            person_data = {
                    "FN_PRS": requested_data["CUST_FNM"],
                    "LN_PRS": requested_data["CUST_LNM"],
                    "DC_PRS_BRT": requested_data["DC_PRS_BRT"],
                    "ID_PRTY": party_object.ID_PRTY,
                    "TY_GND_PRS": requested_data["TY_GND_PRS"],
                }
            person_object = Person.objects.get(ID_PRTY=party_object)
            person_serializer = PersonSerializer(instance=person_object, data=person_data)
            if person_serializer.is_valid(raise_exception=True):
                person_serializer.save()
                person_save_data = person_serializer.data
                logger.info("Person data : %s", person_save_data)

            contact_id_lists = PartyContactMethod.objects.filter(
                ID_PRTY_RO_ASGMT=customer_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT).values_list('ID_PRTY_CNCT_MTH', flat=True)[::1]

            logger.info("Contact ID List : %s", contact_id_lists)
            contact_details_delete(contact_id_lists, None)
            if contact_details:
                contacts = contact_details_create(
                    requested_data, customer_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT)
                if contacts.get('errors'):
                    return Response(contacts.get('errors'),
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Customer Updated Successfully"}, status=status.HTTP_200_OK)

        except Exception as excep:
            logger.exception(excep)
            return Response({"message": excep.args[0]}, status=status.HTTP_400_BAD_REQUEST)

class CustomerStatusUpdate(GenericAPIView, mixins.UpdateModelMixin):
    '''Customer status update'''

    def validate_ids(self, id_list):
        '''Customer validate id'''
        for each_id in id_list:
            try:
                Customer.objects.get(id=each_id)
            except (Customer.DoesNotExist, ValidationError):
                return False
        return True

    def put(self, request, *args, **kwargs):
        '''Customer multiple status update'''
        id_list = request.data['ids']
        status_val = request.data['status']
        current_user = request.user
        chk_stat = self.validate_ids(id_list=id_list)
        if chk_stat:
            instances = []
            for each_id in id_list:
                obj = Customer.objects.get(id=each_id)
                obj.CUST_ST = status_val
                obj.UPDT_BY = current_user
                obj.save()
                instances.append(obj)
            serializer = CustomerStatusSerializer(instances, many=True)
            return Response(serializer.data, *args, **kwargs)
        else:
            response_data = {}
            response_data["message"] = "invalid Id"
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class CustomerDeleteAPIView(GenericAPIView, mixins.DestroyModelMixin):
    
    def validate_ids(self, id):
        '''Customer validate id'''
        for each_id in id:
            try:
                Customer.objects.get(id=each_id)
            except (Customer.DoesNotExist, ValidationError):
                return False
        return True
    
    def delete(self, request):
        '''Customer delete'''
        cust_id = request.data['ids']
        chk_stat = self.validate_ids(id=cust_id)
        if chk_stat:
            for each_id in cust_id:
                customer_obj = Customer.objects.get(id=each_id)
                contact_id_lists = []
                if customer_obj.ID_PRTY_RO_ASGMT:
                    contact_id_lists = PartyContactMethod.objects.filter(
                    ID_PRTY_RO_ASGMT=customer_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT).values_list('ID_PRTY_CNCT_MTH', flat=True)[::1]
                contact_details_delete(contact_id_lists, None)
                Customer.objects.filter(id=each_id).delete()
            return Response({"message": "Customer Deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            response_data = {}
            response_data["message"] = "Invalid Id"
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
