''' Supplier Multiple Status Update adn Delete Views '''
import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from product.models.models_item_stock import ItemSupplier
from worker.models import Supplier, Manufacturer
from party.contact_details import contact_details_delete
from .models import (PartyContactMethod, PartyRoleAssignment)


logger = logging.getLogger(__name__)


class SupplierKeyValueCheckView(APIView):
    '''unique supplier code check'''
    permission_classes = [IsAuthenticated]
    item_params = [
        openapi.Parameter("key",
                          openapi.IN_QUERY,
                          description="Supplier Key",
                          type=openapi.TYPE_STRING
                          ),
        openapi.Parameter("value",
                          openapi.IN_QUERY,
                          description="Supplier Key Value",
                          type=openapi.TYPE_STRING
                          ),
        openapi.Parameter("type",
                          openapi.IN_QUERY,
                          description="Vendor Type (Supplier/Manufacturer)",
                          type=openapi.TYPE_STRING
                          )
    ]

    @ swagger_auto_schema(tags=['Supplier'], operation_description="Duplicate Supplier Code Check",
                          operation_summary="Check if supplier code Exists", manual_parameters=item_params)
    def get(self, request, *args, **kwargs):
        '''Supplier code check'''

        key = request.GET.get('key')
        value = request.GET.get('value')
        vendor_type = request.GET.get('type')
        supplier = None

        if key is not None and value is not None:
            if vendor_type.lower() == 'supplier':
                supplier = Supplier.objects.filter(
                    **{f'{key}__iexact': value}).first()
                if supplier is not None:
                    return Response({'result': True})
                else:
                    return Response({'result': False})
            elif vendor_type.lower() == 'manufacturer':
                supplier = Manufacturer.objects.filter(
                    **{f'{key}__iexact': value}).first()
                if supplier is not None:
                    return Response({'result': True})
                else:
                    return Response({'result': False})
        else:
            return Response({'result': 'Key Value Input Error'})


