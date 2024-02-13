from party.tests.test_models import ITUCountryModelTest, PartyContactMethodModelTest, TelephoneModelTest
from globalsettings.tests.test_models import BusinessUnitSettingModelTest
from party.models import PartyContactMethod, Person, Telephone
from party.tests.test_views import TestEmployee
from django.urls import reverse
from rest_framework import status

from worker.models import Employee, Supplier


class TestEmployeeUpdate(TestEmployee):
    def test_update_employee(self):
        '''test update_employee'''
        self.authenticate()
        res1 = self.setting_data_employee_update
        response = self.create_employee()
        self.update_employee()
        res = self.client.put(
            reverse("employee_update", kwargs={
                'employee_id': response.data['ID_EM']}), res1, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        employee_obj = Employee.objects.get(ID_EM=response.data['ID_EM'])
        worker_obj = employee_obj.ID_WRKR
        party_obj = worker_obj.ID_PRTY_RO_ASGMT.ID_PRTY
        updated_data = Person.objects.get(ID_PRTY=party_obj)
        self.assertEqual(updated_data.FN_PRS, 'FN_PRS')
        res1 = self.setting_data_employee_update
        res = self.client.put(
            reverse("employee_update", kwargs={
                'employee_id': 0}), res1, format='json')
        self.assertEqual(
            res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        res1 = self.setting_data_employee_update
        res1['URL_PGPH_WRKR'] = 'url'
        itu_instance = ITUCountryModelTest.create_itu_cy_cd(self)
        tel_id = Telephone.objects.create(
            CD_CY_ITU=itu_instance, TA_PH="952", TL_PH="256-985-4854", PH_EXTN="+1", PH_CMPL="+1 256-985-4854")
        res1['contact_details'][0]['ID_PH'] = tel_id.ID_PH
        res = self.client.put(
            reverse("employee_update", kwargs={
                'employee_id': response.data['ID_EM']}), res1, format='json')
        self.assertEqual(
            res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        res1 = self.setting_data_employee_update
        res1['position_details'][0]['ID_ASGMT_WRKR_PSN'] = None
        res = self.client.put(
            reverse("employee_update", kwargs={
                'employee_id': response.data['ID_EM']}), res1, format='json')
        self.assertEqual(
            res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        res1['work_availability'][0]['ID_WRKR_AVLB'] = None
        res = self.client.put(
            reverse("employee_update", kwargs={
                'employee_id': response.data['ID_EM']}), res1, format='json')
        self.assertEqual(
            res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        res1['operator_details'][0]['ID_ASGMT_WRKR_OPR'] = None
        res = self.client.put(
            reverse("employee_update", kwargs={
                'employee_id': response.data['ID_EM']}), res1, format='json')
        self.assertEqual(
            res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        res1 = {
            "URL_PGPH_WRKR": None,
            "FN_PRS": 'FN_PRS',
            "LN_PRS": 'LN_PRS',
            "MD_PRS": None,
        }
        res = self.client.put(
            reverse("employee_update", kwargs={
                'employee_id': response.data['ID_EM']}), res1, format='json')
        self.assertEqual(
            res.status_code, status.HTTP_200_OK)


class TestPartyContact(TestEmployee):
    '''Test Party contact'''

    def test_state_not_list_with_auth(self):
        '''test retrieve state with auth'''
        self.authenticate()
        self.create_state()
        res = self.client.get(reverse('State_List'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data['results'], list)

    def test_country_should_list_with_auth(self):
        '''test retrieve Country with auth'''
        self.authenticate()
        self.create_country()
        res = self.client.get(reverse('Country_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data['results'], list)

    def test_contact_method_should_list_with_auth(self):
        '''test retrieve contact method with auth'''
        self.authenticate()
        self.create_contact_method()
        res = self.client.get(reverse('contactmethod'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data, list)

    def test_contact_purpose_should_list_with_auth(self):
        '''test retrieve contact purpose with auth'''
        self.authenticate()
        self.create_contact_purpose()
        res = self.client.get(reverse('contactpurpose'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res.data, list)


class TestSupplier(TestEmployee):
    ''' Test Supplier'''

    def test_create_supplier(self):
        '''Test create supplier'''
        self.authenticate()
        response = self.create_supplier()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = self.setting_data_supplier_create
        res['TYP_PRTY'] = None
        response = self.client.post(
            reverse('supplier_create'), res, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)
        res['CD_SPR'] = 'SUP_002'
        response = self.client.post(
            reverse('supplier_create'), res, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_retrieve_supplier_with_auth(self):
        '''Test retrieve supplier with auth'''
        self.authenticate()
        self.create_supplier()
        response = self.client.get(reverse('supplier_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('supplier_list')+"?search=a")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        create_supplier_obj = Supplier.objects.last()
        response = self.client.get(
            reverse('supplier_list')+"?ID_SPR="+str(create_supplier_obj.ID_SPR))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=&SC_SPR=A,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=&SC_SPR=A,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&TYP_PRTY=a,start-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&NM_SPR=a,end-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&NM_LGL=a,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&NM_TRD=a,not-contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&NM_TRD=a,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&PH_CMPL=5,greater-equal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&TYP_PRTY=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&NM_SPR=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&NM_LGL=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&EM_ADS=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&EM_ADS=a,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&PH_CMPL=5,not-equals&ordering=NM_SPR')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&PH_CMPL=5,not-equals&ordering=-NM_SPR')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('supplier_list')+'?search=a&PH_CMPL=5,not-equalss&ordering=-NM_SPR')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('supplier_list') +
                                   "?ID_BSN_UN=0&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('supplier_list') +
                                   "?ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        business_unit_id = BusinessUnitSettingModelTest.create_bsn_unit_setting(
            self)
        response = self.client.get(reverse('supplier_list') +
                                   "?ID_BSN_UN="+str(business_unit_id.ID_BSN_UN.ID_BSN_UN)+"&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('supplier_list') +
                                   "?CD_SPR=SUP,contains&ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('supplier_list') +
                                   "?NM_SPR=name_supplier,equals&ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_supplier_with_no_auth(self):
        '''Test retrieve supplier with no auth'''
        self.create_supplier()
        response = self.client.get(reverse('supplier_list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_supplier(self):
        '''Test update supplier'''
        self.authenticate()
        created_response = self.create_supplier()
        res = self.setting_data_supplier_create
        res['FN_PRS'] = "test name"
        res['TY_GND_PRS'] = "Male"
        res['SC_SPR'] = "I"
        response = self.client.put(reverse('supplier_update', kwargs={
            "ID_SPR": created_response.data['ID_SPR']}), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = Supplier.objects.filter(
            ID_SPR=created_response.data['ID_SPR']).last()
        self.assertEqual(updated_data.SC_SPR, "I")
        response = self.client.put(reverse('supplier_update', kwargs={
            "ID_SPR": 0}), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_supplier_status(self):
        '''Test update supplier status'''
        self.authenticate()
        created_response = self.create_supplier()
        res = self.setting_data_update_status
        res['ids'] = [created_response.data['ID_SPR']]
        res['status'] = "I"
        response = self.client.put(
            reverse('supplier_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = Supplier.objects.filter(
            ID_SPR=created_response.data['ID_SPR']).last()
        self.assertEqual(updated_data.SC_SPR, "I")
        res['ids'] = [0]
        res['status'] = "I"
        response = self.client.put(
            reverse('supplier_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        party_obj = PartyContactMethod.objects.last()
        res = {
            "ids": [],
            "status": "I",
            'contacts': {
                'ids': [party_obj.ID_PRTY_CNCT_MTH],
                'status': 'I'
            }
        }

        response = self.client.put(
            reverse('supplier_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = PartyContactMethod.objects.filter(
            ID_PRTY_CNCT_MTH=party_obj.ID_PRTY_CNCT_MTH).last()
        self.assertEqual(updated_data.CD_STS, "I")
        res = {
            "ids": [],
            "status": "I",
            'contacts': {
                'ids': [0],
                'status': 'I'
            }
        }
        response = self.client.put(
            reverse('supplier_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_supplier(self):
        '''Test update supplier status'''
        self.authenticate()
        created_response = self.create_supplier()
        party_obj = PartyContactMethodModelTest.create_prty_cnct_mth(self)
        res = {
            "ids": [],
            'contacts': {
                'ids': [party_obj.ID_PRTY_CNCT_MTH],
            }
        }
        response = self.client.delete(
            reverse('supplier_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res = self.setting_data_update_status
        res['ids'] = [created_response.data['ID_SPR']]
        updated_data = Supplier.objects.filter(
            ID_SPR=created_response.data['ID_SPR']).exists()
        self.assertEqual(updated_data, True)
        response = self.client.delete(
            reverse('supplier_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_data = Supplier.objects.filter(
            ID_SPR=created_response.data['ID_SPR']).exists()
        self.assertEqual(updated_data, False)
        res['ids'] = [0]
        response = self.client.delete(
            reverse('supplier_multiple_status_update'), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_legal_status_type_auth(self):
        '''test retrieve Employee with auth'''
        self.authenticate()
        res = self.client.get(reverse('legalstatustype'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
