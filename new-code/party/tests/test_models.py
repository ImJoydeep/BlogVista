from django.test import TestCase
from django.utils import timezone
from random import randint, randrange
from django.utils.crypto import get_random_string

from party.models import Address, Consumer, ContactMethodType, ContactPurposeType, EmailAddress, ExternalPartyIdentificationProvider, GeographicSegment, ISO3166_1Country, ISO3166_2CountrySubdivision, ISO3166_2PrimarySubdivisionType, ITUCountry, Language, LegalOrganizationType, OperationalParty, Organization, Party, PartyContactMethod, PartyIdentification, PartyIdentificationType, PartyRole, PartyRoleAssignment, PartyType, Person, PostalCodeReference, SocialNetworkHandle, SocialNetworkService, SocialNetworkType, State, Telephone, WebSite


# models test
class PartyTypeModelTest(TestCase):
    '''Party Type Model Test'''

    def create_party_type(self, DE_PRTY_TYP="This is party type one"):
        '''Create a party type'''
        CD_PRTY_TYP = randint(1000000, 9999999)
        return PartyType.objects.create(CD_PRTY_TYP=CD_PRTY_TYP, DE_PRTY_TYP=DE_PRTY_TYP)

    def test_party_type_creation(self):
        '''Test party type creation'''
        w = self.create_party_type()
        self.assertTrue(isinstance(w, PartyType))
        self.assertEqual(w.__str__(), w.CD_PRTY_TYP)


class PartyModelTest(PartyTypeModelTest, TestCase):
    '''Party Model Test'''

    def create_party(self):
        '''Create Party'''
        prty_typ_instance = PartyTypeModelTest.create_party_type(self)
        return Party.objects.create(ID_PRTY_TYP=prty_typ_instance)

    def test_party_creation(self):
        '''Test Party creation'''
        w = self.create_party()
        self.assertTrue(isinstance(w, Party))
        self.assertEqual(w.__unicode__(), w.ID_PRTY_TYP)


class PartyRoleModelTest(TestCase):
    '''Party Role Model Test'''

    def create_party_role(self, NM_RO_PRTY="PARTY_ROLE_1", DE_RO_PRTY="Party Role Description"):
        '''Create a partyrole'''
        prty_ro_code = randrange(10000, 99999)
        return PartyRole.objects.create(TY_RO_PRTY=prty_ro_code, NM_RO_PRTY=NM_RO_PRTY, DE_RO_PRTY=DE_RO_PRTY)

    def test_party_role_creation(self):
        '''Test party role creation'''
        w = self.create_party_role()
        self.assertTrue(isinstance(w, PartyRole))
        self.assertEqual(w.__unicode__(), w.NM_RO_PRTY)


class PartyRoleAssgnModelTest(PartyModelTest, PartyTypeModelTest, PartyRoleModelTest, TestCase):
    '''Party Role Assignment model test'''

    def create_prty_role_assign(self, ID_PRTY_RO_ASGMT=1):
        '''Create a party role assignment'''
        prty_role_instance = PartyRoleModelTest.create_party_role(self)

        prty_typ_instance = PartyTypeModelTest.create_party_type(self)
        prty_instance = PartyModelTest.create_party(self)
        return PartyRoleAssignment.objects.create(ID_PRTY=prty_instance, ID_RO_PRTY=prty_role_instance, DC_EF_RO_PRTY=timezone.now(), DC_EP_RO_PRTY=timezone.now())

    def test_party_role_asgn_creation(self):
        '''Test party role assignment creation'''
        w = self.create_prty_role_assign()
        self.assertTrue(w, PartyRoleAssignment)
        self.assertEqual(w.__unicode__(), w.SC_RO_PRTY)


