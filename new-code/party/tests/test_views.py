from django.contrib.auth.models import User
from position.models import WorkerPositionAssignment
from globalsettings.tests.test_models import BusinessUnitSettingModelTest
from worker.models import Employee
from party.models import ITUCountry, PartyContactMethod, PartyType, PartyRole, ContactPurposeType, ContactMethodType, State
from .test_setup import TestSetUp
from django.urls import reverse
from rest_framework import status
from party.tests.test_models import ITUCountryModelTest, PartyContactMethodModelTest, PostalCodeRefModelTest, StateModelTest, TelephoneModelTest
from position.tests.test_models import WorkerPsnAsgmtModelTest
from workerschedule.tests.test_models import WorkerAvlbModelTest
from accesscontrol.tests.test_models import WrkrOprAsgmtModelTest


class TestEmployee(TestSetUp):
    '''common test case functions'''

    def authenticate(self):
        '''user authentication'''
        self.client.post(self.register_url, self.user_data, format="json")
        res = self.client.post(self.login_url, self.user_data, format="json")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def create_Emp_partcont_WorkP_WorkA_WorkO(self):
        '''create employee party contact worker availability worker position worker operator'''
        res = self.setting_data_deletemultiple
        emp = self.create_employee()
        res['ids'] = [emp.data['ID_EM']]

    def update_employee(self):
        '''create employee parcontact worker availability worker position worker operator'''
        res = self.setting_data_employee_update
        party_contact_method_obj = PartyContactMethodModelTest.create_prty_cnct_mth(
            self)
        telephone_obj = TelephoneModelTest.create_telephone(self)
        res['contact_details'][0]['ID_PH'] = telephone_obj.pk
        postal_obj = PostalCodeRefModelTest.create_pstl_cd_ref(self)
        res['contact_details'][0]['CD_PSTL'] = postal_obj.CD_PSTL
        res['contact_details'][0]['A1_ADS'] = party_contact_method_obj.ID_ADS.A1_ADS
        res['contact_details'][0]['A2_ADS'] = party_contact_method_obj.ID_ADS.A2_ADS
        res['contact_details'][0]['CI_CNCT'] = party_contact_method_obj.ID_ADS.CI_CNCT
        res['contact_details'][0]['ID_ST'] = None
        res['contact_details'][0]['ID_EM_ADS'] = party_contact_method_obj.ID_EM_ADS.ID_EM_ADS
        postal_code_ref_obj = PostalCodeRefModelTest.create_pstl_cd_ref(self)
        res['contact_details'][0]['ID_PSTL_CD'] = postal_code_ref_obj.ID_PSTL_CD
        res['contact_details'][0]['ID_ADS'] = party_contact_method_obj.ID_ADS.ID_ADS

        res['contact_details'][0]['ID_PRTY_CNCT_MTH'] = party_contact_method_obj.ID_PRTY_CNCT_MTH

        res['contact_details'][0]['CD_TYP_CNCT_PRPS'] = party_contact_method_obj.CD_TYP_CNCT_PRPS.pk
        res['contact_details'][0]['CD_TYP_CNCT_MTH'] = party_contact_method_obj.CD_TYP_CNCT_MTH.pk
        res['contact_details'][0]['ID_PRTY_RO_ASGMT'] = party_contact_method_obj.ID_PRTY_RO_ASGMT.pk
        res['contact_details'][0]['CD_CY_ITU'] = telephone_obj.CD_CY_ITU.CD_CY_ITU
        res['contact_details'][0]['PH_CMPL'] = telephone_obj.PH_CMPL
        res['contact_details'][0]['TA_PH'] = telephone_obj.TA_PH
        res['contact_details'][0]['TL_PH'] = telephone_obj.TL_PH
        workeroperator_obj = WrkrOprAsgmtModelTest.create_wrkr_opr_asgmt(self)
        res['operator_details'][0]['ID_ASGMT_WRKR_OPR'] = workeroperator_obj.ID_ASGMT_WRKR_OPR
        res['operator_details'][0]['TS_EP'] = workeroperator_obj.TS_EP
        res['operator_details'][0]['SC_ASGMT'] = workeroperator_obj.SC_ASGMT
        res['operator_details'][0]['ID_WRKR'] = workeroperator_obj.ID_WRKR.ID_WRKR
        res['operator_details'][0]['ID_OPR'] = workeroperator_obj.ID_OPR.ID_OPR
        workeravail_obj = WorkerAvlbModelTest.create_worker_availability_group(
            self)
        res['work_availability'][0]['ID_WRKR_AVLB'] = workeravail_obj.ID_WRKR_AVLB
        res['work_availability'][0]['ID_GP_TM'] = workeravail_obj.ID_GP_TM.ID_GP_TM
        res['work_availability'][0]['DC_EF'] = workeravail_obj.DC_EF
        res['work_availability'][0]['DC_EP'] = workeravail_obj.DC_EP
        res['work_availability'][0]['ID_WRKR'] = workeravail_obj.ID_WRKR.ID_WRKR
        res['work_availability'][0]['ID_LCN'] = None
        workerposition_obj = WorkerPsnAsgmtModelTest.create_wrk_psn_asgmt(self)
        res['position_details'][0]['ID_ASGMT_WRKR_PSN'] = workerposition_obj.ID_ASGMT_WRKR_PSN
        res['position_details'][0]['DC_EF'] = workerposition_obj.DC_EF
        res['position_details'][0]['SC_EM_ASGMT'] = workerposition_obj.SC_EM_ASGMT
        res['position_details'][0]['DC_EP'] = workerposition_obj.DC_EP
        res['position_details'][0]['NM_TTL'] = workerposition_obj.NM_TTL
        res['position_details'][0]['CD_PRD_PY'] = workerposition_obj.CD_PRD_PY
        res['position_details'][0]['MO_RTE_PY'] = workerposition_obj.MO_RTE_PY
        res['position_details'][0]['ID_PST'] = workerposition_obj.ID_PST.ID_PST
        res['position_details'][0]['ID_WRKR'] = workerposition_obj.ID_WRKR.ID_WRKR

    def update_Emp_partcont_WorkP_WorkA_WorkO(self):
        '''update employee party contact worker availability worker position worker operator'''
        res = self.setting_data_updatemultiple
        emp = self.create_employee()
        res['ids'] = [emp.data['ID_EM']]
        res['status'] = None
        workP = WorkerPsnAsgmtModelTest.create_wrk_psn_asgmt(self)
        res['positions']['ids'] = [workP.ID_ASGMT_WRKR_PSN]
        res['positions']['status'] = 'I'

    def create_country(self):
        '''Create country'''
        response = self.setting_data_itucountry
        return ITUCountry.objects.create(**response)

    def create_state(self):
        '''create state'''
        countryinstance = self.create_country()
        response_state = self.setting_data_state
        response_state["CD_CY_ITU"] = countryinstance
        return State.objects.create(**response_state)

    def create_contact_method(self):
        '''create contact method'''
        response = self.setting_data_contactmethod
        contactmethod_instance = ContactMethodType.objects.create(**response)

    def create_contact_purpose(self):
        '''create contact purpose'''
        response = self.setting_data_contactpurpose
        return ContactPurposeType.objects.create(**response)

    def create_employee(self):
        '''create employee'''
        response = self.setting_data_employee
        state_id = StateModelTest.create_state(self)
        response['contact_details'][0]['ID_ST'] = state_id.ID_ST
        itu_country_id = ITUCountryModelTest.create_itu_cy_cd(self)
        response['contact_details'][0]['CD_CY_ITU'] = itu_country_id.CD_CY_ITU
        PartyType.objects.create(CD_PRTY_TYP="PR", DE_PRTY_TYP="Person")
        PartyRole.objects.create(TY_RO_PRTY="WRK", NM_RO_PRTY="Worker")
        ContactPurposeType.objects.create(
            CD_TYP_CNCT_PRPS="sp", NM_TYP_CNCT_PRPS="Support")
        ContactMethodType.objects.create(
            CD_TYP_CNCT_MTH="wp", NM_TYP_CNCT_MTH="Work Phone")
        response = self.client.post(
            reverse('employee_create'), response, format="json")
        return response

    def create_supplier(self):
        '''create supplier'''
        res = self.setting_data_supplier_create
        state_id = StateModelTest.create_state(self)
        res['contact_details'][0]['ID_ST'] = state_id.ID_ST
        itu_country_id = ITUCountryModelTest.create_itu_cy_cd(self)
        res['contact_details'][0]['CD_CY_ITU'] = itu_country_id.CD_CY_ITU
        partytype_obj = PartyType.objects.create(
            CD_PRTY_TYP="PR", DE_PRTY_TYP="Person")
        res['TYP_PRTY'] = partytype_obj.CD_PRTY_TYP
        PartyRole.objects.create(TY_RO_PRTY="SPL", NM_RO_PRTY="Worker")
        ContactPurposeType.objects.create(
            CD_TYP_CNCT_PRPS="sp", NM_TYP_CNCT_PRPS="Support")
        ContactMethodType.objects.create(
            CD_TYP_CNCT_MTH="wp", NM_TYP_CNCT_MTH="Work Phone")
        response = self.client.post(
            reverse('supplier_create'), res, format='json')
        return response


