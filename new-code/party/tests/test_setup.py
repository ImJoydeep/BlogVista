import os
from rest_framework.test import APITestCase
from django.urls import reverse
from django.core.cache import cache
from django.utils.crypto import get_random_string as grs


class TestSetUp(APITestCase):
    ''' Test Setup '''

    def setUp(self):
        ''' Here we setup data for unit test '''
        self.register_url = reverse('signup')
        self.login_url = reverse('signin')
        self.user_data = {"username": str(os.getenv('TEST_USERNAME')),
                          "email": str(os.getenv('TEST_EMAIL')),
                          "password": str(os.getenv('TEST_PASSWORD'))
                          }
        self.setting_data_employee = {
            "FN_PRS": "First Name",
            "MD_PRS": "Middle Name",
            "LN_PRS": "Last Name",
            "SC_EM": "A",
            "URL_PGPH_WRKR": "Photo",
            "contact_details": [
                {
                    "CD_TYP_CNCT_PRPS": "sp",
                    "CD_TYP_CNCT_MTH": "wp",
                    "A1_ADS": "Address 1",
                    "A2_ADS": "Address 2",
                    "CI_CNCT": "City",
                    "ST_CNCT": "State",
                    "CD_CY_ITU": "",
                    "PH_CMPL": "+1 200-12346",
                    "EM_ADS": "test@gmail.com",
                    "CD_PSTL": "POstal Code",
                    "CD_STS": "A",
                    "ID_ST": ""
                }
            ]

        }
        self.setting_data_employee1 = {
            "FN_PRS": "First",
            "MD_PRS": "Middle",
            "LN_PRS": "Last",
            "SC_EM": "A",
            "URL_PGPH_WRKR": "Photo",
            "contact_details": [
                {
                    "CD_TYP_CNCT_PRPS": "sp",
                    "CD_TYP_CNCT_MTH": "wp",
                    "A1_ADS": "Address 1",
                    "A2_ADS": "Address 2",
                    "CI_CNCT": "City",
                    "ST_CNCT": "State",
                    "CD_CY_ITU": "",
                    "PH_CMPL": "+1 200-12346",
                    "EM_ADS": "test@gmail.com",
                    "CD_PSTL": "POstal Code",
                    "CD_STS": "A",
                    "ID_ST": ""
                }
            ]

        }
        self.setting_data_state = {
            "NM_ST": "California",
            "CD_ST": "Cal-001"
        }
        self.setting_data_itucountry = {
            "CD_CY_ITU": grs(
                length=2, allowed_chars='ACTG'),
            "NM_CY_ITU": "USA"
        }
        self.setting_data_contactmethod = {
            "CD_TYP_CNCT_MTH": grs(
                length=6, allowed_chars='ACTG'),
            "NM_TYP_CNCT_MTH": "Work Phone"
        }
        self.setting_data_contactpurpose = {
            "CD_TYP_CNCT_PRPS": grs(length=2, allowed_chars='ACTG'),
            "NM_TYP_CNCT_PRPS": "Support"
        }
        self.setting_data_deletemultiple = {
            "ids": [0],
            "contacts": {
                "ids": [

                ]
            },
            "positions": {
                "ids": [

                ]
            },
            "permissions": {
                "ids": [

                ]
            },
            "work_availability": {
                "ids": [

                ]
            }
        }
        self.setting_data_updatemultiple = {
            "ids": [
                0
            ],
            "status": "",
            "positions": {
                "ids": [
                    0
                ],
                "status": ""
            },

        }
        self.setting_data_employee_update = {
            "URL_PGPH_WRKR": None,
            "FN_PRS": 'FN_PRS',
            "LN_PRS": 'LN_PRS',
            "MD_PRS": None,
            "position_details": [
                {
                    "ID_ASGMT_WRKR_PSN": 0,
                    "DC_EF": "",
                    "SC_EM_ASGMT": "A",
                    "DC_EP": "",
                    "NM_TTL": "",
                    "FL_TM_FL": True,
                    "FL_SLRY": True,
                    "FL_EXM_OVR_TM": True,
                    "FL_RTE_PNL": True,
                    "FL_CMN": True,
                    "CD_PRD_PY": "",
                    "MO_RTE_PY": "",
                    "ID_PST": 0,
                    "ID_WRKR": 0
                }
            ],
            "work_availability": [
                {
                    "ID_WRKR_AVLB": 0,
                    "ST_WRKR_AVLB": "A",
                    "DC_EF": "",
                    "DC_EP": "",
                    "ID_WRKR": 0,
                    "ID_GP_TM": 0,
                    "ID_LCN": 0
                }
            ],
            "operator_details": [
                {
                    "ID_ASGMT_WRKR_OPR": 0,
                    "TS_EP": "",
                    "SC_ASGMT": "A",
                    "ID_WRKR": 0,
                    "ID_OPR": 0
                }
            ],
            "contact_details": [
                {
                    "DC_EP": "2022-09-16T06:11:27.641Z",
                    "CD_STS": "A",
                    "CD_TYP_CNCT_PRPS": "",
                    "CD_TYP_CNCT_MTH": "",
                    "ID_PRTY_RO_ASGMT": 0,
                    "ID_SCL_NTWRK_HNDL": None,
                    "ID_ADS": None,
                    "ID_EM_ADS": None,
                    "ID_PH": None,
                    "ID_WB_STE": None,
                    "PCM_CRT_BY": 0,
                    "PCM_MDF_BY": 0,
                    "EM_ADS": "email@gmail.com"
                }
            ]
        }
        self.setting_data_supplier_create = {
            "TYP_PRTY": "PR",
            "CD_SPR": "SUP_001",
            "FN_PRS": "Aiko",
            "MD_PRS": "Blaine Browning",
            "LN_PRS": "Wall",
            "URL_PGPH_VN": "images.jpeg",
            "TY_GND_PRS": "Female",
            "DC_PRS_BRT": None,
            "ID_LGL_STS": None,
            "NM_LGL": "LegalName",
            "NM_TRD": "TradeName",
            "ID_DUNS_NBR": "DUNSNumber",
            "DC_FSC_YR_END": None,
            "CD_LGL_ORGN_TYP": None,
            "SC_SPR": "A",
            "contact_details": [{
                "ID_PRTY_CNCT_MTH": None,
                "CD_TYP_CNCT_PRPS": "sp",
                "CD_TYP_CNCT_MTH": "wp",
                "A1_ADS": "add1",
                "A2_ADS": "add3",
                "CI_CNCT": "city",
                "ID_ST": None,
                "CD_CY_ITU": None,
                "PH_CMPL": "+1 666-666-6666",
                "EM_ADS": "abc@g.com",
                "CD_PSTL": "56678",
                "CD_STS": "A"
            }]
        }
        self.setting_data_update_status = {
            "ids": [],
        }
        return super().setUp()

    def tearDown(self) -> None:
        cache.clear()
        return super().tearDown()