class ContactPurposeTypeModelTest(TestCase):
    '''Contact Purpose Type Model Test'''

    def create_cnct_prps_typ(self, CD_TYP_CNCT_PRPS="CP", NM_TYP_CNCT_PRPS="CP"):
        '''Create Contact Purpose Type Model Test'''
        return ContactPurposeType.objects.create(CD_TYP_CNCT_PRPS=CD_TYP_CNCT_PRPS, NM_TYP_CNCT_PRPS=NM_TYP_CNCT_PRPS)

    def test_cnct_prps_type(self):
        '''Test Contact Purpose type creation'''
        w = self.create_cnct_prps_typ()
        self.assertTrue(isinstance(w, ContactPurposeType))
        self.assertEqual(w.__str__(), w.NM_TYP_CNCT_PRPS)
        self.assertEqual(w.__unicode__(), w.NM_TYP_CNCT_PRPS)


class ContactMethodTypeModelTest(TestCase):
    '''Contact Method Type Model Test'''

    def create_cnct_mth_typ(self, CD_TYP_CNCT_MTH="CM", NM_TYP_CNCT_MTH="CM"):
        '''Create contact method type model'''
        return ContactMethodType.objects.create(
            CD_TYP_CNCT_MTH=CD_TYP_CNCT_MTH, NM_TYP_CNCT_MTH=NM_TYP_CNCT_MTH)

    def test_cnct_mth_typ(self):
        '''Test contact method type creation'''
        w = self.create_cnct_mth_typ()
        self.assertTrue(isinstance(w, ContactMethodType))
        self.assertEqual(w.__str__(), w.NM_TYP_CNCT_MTH)
        self.assertEqual(w.__unicode__(), w.NM_TYP_CNCT_MTH)


class ITUCountryModelTest(TestCase):
    '''ITU Country Model Test'''

    def create_itu_cy_cd(self, NM_CY_ITU="Country Name India"):
        '''Create ITU country model'''
        count_obj = ITUCountry.objects.all().count()
        CD_CY_ITU = str(count_obj+1)
        return ITUCountry.objects.create(CD_CY_ITU=CD_CY_ITU, NM_CY_ITU=NM_CY_ITU)

    def test_itu_cy_cd(self):
        '''Test ITU Country creation'''
        w = self.create_itu_cy_cd()
        self.assertTrue(isinstance(w, ITUCountry))
        self.assertEqual(w.__unicode__(), w.NM_CY_ITU)
        self.assertEqual(w.__str__(), w.NM_CY_ITU)


class StateModelTest(TestCase):
    '''State Model Test'''

    def create_state(self, NM_ST="California", CD_ST="Cal-001"):
        '''Create state model'''
        itucountry_instance = ITUCountryModelTest.create_itu_cy_cd(self)
        return State.objects.create(NM_ST=NM_ST, CD_ST=CD_ST, CD_CY_ITU=itucountry_instance)

    def test_state(self):
        '''Test state creation'''
        w = self.create_state()
        self.assertTrue(isinstance(w, State))
        self.assertEqual(w.__unicode__(), w.NM_ST)


class TelephoneModelTest(ITUCountryModelTest, TestCase):
    '''Telephone Model Test '''

    def create_telephone(self, TA_PH="033", TL_PH="25578", PH_EXTN="123", PH_CMPL="+1 194-967-8238"):
        '''Create telephone model'''
        itu_instance = ITUCountryModelTest.create_itu_cy_cd(self)
        return Telephone.objects.create(CD_CY_ITU=itu_instance, TA_PH=TA_PH, TL_PH=TL_PH, PH_EXTN=PH_EXTN, PH_CMPL=PH_CMPL)

    def test_telephone(self):
        '''Test telephone creation'''
        w = self.create_telephone()
        self.assertTrue(isinstance(w, Telephone))
        self.assertEqual(w.__unicode__(), w.PH_CMPL)


class EmailAddressModelTest(TestCase):
    '''Email Address Model Test'''

    def create_email_address(self, EM_ADS_LOC_PRT="xyz", EM_ADS_DMN_PRT="@abc.in"):
        '''Create Email Address Model'''
        return EmailAddress.objects.create(EM_ADS_LOC_PRT=EM_ADS_LOC_PRT, EM_ADS_DMN_PRT=EM_ADS_DMN_PRT)

    def test_em_ads_create(self):
        '''Test email address create_email_address'''
        w = self.create_email_address()
        self.assertTrue(isinstance(w, EmailAddress))
        self.assertEqual(w.__unicode__(), w.EM_ADS_LOC_PRT)
        self.assertEqual(w.__str__(), 'xyz@abc.in')


