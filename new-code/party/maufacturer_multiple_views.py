from rest_framework.response import Response
import logging
from django.db import transaction
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from product.models.models_item_stock import ItemManufacturer
from party.contact_details import contact_details_delete
from django.core.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from party.models import PartyContactMethod, PartyRoleAssignment

from worker.models import Manufacturer
logger = logging.getLogger(__name__)


class ManufacturerMultipleStatusUpdate(GenericAPIView):
    '''Manufacturer multiple status update and delete'''
    permission_classes = (IsAuthenticated,)

    def validate_ids(self, id_list, id_type):
        ''' validate Manufacturer id '''
        if id_type == 'manufacturer':
            for manufacturer_id in id_list:
                try:
                    Manufacturer.objects.get(
                        ID_MF=manufacturer_id)
                except (Manufacturer.DoesNotExist, ValidationError):
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

    multiple_update_response_schema = {
        "200": openapi.Response(
            description="Status Successfully Updated",
        ),
        "400": openapi.Response(
            description="Bad Request"
        )
    }

    def update_manufacturer_status(self, manufacturer_list, manufacturer_status, invalid_count, request, response):
        '''Update manufacturer status'''
        for manufacture_id in manufacturer_list:
            if ItemManufacturer.objects.filter(ID_MF=manufacture_id).exists() and manufacturer_status == "I":
                invalid_count += 1
            else:
                obj = Manufacturer.objects.get(
                    ID_MF=manufacture_id)
                obj.SC_MF = manufacturer_status
                obj.MDF_BY = request.user
                obj.save()
                response["message"] = "Status Successfully Updated"
        if invalid_count > 0:
            message = str(invalid_count) + \
                " Manufacturer not updated. Already assigned with products."
            response['message'] = message
        return response, invalid_count

    @swagger_auto_schema(tags=['Manufacturer'], operation_description="Manufacturer multiple status update",
                         operation_summary="Manufacturer multiple status update", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Ids',
                                  items=openapi.Items(type=openapi.TYPE_INTEGER, description='Manufacturer Id')),
            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Manufacturer status (A/I)'),
            'contacts': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of contact Ids and status',
                                       properties={
                                           'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Contact Ids',
                                                                 items=openapi.Items(type=openapi.TYPE_INTEGER,
                                                                                     description='Supplier Contacts Ids')),
                                           'status': openapi.Schema(type=openapi.TYPE_STRING,
                                                                    description='Supplier status (A/I)'),
                                       }),
        }, required=['ids']
    ), responses=multiple_update_response_schema)
    def put(self, request):
        '''Manufacturer multiple status update'''
        manufacturer_list = request.data['ids']
        manufacturer_status = request.data['status']
        contact_status = request.data.get('contacts')
        response = {}
        invalid_count = 0
        if contact_status is not None:
            chk_stat = self.validate_ids(
                id_list=contact_status.get('ids'), id_type='contacts')
            if chk_stat:
                for contact_id in contact_status.get('ids'):
                    PartyContactMethod.objects.filter(
                        ID_PRTY_CNCT_MTH=contact_id).update(CD_STS=contact_status.get('status'))
                response['message'] = "Contact Status Successfully Updated"
                return Response(response, status.HTTP_200_OK)
            else:
                response['message'] = "Invalid Contact Id"
                return Response(response, status.HTTP_400_BAD_REQUEST)
        else:
            chk_stat = self.validate_ids(
                id_list=manufacturer_list, id_type='manufacturer')
            if chk_stat:
                response, invalid_count = self.update_manufacturer_status(
                    manufacturer_list, manufacturer_status, invalid_count, request, response)
                return Response(response, status=status.HTTP_200_OK)
            else:
                response["message"] = "Invalid Data"
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

    multiple_delete_response_schema = {
        "200": openapi.Response(
            description="Item Successfully Deleted",
        ),
        "400": openapi.Response(
            description="Bad Request"
        )
    }

    def delete_manufacturer_contact_details(self, contacts, response):
        '''Delete manufacturer contact details'''
        contact_id_list = contacts['ids']
        contact_chk = self.validate_ids(
            contact_id_list, id_type='contacts')
        if contact_chk:
            contact_details_delete(
                contact_id_list, None)
            response['message'] = "Contact Details Deleted Successfully"
        return response

    def delete_manufacturer_all_details(self, manufacture_id, invalid_count, response):
        '''Delete manufacturer all the details'''
        if ItemManufacturer.objects.filter(ID_MF=manufacture_id).exists():
            invalid_count += 1
        else:
            manufacturer_obj = Manufacturer.objects.get(
                ID_MF=manufacture_id)
            party_role_assign_id = manufacturer_obj.ID_VN.ID_PRTY_RO_ASGMT_id
            contact_details_delete(
                None, party_role_assign_id)

            party_role_assign_obj = PartyRoleAssignment.objects.get(
                ID_PRTY_RO_ASGMT=party_role_assign_id)

            if party_role_assign_obj.ID_PRTY is not None:
                party_role_assign_obj.ID_PRTY.delete()
                logger.info("Party delete")

            if manufacturer_obj.ID_VN is not None:
                manufacturer_obj.ID_VN.delete()
                logger.info("Vendor deleted")

            if party_role_assign_obj:
                party_role_assign_obj.delete()
                logger.info(
                    "Party Role Assignment deleted")

            manufacturer_obj.delete()
            logger.info("Manufacturer delete")

            response['message'] = "Manufacturer/s Deleted Successfully"
        return response, invalid_count

    @swagger_auto_schema(tags=['Manufacturer'], operation_description="Manufacturer multiple delete",
                         operation_summary="Manufacturer multiple delete", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Ids', items=openapi.Items(type=openapi.TYPE_STRING, description='Manufacturer id list')),
            'contacts': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of contact Ids ',
                                       properties={
                                           'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Contact Ids', items=openapi.Items(type=openapi.TYPE_INTEGER, description='Contacts Ids')),
                                       }),
        }, required=['ids']
    ))
    def delete(self, request):
        '''Manufacturer multiple delete'''
        manufacturer_id = request.data['ids']
        contacts = request.data.get('contacts', None)
        response = {}
        response_status = None
        invalid_count = 0
        try:
            with transaction.atomic():
                chk_stat = self.validate_ids(manufacturer_id, 'manufacturer')
                if chk_stat:
                    if contacts:
                        response = self.delete_manufacturer_contact_details(
                            contacts, response)
                    else:
                        for manufacture_id in manufacturer_id:
                            response, invalid_count = self.delete_manufacturer_all_details(
                                manufacture_id, invalid_count, response)

                        if invalid_count > 0:
                            message = str(invalid_count) + \
                                " Manufacturer not deleted. Already assigned with products."
                            response['message'] = message
                        return Response(response, status.HTTP_200_OK)
                else:
                    response['message'] = "Invalid Manufacturer Id"
                    return Response(response, status.HTTP_400_BAD_REQUEST)
        except Exception as exp:
            logger.exception(exp)
            response["message"] = "Invalid Data"
            response_status = status.HTTP_400_BAD_REQUEST
        return Response(response, status=response_status)
