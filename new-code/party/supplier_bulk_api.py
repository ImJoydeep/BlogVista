from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging
import pandas as pd
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from copy import deepcopy
from party.manufacturer_views import ManufacturerCreateViews, ManufacturerUpdateViews
from party.models import ITUCountry, PartyType, State
from worker.models import Supplier, Manufacturer
from party.supplier_views import SupplierCreateViews, SupplierUpdateViews

logger = logging.getLogger(__name__)

contact_details_swagger = openapi.Schema(
    type=openapi.TYPE_ARRAY, description='Array of Suppliers contacts details',
    items=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'A1_ADS': openapi.Schema(type=openapi.TYPE_STRING, description='Addres 1'),
            'A2_ADS': openapi.Schema(type=openapi.TYPE_STRING, description='Address 2'),
            'CD_CY_ITU': openapi.Schema(type=openapi.TYPE_STRING, description='Country Code'),
            'CD_PSTL': openapi.Schema(type=openapi.TYPE_STRING, description='Zip Code'),
            'CD_STS': openapi.Schema(type=openapi.TYPE_STRING, description='Status (A)'),
            'CI_CNCT': openapi.Schema(type=openapi.TYPE_STRING, description='City'),
            'EM_ADS': openapi.Schema(type=openapi.TYPE_STRING, description='Email Address'),
            'ST_CNCT': openapi.Schema(type=openapi.TYPE_STRING, description='State Code'),
            'PH_CMPL': openapi.Schema(type=openapi.TYPE_STRING, description='Phone Number')
        }
    )
)


def create_data_for_postal_code_and_phone(cont_id):
    '''Create data for postal code and phone number'''
    if cont_id.get('PH_CMPL'):
        if str(cont_id['PH_CMPL']).startswith('+1 '):
            if str(cont_id['PH_CMPL']).find('-') != -1:
                logger.info(
                    "Phone number provided which is separated by dash")
            else:
                country_code = '+1'
                temp_value = str(cont_id['PH_CMPL'])[3:]
                first_three_digit = str(temp_value)[:3]
                middle_three_digit = str(temp_value)[3:6]
                last_four_digit = str(temp_value)[6:]
                final_number = country_code+' '+first_three_digit + \
                    '-'+middle_three_digit+'-'+last_four_digit
                cont_id['PH_CMPL'] = final_number
        elif len(str(cont_id['PH_CMPL'])) <= 10:
            country_code = '+1'
            first_three_digit = str(cont_id['PH_CMPL'])[:3]
            middle_three_digit = str(cont_id['PH_CMPL'])[3:6]
            last_four_digit = str(cont_id['PH_CMPL'])[6:]
            final_number = country_code+' '+first_three_digit + \
                '-'+middle_three_digit+'-'+last_four_digit
            cont_id['PH_CMPL'] = final_number
        elif len(str(cont_id['PH_CMPL'])) > 10:
            country_code = '+1 '
            final_number = country_code+cont_id['PH_CMPL']
            cont_id['PH_CMPL'] = final_number
    return cont_id


def validate_contact_details(spl_data, copy_supplier_data, index, contact_index, error_supplier_list, index_list, flag):
    '''Validate contact details'''
    for cont_id in spl_data.get('contact_details', []):
        contact_index += 1
        if cont_id.get('CD_CY_ITU'):
            if str(cont_id.get('CD_CY_ITU')).lower() == 'us':
                country_instance = ITUCountry.objects.get(
                    NM_CY_ITU='United States Of America')
                cont_id['CD_CY_ITU'] = country_instance.CD_CY_ITU
            else:
                copy_supplier_data[index]['contact_details'][contact_index]['remark'] = "Provide valid Country code."
                index_list.append(contact_index)
                flag = True
                continue
        if cont_id.get('ST_CNCT'):
            if State.objects.filter(CD_ST__iexact=cont_id.get('ST_CNCT')):
                state_instance = State.objects.filter(
                    CD_ST__iexact=cont_id.get('ST_CNCT')).first()
                cont_id['ID_ST'] = state_instance.ID_ST
                cont_id.pop('ST_CNCT')
            else:
                copy_supplier_data[index]['contact_details'][contact_index]['remark'] = "Provide valid state code."
                index_list.append(contact_index)
                flag = True
                continue
        else:
            cont_id['ID_ST'] = None
        cont_id = create_data_for_postal_code_and_phone(cont_id)
        cont_id['CD_TYP_CNCT_PRPS'] = None
        cont_id['CD_TYP_CNCT_MTH'] = None
        cont_id['CD_STS'] = "A"
    return index_list, error_supplier_list, spl_data, flag


