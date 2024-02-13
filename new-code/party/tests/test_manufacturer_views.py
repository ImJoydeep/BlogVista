from globalsettings.tests.test_models import BusinessUnitSettingModelTest
from worker.models import Manufacturer
from party.models import ContactMethodType, ContactPurposeType, PartyContactMethod, PartyRole, PartyType
from party.tests.test_models import ITUCountryModelTest, StateModelTest
from party.tests.test_views import TestEmployee
from party.tests.test_setup import TestSetUp
from django.urls import reverse
from rest_framework import status
from copy import deepcopy


class TestManufacturer(TestEmployee, TestSetUp):
    '''Test Manufacturer'''

    def create_manufacturer(self):
        payload = deepcopy(self.setting_data_supplier_create)
        payload.pop("SC_SPR")
        payload['contact_details'][0].pop('ID_PRTY_CNCT_MTH')
        payload['contact_details'][0].pop('CD_STS')
        payload['CD_MF'] = 'MF001'
        payload['SC_MF'] = 'A'
        state_id = StateModelTest.create_state(self)
        payload['contact_details'][0]['ID_ST'] = state_id.ID_ST
        itu_country_id = ITUCountryModelTest.create_itu_cy_cd(self)
        payload['contact_details'][0]['CD_CY_ITU'] = itu_country_id.CD_CY_ITU
        partytype_obj = PartyType.objects.create(
            CD_PRTY_TYP="PR", DE_PRTY_TYP="Person")
        payload['TYP_PRTY'] = partytype_obj.CD_PRTY_TYP
        PartyRole.objects.create(
            TY_RO_PRTY="SPL", NM_RO_PRTY="Manufacturer Vendor")
        response = self.client.post(
            reverse('manufacturer_create'), payload, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)
        PartyRole.objects.create(
            TY_RO_PRTY="VND", NM_RO_PRTY="Manufacturer Vendor")
        ContactPurposeType.objects.create(
            CD_TYP_CNCT_PRPS="sp", NM_TYP_CNCT_PRPS="Support")
        ContactMethodType.objects.create(
            CD_TYP_CNCT_MTH="wp", NM_TYP_CNCT_MTH="Work Phone")
        response = self.client.post(
            reverse('manufacturer_create'), payload, format='json')
        return response, payload

    def test_manufacturer_create(self):
        '''Test Manufacturer create'''
        self.authenticate()
        response = self.create_manufacturer()
        self.assertEqual(response[0].status_code, status.HTTP_200_OK)
        partytype_obj = PartyType.objects.create(
            CD_PRTY_TYP="OR", DE_PRTY_TYP="Person")
        response[1]['TYP_PRTY'] = partytype_obj.CD_PRTY_TYP
        response[1]['ID_DUNS_NBR'] = "DNS001"
        response[1]['CD_MF'] = 'MF002'
        response = self.client.post(
            reverse('manufacturer_create'), response[1], format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_manufacturer_with_no_auth(self):
        '''Test Retrieve Manufacturer with no auth'''
        response = self.client.get(reverse('manufacturer_list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_manufacturer_with_auth(self):
        '''Test Retrieve Manufacturer with auth'''
        self.authenticate()
        self.create_manufacturer()
        response = self.client.get(reverse('manufacturer_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        manufacturer_obj = Manufacturer.objects.all().last()
        response = self.client.get(
            reverse('manufacturer_list')+'?ID_MF='+str(manufacturer_obj.ID_MF))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('manufacturer_list')+'?search=a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('manufacturer_list')+'?search=a&NM_MF=a,contains&ordering=-NM_MF')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('manufacturer_list')+'?search=a&NM_MF=a,not-contains&ordering=NM_MF')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('manufacturer_list') +
                                   "?ID_BSN_UN=0&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('manufacturer_list') +
                                   "?ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        business_unit_id = BusinessUnitSettingModelTest.create_bsn_unit_setting(
            self)
        response = self.client.get(reverse('manufacturer_list') +
                                   "?ID_BSN_UN="+str(business_unit_id.ID_BSN_UN.ID_BSN_UN)+"&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('manufacturer_list') +
                                   "?NM_MF=ai,contains&ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('manufacturer_list') +
                                   "?NM_MF=name_manufacturer,equals&ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_manufacturer(self):
        '''Test update_manufacturer'''
        self.authenticate()
        created_manufacturer_data = self.create_manufacturer()
        payload = created_manufacturer_data[1]
        payload['CD_MF'] = "MF100"
        payload['contact_details'][0]['CD_STS'] = "A"
        response = self.client.put(
            reverse('manufacturer_update', kwargs={'ID_MF': created_manufacturer_data[0].data.get('ID_MF')}), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = Manufacturer.objects.filter(
            ID_MF=created_manufacturer_data[0].data.get('ID_MF')).last()
        self.assertEqual(updated_data.CD_MF, "MF100")

    def test_manufacturer_multiple_status_update(self):
        '''Test manufacturer multiple status update'''
        self.authenticate()
        created_manufacturer_data = self.create_manufacturer()
        res = {
            "ids": [created_manufacturer_data[0].data.get('ID_MF')],
            "status": "I"
        }
        response = self.client.put(
            reverse('manufacturer_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = Manufacturer.objects.filter(
            ID_MF=created_manufacturer_data[0].data.get('ID_MF')).last()
        self.assertEqual(updated_data.SC_MF, 'I')
        res = {
            "ids": [0],
            "status": "I"
        }
        response = self.client.put(
            reverse('manufacturer_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        party_obj = PartyContactMethod.objects.last()
        res = {
            "ids": [created_manufacturer_data[0].data.get('ID_MF')],
            "status": "I",
            'contacts': {
                'ids': [party_obj.ID_PRTY_CNCT_MTH],
                'status': 'I'
            }
        }
        response = self.client.put(
            reverse('manufacturer_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = PartyContactMethod.objects.filter(
            ID_PRTY_CNCT_MTH=party_obj.ID_PRTY_CNCT_MTH).last()
        self.assertEqual(updated_data.CD_STS, "I")
        res = {
            "ids": [created_manufacturer_data[0].data.get('ID_MF')],
            "status": "I",
            'contacts': {
                'ids': [0],
                'status': 'I'
            }
        }
        response = self.client.put(
            reverse('manufacturer_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_manufacturer_multiple_delete(self):
        '''Test manufacturer multiple delete'''
        self.authenticate()
        created_manufacturer_data = self.create_manufacturer()
        party_obj = PartyContactMethod.objects.last()
        res = {
            "ids": [created_manufacturer_data[0].data.get('ID_MF')],
            'contacts': {
                'ids': [party_obj.ID_PRTY_CNCT_MTH]
            }
        }
        response = self.client.delete(
            reverse('manufacturer_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = {
            "ids": [created_manufacturer_data[0].data.get('ID_MF')]
        }
        response = self.client.delete(
            reverse('manufacturer_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = {
            "ids": [0]
        }
        response = self.client.delete(
            reverse('manufacturer_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