class GeographicSegmentModelTest(TestCase):
    '''Geographic Segment Model Test'''

    def create_geo_sgmt(self, DE_GEO_SGMT_CLSFR="GeographicSegment Description"):
        '''Create geographic segment model'''
        return GeographicSegment.objects.create(DE_GEO_SGMT_CLSFR=DE_GEO_SGMT_CLSFR)

    def test_geo_sgmt_create(self):
        '''Test geographic segment creation'''
        w = self.create_geo_sgmt()
        self.assertTrue(isinstance(w, GeographicSegment))
        self.assertEqual(w.__unicode__(), w.DE_GEO_SGMT_CLSFR)


class ISO3166CountryModelTest(ITUCountryModelTest, TestCase):
    '''ISO3166 Country Model Test'''

    def create_iso03166_country(self, NM_CY="India", CD_ISO_3CHR_CY="IND"):
        '''Create iso3166 country '''
        count_obj = ISO3166_1Country.objects.all().count()
        CD_CY_ISO = count_obj + 1
        itu_instance = ITUCountryModelTest.create_itu_cy_cd(self)
        return ISO3166_1Country.objects.create(CD_CY_ISO=CD_CY_ISO, CD_CY_ITU=itu_instance, NM_CY=NM_CY, CD_ISO_3CHR_CY=CD_ISO_3CHR_CY)

    def test_iso3166_country_create(self):
        '''Test iso3166 country creation'''
        w = self.create_iso03166_country()
        self.assertTrue(isinstance(w, ISO3166_1Country))
        self.assertEqual(w.__unicode__(), w.NM_CY)
        self.assertEqual(w.__str__(), w.NM_CY)


class PostalCodeRefModelTest(ISO3166CountryModelTest, TestCase):
    '''Postal Code Reference Model Test'''

    def create_pstl_cd_ref(self, CD_PSTL="735301"):
        '''Create postal code referance'''
        iso_instance = ISO3166CountryModelTest.create_iso03166_country(self)
        return PostalCodeReference.objects.create(CD_PSTL=CD_PSTL, CD_CY_ISO=iso_instance)

    def test_pstl_cd_ref(self):
        '''Test postal code reference'''
        w = self.create_pstl_cd_ref()
        self.assertTrue(isinstance(w, PostalCodeReference))
        self.assertEqual(w.__unicode__(), w.CD_PSTL)


class ISO3166PrimarySubdivisionTypeModelTest(TestCase):
    '''ISO3166 Primary Subdivision Type Model Test'''

    def create_prmry_sub_typ(self, CD_ISO3166_CY_PRMRY_SBDVN_TYP="ISO3166_SUB", DE_ISO3166_CY_PRMRY_SBDVN_TYP="ISO3166_CountryPrimarySubdivisionDescription"):
        '''Create Primary Subdivision Type'''
        return ISO3166_2PrimarySubdivisionType.objects.create(CD_ISO3166_CY_PRMRY_SBDVN_TYP=CD_ISO3166_CY_PRMRY_SBDVN_TYP, DE_ISO3166_CY_PRMRY_SBDVN_TYP=DE_ISO3166_CY_PRMRY_SBDVN_TYP)

    def test_prmry_sub_typ(self):
        '''Test Primary Subdivision Type Creation'''
        w = self.create_prmry_sub_typ()
        self.assertTrue(isinstance(w, ISO3166_2PrimarySubdivisionType))
        self.assertEqual(w.__unicode__(), w.DE_ISO3166_CY_PRMRY_SBDVN_TYP)
        self.assertEqual(w.__str__(), w.CD_ISO3166_CY_PRMRY_SBDVN_TYP)