class SupplierBulkAPIView(GenericAPIView):
    '''Supplier Bulk API'''
    permission_classes = (IsAuthenticated,)

    def insert_update_into_supplier(self, spl_data, temp_request, request):
        '''Insert or update a supplier'''
        supplier_obj = Supplier.objects.filter(
            CD_SPR__iexact=spl_data.get('CD_SPR'))
        if supplier_obj.exists():
            supplier_instance = supplier_obj.first()
            new_obj = pd.DataFrame(temp_request)
            supplier_update_obj = SupplierUpdateViews()
            supplier_update_obj.kwargs = {}
            supplier_update_obj.kwargs['ID_SPR'] = supplier_instance.ID_SPR
            new_obj.user = request.user
            supplier_update_obj.put(new_obj, new_obj)
        else:
            temp_request['data']['user'] = request.user.id
            new_obj = pd.DataFrame(temp_request)
            SupplierCreateViews.post(
                SupplierCreateViews, new_obj, new_obj)

    def validation_for_supplier(self, supplier_data, index, copy_supplier_data, error_supplier_list, request):
        '''Validation function for supplier'''
        for spl_data in supplier_data:
            index_list = []
            index += 1
            contact_index = -1
            flag = False
            if not PartyType.objects.filter(CD_PRTY_TYP=spl_data.get('TYP_PRTY')).exists():
                copy_supplier_data[index]['remark'] = "Provide valid party type."
                error_supplier_list.append(copy_supplier_data[index])
                continue
            if not spl_data.get('CD_SPR'):
                copy_supplier_data[index]['remark'] = "Provide valid Supplier Code."
                error_supplier_list.append(copy_supplier_data[index])
                continue
            if not spl_data.get('NM_TRD'):
                copy_supplier_data[index]['remark'] = "Trade Name cannot be blank."
                error_supplier_list.append(copy_supplier_data[index])
                continue
            index_list, error_supplier_list, spl_data, flag = validate_contact_details(
                spl_data, copy_supplier_data, index, contact_index, error_supplier_list, index_list, flag)
            logger.info({"CD_SPR": spl_data.get('CD_SPR'), "flag": flag})
            if flag:
                error_supplier_list.append(
                    copy_supplier_data[index])
            for j in index_list[::-1]:
                spl_data.get('contact_details').pop(j)
            spl_data['ID_LGL_STS'] = None
            spl_data['ID_DUNS_NBR'] = None
            spl_data['DC_FSC_YR_END'] = None
            spl_data['CD_LGL_ORGN_TYP'] = None
            spl_data['URL_PGPH_VN'] = None
            spl_data['SC_SPR'] = "A"
            temp_request = {}
            temp_request['data'] = spl_data
            self.insert_update_into_supplier(
                spl_data, temp_request, request)
        return error_supplier_list

    @swagger_auto_schema(tags=['Supplier'], operation_description="Supplier Bulk API", operation_summary="Supplier Bulk API", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'suppliers': openapi.Schema(
                type=openapi.TYPE_ARRAY, description='Array of Suppliers',
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'TYP_PRTY': openapi.Schema(type=openapi.TYPE_STRING, description='Supplier Type (OR)'),
                        'CD_SPR': openapi.Schema(type=openapi.TYPE_STRING, description='Supplier Code'),
                        'NM_LGL': openapi.Schema(type=openapi.TYPE_STRING, description='Supplier Legal Name'),
                        'NM_TRD': openapi.Schema(type=openapi.TYPE_STRING, description='Supplier Trade Name'),
                        'contact_details': contact_details_swagger
                    }
                )
            )
        }
    ))
    def post(self, request, *args, **kwargs):
        '''Create a Supplier Bulk API'''
        response = {}
        supplier_data = request.data.get('suppliers', [])
        error_supplier_list = []
        copy_supplier_data = deepcopy(supplier_data)
        if supplier_data:
            index = -1
            error_supplier_list = self.validation_for_supplier(
                supplier_data, index, copy_supplier_data, error_supplier_list, request)
        if error_supplier_list:
            response['error'] = "Error in Supplier bulk create/update data"
        else:
            response['message'] = "Supplier Bulk Create and Update Successfully Done."
        response['data'] = error_supplier_list
        return Response(response, status=status.HTTP_200_OK)