class SupplierMultipleStatusUpdate(APIView):
    '''Supplier multiple status updates '''
    permission_classes = (IsAuthenticated,)

    def validate_ids(self, id_list, id_type):
        '''validate Supplier id'''
        if id_type == 'supplier':
            for supplier_id in id_list:
                try:
                    Supplier.objects.get(ID_SPR=supplier_id)
                except (Supplier.DoesNotExist, ValidationError):
                    return False
            return True
        elif id_type == 'contacts':
            for contact_id in id_list:
                try:
                    PartyContactMethod.objects.get(
                        ID_PRTY_CNCT_MTH=contact_id)
                except (PartyContactMethod.DoesNotExist, ValidationError):
                    return False
            return True

    def update_vendor_contact_details_status(self, chk_stat, contact_status, response):
        '''Update vendor contact details status'''
        if chk_stat:
            for contact_id in contact_status.get('ids'):
                PartyContactMethod.objects.filter(
                    ID_PRTY_CNCT_MTH=contact_id).update(CD_STS=contact_status.get('status'))
            response['message'] = "Contact Status Successfully Updated"
            stat = status.HTTP_200_OK
        else:
            response['message'] = "Invalid Contact Id"
            stat = status.HTTP_400_BAD_REQUEST
        return response, stat

    def update_vendor_status(self, supplier_id, supplier_status, invalid_count, request, response):
        '''Update Vendor status'''
        for sup_id in supplier_id:
            if ItemSupplier.objects.filter(ID_SPR=sup_id).exists() and supplier_status == 'I':
                invalid_count += 1
            else:
                obj = Supplier.objects.get(ID_SPR=sup_id)
                obj.SC_SPR = supplier_status
                obj.MDF_BY = request.user
                obj.save()
                response['message'] = "Status Successfully Updated"
        if invalid_count > 0:
            message = str(invalid_count) + \
                " Supplier not updated. Already assigned with products."
            response['message'] = message
        return response

    multiple_update_response_schema = {
        "200": openapi.Response(
            description="Status Successfully Updated",
        ),
        "400": openapi.Response(
            description="Bad Request"
        )
    }

    @ swagger_auto_schema(tags=['Supplier'], operation_description="Supplier multiple status update",
                          operation_summary="Supplier multiple status update",
                          request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Ids',
                                  items=openapi.Items(type=openapi.TYPE_INTEGER,
                                                      description='Supplier Id')),
            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Supplier status (A/I)'),
            'contacts': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of contact Ids and status',
                                       properties={
                                           'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Contact Ids',
                                                                 items=openapi.Items(type=openapi.TYPE_INTEGER,
                                                                                     description='Supplier Contacts Ids')),
                                           'status': openapi.Schema(type=openapi.TYPE_STRING,
                                                                    description='Supplier status (A/I)'),
                                       }),
        }, required=['ids', 'status']
    ), responses=multiple_update_response_schema)
    def put(self, request):
        '''Supplier multiple status update'''
        supplier_id = request.data['ids']
        supplier_status = request.data['status']
        contact_status = request.data.get('contacts')
        invalid_count = 0
        if contact_status is not None:
            chk_stat = self.validate_ids(
                id_list=contact_status.get('ids'), id_type='contacts')
            response = {}
            response, stat = self.update_vendor_contact_details_status(
                chk_stat, contact_status, response)
            return Response(response, status=stat)
        else:
            chk_stat = self.validate_ids(
                id_list=supplier_id, id_type='supplier')
            response = {}
            if chk_stat:
                response = self.update_vendor_status(
                    supplier_id, supplier_status, invalid_count, request, response)
                return Response(response, status.HTTP_200_OK)
            else:
                response['message'] = "Invalid Supplier Id"
                return Response(response, status.HTTP_400_BAD_REQUEST)

    multiple_update_response_schema = {
        "200": openapi.Response(
            description="Supplier Successfully Deleted",
        ),
        "400": openapi.Response(
            description="Bad Request"
        )
    }

    def delete_vendor_contact_details(self, contact_chk, contact_id_list):
        '''Delete vendor contact details'''
        if contact_chk:
            contact_details_delete(
                contact_id_list, None)

    def delete_vendor(self, sup_id, invalid_count):
        '''Delete Vendor'''
        if ItemSupplier.objects.filter(ID_SPR=sup_id).exists():
            message = ""
            invalid_count += 1
        else:
            supplier_obj = Supplier.objects.get(
                ID_SPR=sup_id)
            party_role_assign_id = supplier_obj.ID_VN.ID_PRTY_RO_ASGMT_id
            contact_details_delete(
                None, party_role_assign_id)

            party_role_assign_obj = PartyRoleAssignment.objects.get(
                ID_PRTY_RO_ASGMT=party_role_assign_id)

            if party_role_assign_obj.ID_PRTY is not None:
                party_role_assign_obj.ID_PRTY.delete()
                logger.info("Party delete")

            if supplier_obj.ID_VN is not None:
                supplier_obj.ID_VN.delete()
                logger.info("Vendor deleted")

            if party_role_assign_obj:
                party_role_assign_obj.delete()
                logger.info(
                    "Party Role Assignment deleted")

            supplier_obj.delete()
            logger.info("Vendor delete")
            message = "Vendor/s Deleted Successfully"
        return message, invalid_count

    @ swagger_auto_schema(tags=['Supplier'], operation_description="Supplier multiple delete",
                          operation_summary="Supplier Multiple Delete",
                          request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Ids',
                                  items=openapi.Items(type=openapi.TYPE_INTEGER,
                                                      description='Supplier Id')),
            'contacts': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of contact Ids ',
                                       properties={
                                           'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Contact Ids',
                                                                 items=openapi.Items(type=openapi.TYPE_INTEGER,
                                                                                     description='Contacts Ids')),
                                       }),
        }, required=['ids']
    ), responses=multiple_update_response_schema)
    def delete(self, request):
        supplier_id = request.data['ids']
        contacts = request.data.get('contacts', None)
        response = {}
        invalid_count = 0
        response_status = None
        try:
            with transaction.atomic():
                chk_stat = self.validate_ids(supplier_id, 'supplier')
                if chk_stat:
                    if contacts:
                        contact_id_list = contacts['ids']
                        contact_chk = self.validate_ids(
                            contact_id_list, id_type='contacts')
                        self.delete_vendor_contact_details(
                            contact_chk, contact_id_list)
                        message = "Contact Details Deleted Successfully"
                        response['message'] = message

                    else:
                        for sup_id in supplier_id:
                            message, invalid_count = self.delete_vendor(
                                sup_id, invalid_count)
                        if invalid_count > 0:
                            message = str(invalid_count) + \
                                " Vendor not deleted. Already assigned with products."
                        response['message'] = message
                        return Response(response, status.HTTP_200_OK)
                else:
                    response['message'] = "Invalid Vendor Id"
                    return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as exp:
            logger.exception(exp)
            response["message"] = "Invalid Data"
            response_status = status.HTTP_400_BAD_REQUEST
        return Response(response, status=response_status)