class ISO3166CountrySubdivisionModelTest(ISO3166CountryModelTest, ISO3166PrimarySubdivisionTypeModelTest, TestCase):
    '''ISO3166 Country Subdivision Model Test'''

    def create_cy_svdvn(self, CD_ISO3166_CY_PRMRY_SBDVN_TYP="ISO3166_SUB", DE_ISO3166_CY_PRMRY_SBDVN_TYP="ISO3166_CountryPrimarySubdivisionDescription"):
        '''Create Country Subdivision'''
        iso_cy_instance = ISO3166CountryModelTest.create_iso03166_country(self)

        iso_prmry_svdn_instance = ISO3166PrimarySubdivisionTypeModelTest.create_prmry_sub_typ(
            self)

        return ISO3166_2CountrySubdivision.objects.create(CD_ISO3166_CY_PRMRY_SBDVN_TYP=iso_prmry_svdn_instance, CD_CY_ISO=iso_cy_instance, ID_ISO_3166_2_CY_PRMRY_SBDVN=1, CD_ISO_3_CHR_CY="IND", NM_ISO_CY_PRMRY_SBDVN="ISOCountryPrimarySubDivisionName", CD_ISO_CY_PRMRY_SBDVN_ABBR_CD="SBDVN", DE_ISO_SBDVN_ALT_NM="ISOSubdivisionAlternateNameDescription", NM_ISO_CY="INDIA")

    def test_prmry_sub_typ(self):
        '''Test Country Subdivision creation'''
        w = self.create_cy_svdvn()
        self.assertTrue(isinstance(w, ISO3166_2CountrySubdivision))
        self.assertEqual(w.__unicode__(), w.NM_ISO_CY_PRMRY_SBDVN)
        self.assertEqual(w.__str__(), w.NM_ISO_CY_PRMRY_SBDVN)

#! Address Test Class


class AddressModelTest(GeographicSegmentModelTest, ISO3166CountrySubdivisionModelTest, PostalCodeRefModelTest, TestCase):
    '''Address Model Test'''

    def create_address(self, A1_ADS="Topsia", A2_ADS="Kolkata", A3_ADS="Kolkata", A4_ADS="Kolkata", CI_CNCT="Kolkata", ST_CNCT="West Bengal"):
        '''Create address'''
        geo_instance = GeographicSegmentModelTest.create_geo_sgmt(self)
        cy_svdvn_instance = ISO3166CountrySubdivisionModelTest.create_cy_svdvn(
            self)
        pstl_instance = PostalCodeRefModelTest.create_pstl_cd_ref(self)
        return Address.objects.create(A1_ADS=A1_ADS, A2_ADS=A2_ADS, CI_CNCT=CI_CNCT, ST_CNCT=ST_CNCT, ID_GEO_SGMT=geo_instance, ID_ISO_3166_2_CY_SBDVN=cy_svdvn_instance, ID_PSTL_CD=pstl_instance)

    def test_create_address(self):
        '''Test address creation'''
        w = self.create_address()
        self.assertTrue(isinstance(w, Address))
        self.assertEqual(w.__unicode__(), w.CI_CNCT)


class SocialNetworkTypeModelTest(TestCase):
    '''Social Network Type Model Test'''

    def create_scl_ntwrk_typ(self, DE_SCL_NTWRK_TYP="Social Network Type Description"):
        '''Create Social Network Type'''
        return SocialNetworkType.objects.create(DE_SCL_NTWRK_TYP=DE_SCL_NTWRK_TYP)

    def test_scl_ntwrk_typ(self):
        '''Test Social Network Type creation'''
        w = self.create_scl_ntwrk_typ()
        self.assertTrue(isinstance(w, SocialNetworkType))
        self.assertEqual(w.__unicode__(), w.DE_SCL_NTWRK_TYP)


class WebSiteModelTest(TestCase):
    '''WebSite Model Test'''

    def create_website(self, URI_HM_PG="Social Network Type Description", NM_WB_STE_BSN="Website Business Name", NM_WB_STE_TTL_TG="Website Tag Value", DE_WB_STE_MTA_DSCR_TG_VL="Meta Description Tag Value", NA_WB_STE_KYWRD_LST="WebSite Meta Keyword List Narrative"):
        '''Create Website'''
        return WebSite.objects.create(URI_HM_PG=URI_HM_PG, NM_WB_STE_BSN=NM_WB_STE_BSN, NM_WB_STE_TTL_TG=NM_WB_STE_TTL_TG, DE_WB_STE_MTA_DSCR_TG_VL=DE_WB_STE_MTA_DSCR_TG_VL, NA_WB_STE_KYWRD_LST=NA_WB_STE_KYWRD_LST)

    def test_create_website(self):
        '''Test website creation'''
        w = self.create_website()
        self.assertTrue(isinstance(w, WebSite))
        self.assertEqual(w.__unicode__(), w.NM_WB_STE_BSN)


