''' Contact Details Swagger Schema '''
from drf_yasg import openapi

address_line_1_value = 'Address Line 1'


def get_contact_details_schema():
    ''' Get Contact Details Schema '''
    contact_details = openapi.Schema(
        type=openapi.TYPE_ARRAY, description='Contact Details',
        items=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'A1_ADS': openapi.Schema(type=openapi.TYPE_STRING,
                                         description=address_line_1_value),
                'A2_ADS': openapi.Schema(type=openapi.TYPE_STRING,
                                         description='Address Line 2'),
                'CD_CY_ITU': openapi.Schema(type=openapi.TYPE_STRING,
                                            description='Country Code'),
                'CD_PSTL': openapi.Schema(type=openapi.TYPE_STRING,
                                          description='Postal Code'),
                'CD_STS': openapi.Schema(type=openapi.TYPE_STRING,
                                         description='Status (A/I)'),
                'CD_TYP_CNCT_MTH': openapi.Schema(type=openapi.TYPE_STRING,
                                                  description="Contact Method"),
                'CD_TYP_CNCT_PRPS': openapi.Schema(type=openapi.TYPE_STRING,
                                                   description="Contact Purpose"),
                'CI_CNCT': openapi.Schema(type=openapi.TYPE_STRING,
                                          description='City Name'),
                'EM_ADS': openapi.Schema(type=openapi.TYPE_STRING,
                                         description='Email Address'),
                'ID_ST': openapi.Schema(type=openapi.TYPE_INTEGER,
                                        description='State Id'),
                'ST_CNCT': openapi.Schema(type=openapi.TYPE_STRING,
                                          description='State Name (Like - Idaho)'),
                'PH_CMPL': openapi.Schema(type=openapi.TYPE_STRING,
                                          PH_CMPLdescription='Phone Number'),
                'IS_SHIPPING': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                              description='Is Default Shipping Address?'),
                'IS_BILLING': openapi.Schema(type=openapi.TYPE_BOOLEAN,
                                             description='Is Default Billing Address?')
            }
        ))
    return contact_details