class ManufacturerBulkAPIView(GenericAPIView):
    '''Manufacturer Bulk API'''
    permission_classes = (IsAuthenticated,)

    def insert_or_update_manufacturer(self, manu_data, temp_request, request):
        '''Insert or Update the Manufacturer'''
        if Manufacturer.objects.filter(CD_MF__iexact=manu_data.get('CD_MF')).exists():
            manufacturer_obj = Manufacturer.objects.filter(
                CD_MF__iexact=manu_data.get('CD_MF'))
            if manufacturer_obj.exists():
                manufacturer_instance = manufacturer_obj.first()
                new_obj = pd.DataFrame(temp_request)
                manufacturer_update_obj = ManufacturerUpdateViews()
                manufacturer_update_obj.kwargs = {}
                manufacturer_update_obj.kwargs['ID_MF'] = manufacturer_instance.ID_MF
                new_obj.user = request.user
                manufacturer_update_obj.put(new_obj, new_obj)
        else:
            temp_request['data']['user'] = request.user.id
            new_obj = pd.DataFrame(temp_request)
            new_obj.user = request.user
            ManufacturerCreateViews.post(
                ManufacturerCreateViews, new_obj, new_obj)

    def validation_and_insert_update_manufacturer(self, manufacturer_data, error_manufacturer_list, request, copy_manufacturer_data, index):
        '''Validation as well as insertion or update in manufacturer'''
        for manu_data in manufacturer_data:
            index_list = []
            index += 1
            contact_index = -1
            flag = False
            if not PartyType.objects.filter(CD_PRTY_TYP=manu_data.get('TYP_PRTY')).exists():
                manu_data['remark'] = "Provide valid party type."
                error_manufacturer_list.append(manu_data)
                continue
            if not manu_data.get('CD_MF'):
                manu_data['remark'] = "Provide valid Manufacturer code."
                error_manufacturer_list.append(manu_data)
                continue
            if not manu_data.get('NM_TRD'):
                manu_data['remark'] = "Trade Name cannot be blank."
                error_manufacturer_list.append(manu_data)
                continue
            if not manu_data.get('NM_LGL'):
                manu_data['remark'] = "Legal Name cannot be blank."
                error_manufacturer_list.append(manu_data)
                continue
            index_list, error_manufacturer_list, manu_data, flag = validate_contact_details(
                manu_data, copy_manufacturer_data, index, contact_index, error_manufacturer_list, index_list, flag)
            if flag:
                error_manufacturer_list.append(
                    copy_manufacturer_data[index])
            for j in index_list[::-1]:
                manu_data.get('contact_details').pop(j)
            manu_data['ID_LGL_STS'] = None
            manu_data['ID_DUNS_NBR'] = None
            manu_data['DC_FSC_YR_END'] = None
            manu_data['CD_LGL_ORGN_TYP'] = None
            manu_data['URL_PGPH_VN'] = None
            manu_data['SC_MF'] = "A"
            temp_request = {}
            temp_request['data'] = manu_data
            self.insert_or_update_manufacturer(
                manu_data, temp_request, request)
        return error_manufacturer_list

    @swagger_auto_schema(tags=['Manufacturer'], operation_description="Manufacturer Bulk API", operation_summary="Manufacturer Bulk API", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'manufacturers': openapi.Schema(
                type=openapi.TYPE_ARRAY, description='Array of Manufacturers',
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'TYP_PRTY': openapi.Schema(type=openapi.TYPE_STRING, description='Manufacturer Type (OR)'),
                        'CD_MF': openapi.Schema(type=openapi.TYPE_STRING, description='Manufacturer Code'),
                        'NM_LGL': openapi.Schema(type=openapi.TYPE_STRING, description='Manufacturer Legal Name'),
                        'NM_TRD': openapi.Schema(type=openapi.TYPE_STRING, description='Manufacturer Trade Name'),
                        'contact_details': contact_details_swagger
                    }
                )
            )
        }
    ))
    def post(self, request, *args, **kwargs):
        '''Create a Manufacturer Bulk API'''
        response = {}
        error_manufacturer_list = []
        manufacturer_data = request.data.get('manufacturers', [])
        copy_manufacturer_data = deepcopy(manufacturer_data)
        if manufacturer_data:
            index = -1
            error_manufacturer_list = self.validation_and_insert_update_manufacturer(
                manufacturer_data, error_manufacturer_list, request, copy_manufacturer_data, index)
        if error_manufacturer_list:
            response['error'] = "Error in Manufacturer bulk create/update data"
        else:
            response['message'] = "Manufacturer Bulk Create and Update Successfully Done."
        response['data'] = error_manufacturer_list
        return Response(response, status=status.HTTP_200_OK)