class SocialNetworkServiceModelTest(SocialNetworkTypeModelTest, WebSiteModelTest, TestCase):
    '''Social Network Service Model Test'''

    def create_scl_ntwrk_service(self, NM_SCL_NTWRK="Facebook"):
        '''Create Social Network Service'''
        web_insatnce = WebSiteModelTest.create_website(self)
        scl_ntwrk_typ_instance = SocialNetworkTypeModelTest.create_scl_ntwrk_typ(
            self)
        return SocialNetworkService.objects.create(NM_SCL_NTWRK=NM_SCL_NTWRK, CD_SCL_NTWRK_TYP=scl_ntwrk_typ_instance, ID_WB_STE=web_insatnce)

    def test_scl_ntwrk_typ(self):
        '''Test Social Network Service'''
        w = self.create_scl_ntwrk_service()
        self.assertTrue(isinstance(w, SocialNetworkService))
        self.assertEqual(w.__unicode__(), w.NM_SCL_NTWRK)


class SocialNetworkHandleModelTest(SocialNetworkServiceModelTest, TestCase):
    '''Social Network Handle Model Test'''

    def create_scl_ntwrk_handle(self, ID_SCL_NTWRK_USR="Haranath"):
        '''Create Social Network Handle'''
        scl_ntwrk_instance = SocialNetworkServiceModelTest.create_scl_ntwrk_service(
            self)
        return SocialNetworkHandle.objects.create(ID_SCL_NTWRK_USR=ID_SCL_NTWRK_USR, ID_SCL_NTWRK=scl_ntwrk_instance)

    def test_scl_ntwrk_handle(self):
        '''Test Social Network Handle creation'''
        w = self.create_scl_ntwrk_handle()
        self.assertTrue(isinstance(w, SocialNetworkHandle))
        self.assertEqual(w.__unicode__(), w.ID_SCL_NTWRK_USR)


class ConsumerModelTest(PartyRoleAssgnModelTest, PartyModelTest, TestCase):
    '''Consumer Model Test'''

    def create_consumer(self, ID_CNS="NAVSOFT"):
        '''Create Consumer'''
        prty_instance = PartyModelTest.create_party(self)
        prty_ro_asgmt = PartyRoleAssgnModelTest.create_prty_role_assign(self)
        return Consumer.objects.create(ID_CNS=ID_CNS, ID_PRTY_RO_ASGMT=prty_ro_asgmt, ID_PRTY=prty_instance)

    def test_consumer(self):
        '''Test Consumer'''
        w = self.create_consumer()
        self.assertTrue(isinstance(w, Consumer))
        self.assertEqual(w.__unicode__(), w.ID_CNS)