class TestEmployees(TestEmployee):
    ''' Test Employee '''

    def test_should_not_create_employee_with_no_auth(self):
        '''test Employee should not be created with no auth'''
        res = self.create_employee()
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_should_create_employee_auth(self):
        '''test create Employee with auth'''
        self.authenticate()
        res = self.create_employee()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['FN_PRS'], 'First Name')
        res = self.setting_data_employee
        res['contact_details'] = []
        response = self.client.post(
            reverse('employee_create'), res, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_employee_list_with_auth(self):
        '''test retrieve Employee with auth'''
        self.authenticate()
        res = self.client.get(reverse('employee_list'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        url = reverse('employee_list') + '?search=a'
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.create_employee()
        url = reverse('employee_list') + '?ID_EM='+str(res.data['ID_EM'])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=&SC_EM=A,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=&SC_EM=A,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&position_name=a,start-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&permission_set=a,end-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&operator=a,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&department_name=a,not-contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&EM_ADS=a,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&employee_name=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&PH_CMPL=5,greater-equal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&position_name=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&permission_set=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&operator=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&department_name=a,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&EM_ADS=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&employee_name=a,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&PH_CMPL=5,not-equals&ordering=position_name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&PH_CMPL=5,not-equals&ordering=-position_name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list')+'?search=a&PH_CMPL=5,not-equalss&ordering=-position_name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=Annonymous,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=Annonymous,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=Annonymous,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=Annonymous,start-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=Annonymous,not-contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=a,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=a,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=a,start-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_CRT=a,not-contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_UPDT=a,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_UPDT=a,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_UPDT=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_UPDT=a,start-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ID_USR_UPDT=a,not-contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&CRT_DT=2023-04-20,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&CRT_DT=2023-04-20,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&CRT_DT=2023-04-20,less-than')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&CRT_DT=2023-04-20,greater-equal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&UPDT_DT=2023-04-20,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&UPDT_DT=2023-04-20,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&UPDT_DT=2023-04-20,less-than')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&UPDT_DT=2023-04-20,greater-equal')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&employee_name=a,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&employee_name=a,contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&employee_name=a,not-equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&employee_name=a,start-with')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&employee_name=a,not-contains')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=first last&page=1&page_size=50&ordering=CRT_DT&employee_name=first last,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&?ID_BSN_UN=25')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&EM_ADS=abc@navsoft.in,equals')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.get(
            reverse('employee_list') + '?search=&page=1&page_size=50&ordering=-operator')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.setting_data_employee1
        self.client.get(
            reverse('employee_list') + '?search=A&page=1&page_size=50&ID_BSN_UN=0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('employee_list') +
                                   "?ID_BSN_UN=0&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('employee_list') +
                                   "?ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        business_unit_id = BusinessUnitSettingModelTest.create_bsn_unit_setting(
            self)
        response = self.client.get(reverse('employee_list') +
                                   "?ID_BSN_UN="+str(business_unit_id.ID_BSN_UN.ID_BSN_UN)+"&export_flag=1&device_id=cTWUD2NsQ-2ac93Vph_ocQ:APA91bE-6_qwcHXb6e98MxdJOYFDAXpItgXWMmGZxPTPvPXKIZqGR9Zsj6SO_AlHQ8iRWUtgvS8CKBhZaXwnqz7lAxWE0mdOp23y2VdetDsBpanqJSWY6MlwJHOkh69fkYOd5-iotFbq")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('employee_list') +
                                   "?position_name=name,equals&ID_BSN_UN=1000&export_flag=1")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_multiple_with_auth(self):
        '''test delete Employee with auth'''
        self.authenticate()
        self.create_Emp_partcont_WorkP_WorkA_WorkO()
        res = self.setting_data_deletemultiple
        prev_db_count = Employee.objects.all().count()

        self.assertGreater(prev_db_count, 0)
        self.assertEqual(prev_db_count, 1)
        response = self.client.delete(
            reverse("employee_multiple_status_update"), res, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': [0]
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        party = PartyContactMethodModelTest.create_prty_cnct_mth(self)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'contacts': {'ids': [party.ID_PRTY_CNCT_MTH],
                                                                       },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        if "contacts" in res:
            self.assertEqual(PartyContactMethod.objects.all().count(), 1)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'contacts': {'ids': [0],
                                                                       },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        workP = WorkerPsnAsgmtModelTest.create_wrk_psn_asgmt(self)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'positions': {'ids': [workP.ID_ASGMT_WRKR_PSN],
                                                                        },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'positions': {'ids': [0],
                                                                        },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        workA = WorkerAvlbModelTest.create_worker_availability_group(self)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'work_availability': {'ids': [workA.ID_WRKR_AVLB],
                                                                                },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'work_availability': {'ids': [0],
                                                                                },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        workA = WrkrOprAsgmtModelTest.create_wrkr_opr_asgmt(self)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'permissions': {'ids': [workA.ID_ASGMT_WRKR_OPR],
                                                                          },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids'],
                                                          'permissions': {'ids': [0],
                                                                          },
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.delete(
            reverse("employee_multiple_status_update"),  {'ids': res['ids']
                                                          }, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update_multiple_status(self):
        '''test update Employee with auth'''
        self.authenticate()
        res1 = self.setting_data_updatemultiple
        self.update_Emp_partcont_WorkP_WorkA_WorkO()
        res = self.client.put(
            reverse("employee_multiple_status_update"), res1, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        if "positions" in res1:
            updated_gsetting = WorkerPositionAssignment.objects.filter(
                SC_EM_ASGMT=res1['positions']['status']).last()
            self.assertEqual(updated_gsetting.SC_EM_ASGMT, 'I')
        res1['status'] = 'I'
        res = self.client.put(
            reverse("employee_multiple_status_update"), res1, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'positions': {'ids': [0],
                                                                       "status": 'I'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        party_contact_obj = PartyContactMethod.objects.last()
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'contacts': {'ids': [party_contact_obj.ID_PRTY_CNCT_MTH],
                                                                      "status": 'I'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'contacts': {'ids': [0],
                                                                      "status": 'I'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        worker_obj = WorkerAvlbModelTest.create_worker_availability_group(self)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'work_availability': {'ids': [worker_obj.ID_WRKR_AVLB],
                                                                               "status": 'I'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'work_availability': {'ids': [0],
                                                                               "status": 'I'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        User.objects.create(password="password", username="username")
        workA = WrkrOprAsgmtModelTest.create_wrkr_opr_asgmt(self)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'permissions': {'ids': [workA.ID_ASGMT_WRKR_OPR],
                                                                         "status": 'A'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'permissions': {'ids': [workA.ID_ASGMT_WRKR_OPR],
                                                                         "status": 'I'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': res1['ids'],
                                                         'status': None,
                                                         'permissions': {'ids': [0],
                                                                         "status": 'I'},
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        res = self.client.put(
            reverse("employee_multiple_status_update"), {'ids': [0],
                                                         'status': None,
                                                         }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