# PartyContactMethod
class PartyContactMethodModelTest(SocialNetworkHandleModelTest, ContactMethodTypeModelTest, ContactPurposeTypeModelTest, PartyRoleAssgnModelTest, WebSiteModelTest, AddressModelTest, EmailAddressModelTest, TelephoneModelTest, TestCase):
    '''Party Contact Method Model Test'''

    def create_prty_cnct_mth(self, ID_LGE="ENG", NM_LGE="ENGLISH"):
        '''Create Party Contact Method'''
        cnct_prps_typ_instance = ContactPurposeTypeModelTest.create_cnct_prps_typ(
            self)
        cnct_mth_typ_instance = ContactMethodTypeModelTest.create_cnct_mth_typ(
            self)
        prty_ro_asgmt_inst = PartyRoleAssgnModelTest.create_prty_role_assign(
            self)
        scl_ntwrk_hndl_inst = SocialNetworkHandleModelTest.create_scl_ntwrk_handle(
            self)
        ads_instance = AddressModelTest.create_address(self)
        em_ads_instance = EmailAddressModelTest.create_email_address(self)
        ph_instance = TelephoneModelTest.create_telephone(self)
        web_instance = WebSiteModelTest.create_website(self)

        return PartyContactMethod.objects.create(CD_TYP_CNCT_PRPS=cnct_prps_typ_instance, CD_TYP_CNCT_MTH=cnct_mth_typ_instance, ID_PRTY_RO_ASGMT=prty_ro_asgmt_inst, ID_SCL_NTWRK_HNDL=scl_ntwrk_hndl_inst, DC_EF=timezone.now(), DC_EP=timezone.now(), ID_ADS=ads_instance, ID_EM_ADS=em_ads_instance, ID_PH=ph_instance, ID_WB_STE=web_instance)

    def test_prty_cnct_mth(self):
        '''Test party contact method creation'''
        w = self.create_prty_cnct_mth()
        self.assertTrue(isinstance(w, PartyContactMethod))
        self.assertEqual(w.__unicode__(), w.ID_PRTY_CNCT_MTH)


class LanguageModelTest(TestCase):
    '''Language Model Test'''

    def create_language(self, ID_LGE="E", NM_LGE="ENGLISH"):
        '''Create Language'''
        return Language.objects.create(ID_LGE=get_random_string(length=3), NM_LGE=NM_LGE)

    def test_create_language(self):
        '''Test Language creation'''
        w = self.create_language()
        self.assertTrue(isinstance(w, Language))
        self.assertEqual(w.__unicode__(), w.NM_LGE)


#! PERSON
class PersonModelTest(PartyModelTest, LanguageModelTest, TestCase):
    '''Person Model Test'''

    def create_person(self):
        '''Create Person'''
        prty_instance = PartyModelTest.create_party(self)
        lang_instance = LanguageModelTest.create_language(self)
        return Person.objects.create(ID_PRTY=prty_instance, ID_LGE=lang_instance)

    def test_create_person(self):
        '''Test person creation'''
        w = self.create_person()
        self.assertTrue(isinstance(w, Person))
        self.assertEqual(w.__unicode__(), w.FN_PRS)


class OperationalPartyModelTest(PartyRoleAssgnModelTest, TestCase):
    '''Operational Party Model Test '''

    def create_opr_prty(self, TY_PRTY_OPR="PR"):
        '''Create Operational Party'''
        prty_ro_asgmt = PartyRoleAssgnModelTest.create_prty_role_assign(self)
        return OperationalParty.objects.create(TY_PRTY_OPR=TY_PRTY_OPR, ID_PRTY_RO_ASGMT=prty_ro_asgmt)

    def test_create_opr_prty(self):
        '''Test Operational Party create'''
        w = self.create_opr_prty()
        self.assertTrue(isinstance(w, OperationalParty))
        self.assertEqual(w.__unicode__(), w.TY_PRTY_OPR)


class LegalOrganizationTypeModelTest(TestCase):
    '''Legal Organization Type Model Test'''

    def create_lgl_org_typ(self, CD_LGL_ORGN_TYP="LG_ORG_TYP", DE_LGL_ORGN_TYP="Legal Organization Type Description"):
        '''Create Legal Organization Type'''
        return LegalOrganizationType.objects.create(CD_LGL_ORGN_TYP=CD_LGL_ORGN_TYP, DE_LGL_ORGN_TYP=DE_LGL_ORGN_TYP)

    def test_lgl_org_typ(self):
        '''Test Legal Organization Type creation'''
        w = self.create_lgl_org_typ()
        self.assertTrue(isinstance(w, LegalOrganizationType))
        self.assertEqual(w.__unicode__(), w.DE_LGL_ORGN_TYP)


class OrganizationModelTest(PartyModelTest, LegalOrganizationTypeModelTest, LanguageModelTest, TestCase):
    '''Organization Model Test'''

    def create_organization(self):
        '''Create Organization'''
        org_object = {"NM_LGL": "NAVSOFT", "NM_TRD": "Trade Name", "NM_JRDT_OF_INCRP": "", "MO_LCL_ANN_RVN": 2.4, "MO_GBL_ANN_RVN": 5.5, "ID_DUNS_NBR": "134", "CD_BNKRPTY_TYP": "321", "QU_EM_CNT_LCL": 100, "QU_EM_CNT_GBL": 200, "CD_RTG_DUNN_AND_BRDST": "5",
                      "NA_DE_ORGN": "", "DC_INCRP": timezone.now(), "DC_FSC_YR_END": timezone.now(), "DC_TRMN": timezone.now(), "DC_OPN_FR_BSN":  timezone.now(), "DC_CLSD_FR_BSN": timezone.now(), "DC_BNKRPTY": timezone.now(), "DC_BNKRPTY_EMRGNC": timezone.now()}
        prty_instance = PartyModelTest.create_party(self)
        lang_instance = LanguageModelTest.create_language(self)
        return Organization.objects.create(ID_PRTY=prty_instance, ID_LGE_PRMRY=lang_instance, **org_object)

    def test_create_organization(self):
        '''Test Organization creation'''
        w = self.create_organization()
        self.assertTrue(isinstance(w, Organization))
        self.assertEqual(w.__unicode__(), w.ID_ORGN)


class PartyIdentificationTypeModelTest(TestCase):
    '''Party Identification Type Model Test'''

    def create_prty_idn_type(self, DE_PRTY_ID="LG_ORG_TYP", TY_PRTY_ID="LA"):
        '''Create Party Identification Type'''
        return PartyIdentificationType.objects.create(DE_PRTY_ID=DE_PRTY_ID, TY_PRTY_ID=TY_PRTY_ID)

    def test_prty_idn_typ(self):
        '''Test party identification creation'''
        w = self.create_prty_idn_type()
        self.assertTrue(isinstance(w, PartyIdentificationType))
        self.assertEqual(w.__unicode__(), w.TY_PRTY_ID)


class ExtrnlPrtyIdenPrvdrModelTest(PartyRoleAssgnModelTest, TestCase):
    '''External Party Identification Provider Model Test'''

    def create_extrn_prvdr(self):
        '''Create External Party Identification Provider'''
        prty_ro_asgn_instance = PartyRoleAssgnModelTest.create_prty_role_assign(
            self)
        return ExternalPartyIdentificationProvider.objects.create(ID_PRTY_RO_ASGMT=prty_ro_asgn_instance)

    def test_create_extrn_prvdr(self):
        '''Test External Party Identification Provider creation'''
        w = self.create_extrn_prvdr()
        self.assertTrue(isinstance(w, ExternalPartyIdentificationProvider))
        self.assertEqual(w.__unicode__(), w.ID_PA_PVR_EXTRN)


class PartyIdentificationModelTest(ExtrnlPrtyIdenPrvdrModelTest, PartyIdentificationTypeModelTest, AddressModelTest, PersonModelTest, PartyModelTest, TestCase):
    '''Party Identification Model Test'''

    def create_lgl_org_typ(self):
        '''Create Party Identification'''
        party_instance = PartyModelTest.create_party(self)
        prty_iden_typ_instance = PartyIdentificationTypeModelTest.create_prty_idn_type(
            self)
        person_instance = PersonModelTest.create_person(self)
        ads_instance = AddressModelTest.create_address(self)
        extrn_prvr_instance = ExtrnlPrtyIdenPrvdrModelTest.create_extrn_prvdr(
            self)
        return PartyIdentification.objects.create(ID_PRTY=party_instance, TY_PRTY_ID=prty_iden_typ_instance, DT_EF=timezone.now(), ID_PRTY_PRS=person_instance, ID_ADS=ads_instance, ID_PA_PVR_EXTRN=extrn_prvr_instance, LU_ID_PRTY=1, DC_ISS=timezone.now(), DC_ID_PRTY_EP=timezone.now())

    def test_lgl_org_typ(self):
        '''Test Party Identification creation'''
        w = self.create_lgl_org_typ()
        self.assertTrue(isinstance(w, PartyIdentification))
        self.assertEqual(w.__unicode__(), w.ID_PA_IDTN)
