''' Supplier Filter File '''
import logging
import json
from copy import deepcopy
from django.db.models import Q
from django.db.models.functions import Concat
from django.db.models import Value, CharField
from django.contrib.auth.models import User
from color.color_filter import get_user_details
from party.manufacturer_serializers import ManufacturerListSerializer
from party.supplier_serializers import SupplierListSerializer
from party.models import EmailAddress, Organization, PartyContactMethod, Person
from worker.models import Manufacturer, Supplier
from size.common_date_filter_file import common_date_filter_query
from size.size_filter import separate_value
from color.filter_ordering_by_user import order_by_crt_by_nm

logger = logging.getLogger(__name__)


def supplier_filter_columns(filterquery, i, filter_type, filter_val):
    '''Supplier filter by columns'''
    organisation_obj = Organization.objects.filter(
        **{'NM_TRD' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)
    if i == 'TYP_PRTY':
        filterquery.add(
            Q(**{'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__ID_PRTY_TYP__DE_PRTY_TYP' +
              str(filter_type): filter_val}),
            Q.AND)
    elif i == 'NM_SPR' or i == 'NM_MF':
        if organisation_obj.exists():
            filterquery.add(Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(
                **{'NM_TRD' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
                Q.AND)
        else:
            filterquery.add(Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Person.objects.annotate(
                person_name=Concat('FN_PRS', Value(' '), 'LN_PRS')).filter(
                **{'person_name' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
                Q.AND)
    elif i == 'NM_LGL':
        filterquery.add(Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(
            **{'NM_LGL' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
            Q.AND)
    elif i == 'EM_ADS':
        email_id = EmailAddress.objects.annotate(Email=Concat(
            'EM_ADS_LOC_PRT', Value('@'), 'EM_ADS_DMN_PRT', output_field=CharField())).filter(
            **{'Email__in': str(filter_val).split(',')}).exclude(EM_ADS_LOC_PRT__exact='',
                                                                 EM_ADS_DMN_PRT__exact='').values_list(
            'ID_EM_ADS', flat=True)
        getemail = PartyContactMethod.objects.filter(
            Q(ID_EM_ADS__in=email_id) & Q(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=False) & Q(
                ID_EM_ADS__EM_ADS_DMN_PRT__isnull=False) & Q(
                CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
        filterquery.add(Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=getemail),
                        Q.AND)
    elif i == 'NM_TRD':
        filterquery.add(Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(
            **{'NM_TRD' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
            Q.AND)
    elif i == 'PH_CMPL':
        filterquery.add(Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=PartyContactMethod.objects.filter(
            **{'ID_PH__PH_CMPL__in': str(filter_val).split(',')},
            CD_STS='A').values_list('ID_PRTY_RO_ASGMT', flat=True)),
            Q.AND)
    return filterquery


def create_supplier_filter_query_filtertype_is_not(filterquery, filter_type, i, filter_val):
    '''Create a filter query'''
    org = Organization.objects.filter(
        **{'NM_TRD' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)
    if i == 'TYP_PRTY':
        filterquery.add(
            ~Q(**{'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__ID_PRTY_TYP__DE_PRTY_TYP' +
                  str(filter_type): filter_val}),
            Q.AND)
    elif i == 'NM_SPR' or i == 'NM_MF':
        if org.exists():
            filterquery.add(~Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(
                **{'NM_TRD' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
                Q.AND)
        else:
            filterquery.add(~Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Person.objects.annotate(
                person_name=Concat('FN_PRS', Value(' '), 'LN_PRS')).filter(
                **{'person_name' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
                Q.AND)
    elif i == 'NM_LGL':
        filterquery.add(~Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(
            **{'NM_LGL' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
            Q.AND)
    elif i == 'EM_ADS':
        email_ids = EmailAddress.objects.annotate(Email=Concat(
            'EM_ADS_LOC_PRT', Value('@'), 'EM_ADS_DMN_PRT', output_field=CharField())).filter(
            **{'Email__in': str(filter_val).split(',')}).exclude(EM_ADS_LOC_PRT__exact='',
                                                                 EM_ADS_DMN_PRT__exact='').values_list(
            'ID_EM_ADS', flat=True)
        get_email = PartyContactMethod.objects.filter(
            Q(ID_EM_ADS__in=email_ids) & Q(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=False) & Q(
                ID_EM_ADS__EM_ADS_DMN_PRT__isnull=False) & Q(
                CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
        filterquery.add(~Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=get_email),
                        Q.AND)
    elif i == 'NM_TRD':
        filterquery.add(~Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(
            **{'NM_TRD' + str(filter_type): filter_val}).values_list('ID_PRTY', flat=True)),
            Q.AND)
    elif i == 'PH_CMPL':
        filterquery.add(~Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=PartyContactMethod.objects.filter(
            **{'ID_PH__PH_CMPL__in': str(filter_val).split(',')},
            CD_STS='A').values_list('ID_PRTY_RO_ASGMT', flat=True)),
            Q.AND)
    else:
        filterquery.add(
            ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery


def supplier_filter_query(filterquery, i, filter_type, filter_val):
    '''Supplier Filter query for a filter'''
    field_list = ['TYP_PRTY', 'NM_SPR',
                  'NM_LGL', 'NM_TRD', 'PH_CMPL', 'EM_ADS', 'NM_MF']
    if i == 'CRT_BY_NM' or i == 'MDF_BY_NM':
        i = i.replace('CRT_BY_NM', 'CRT_BY')
        i = i.replace('MDF_BY_NM', 'MDF_BY')
        get_user_details(filter_type, filterquery, i, filter_val)
        return filterquery
    if i == 'MDF_DT' or i == 'CRT_DT':
        return common_date_filter_query(filter_type, i, filter_val, filterquery)
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        create_supplier_filter_query_filtertype_is_not(
            filterquery, filter_type, i, filter_val)
    else:
        filter_type = filter_type.replace(
            'end-with', '__iendswith')
        filter_type = filter_type.replace(
            'contains', '__icontains')
        filter_type = filter_type.replace(
            'start-with', '__istartswith')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        filter_type = filter_type.replace(
            'greater-than', '__gt')
        if i in field_list:
            supplier_filter_columns(filterquery, i, filter_type, filter_val)
        else:
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery


def ordering_supplier_manufacturer(ordering):
    '''Common function of ordering for Vendor & Manufacturer'''
    ordering = ordering.replace(
        'TYP_PRTY', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__ID_PRTY_TYP__DE_PRTY_TYP')
    ordering = ordering.replace(
        '-TYP_PRTY', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__ID_PRTY_TYP__DE_PRTY_TYP')
    ordering = ordering.replace(
        'NM_LGL', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_LGL')
    ordering = ordering.replace(
        '-NM_LGL', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_LGL')
    ordering = ordering.replace(
        'NM_TRD', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_TRD')
    ordering = ordering.replace(
        '-NM_TRD', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_TRD')
    ordering = ordering.replace('PH_CMPL', 'ID_SPR')
    ordering = ordering.replace('-PH_CMPL', '-ID_SPR')
    ordering = ordering.replace('EM_ADS', 'ID_SPR')
    ordering = ordering.replace('-EM_ADS', '-ID_SPR')
    if ordering == 'NM_SPR':
        ordering1 = ordering.replace(
            'NM_SPR', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__FN_PRS')
        ordering2 = ordering.replace(
            'NM_SPR', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__LN_PRS')
        ordering3 = ordering.replace(
            'NM_SPR', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_TRD')
        ordering = [ordering1, ordering2, ordering3]
    if ordering == '-NM_SPR':
        ordering1 = ordering.replace(
            '-NM_SPR', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__FN_PRS')
        ordering2 = ordering.replace(
            '-NM_SPR', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__LN_PRS')
        ordering3 = ordering.replace(
            '-NM_SPR', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_TRD')
        ordering = [ordering1, ordering2, ordering3]
    if ordering == 'NM_MF':
        ordering1 = ordering.replace(
            'NM_MF', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__FN_PRS')
        ordering2 = ordering.replace(
            'NM_MF', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__LN_PRS')
        ordering3 = ordering.replace(
            'NM_MF', 'ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_TRD')
        ordering = [ordering1, ordering2, ordering3]
    if ordering == '-NM_MF':
        ordering1 = ordering.replace(
            '-NM_MF', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__FN_PRS')
        ordering2 = ordering.replace(
            '-NM_MF', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__LN_PRS')
        ordering3 = ordering.replace(
            '-NM_MF', '-ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__organization_party_id__NM_TRD')
        ordering = [ordering1, ordering2, ordering3]
    ordering = order_by_crt_by_nm(ordering)
    return ordering


def create_supplier_manufacturer_search_query(filterquery, search, module_name):
    '''Supplier and manufacturer search query'''
    if module_name == 'supplier':
        column_supplier_manufacturer = {
            'CD_SPR__icontains': search
        }
    else:
        column_supplier_manufacturer = {
            'CD_MF__icontains': search
        }
    email_id = EmailAddress.objects.annotate(Email=Concat(
        'EM_ADS_LOC_PRT', Value('@'), 'EM_ADS_DMN_PRT', output_field=CharField())).filter(
        Email__icontains=search).exclude(EM_ADS_LOC_PRT__exact='', EM_ADS_DMN_PRT__exact='').values_list(
        'ID_EM_ADS', flat=True)
    getemail = PartyContactMethod.objects.filter(
        Q(ID_EM_ADS__in=email_id) & Q(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=False) & Q(
            ID_EM_ADS__EM_ADS_DMN_PRT__isnull=False) & Q(
            CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
    filterquery.add(
        Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__ID_PRTY_TYP__DE_PRTY_TYP__icontains=search) |
        Q(**column_supplier_manufacturer) |
        Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(NM_LGL__icontains=search).values_list(
            'ID_PRTY', flat=True)) |
        Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(NM_TRD__icontains=search).values_list(
            'ID_PRTY', flat=True)) |
        Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=PartyContactMethod.objects.filter(
            ID_PH__PH_CMPL__icontains=search,
            CD_STS='A').values_list('ID_PRTY_RO_ASGMT', flat=True)) |
        Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=getemail) |
        Q(CRT_DT__date__icontains=search) |
        Q(MDF_DT__date__icontains=search) |
        Q(CRT_BY__in=User.objects.annotate(full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())).filter(
            full_name__icontains=search).values_list('id', flat=True)) |
        Q(MDF_BY__in=User.objects.annotate(full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())).filter(
            full_name__icontains=search).values_list('id', flat=True)) |
        Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Person.objects.annotate(
            person_name=Concat('FN_PRS', Value(' '), 'LN_PRS')).filter(person_name__icontains=search).values_list(
            'ID_PRTY', flat=True)) |
        Q(ID_VN__ID_PRTY_RO_ASGMT__ID_PRTY__in=Organization.objects.filter(NM_TRD__icontains=search).values_list(
            'ID_PRTY', flat=True)), Q.AND)
    return filterquery


def get_data_supp_manu_from_filter_query(filterquery, request_data, flags):
    ''''''
    for i in request_data:
        separate_values = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        if len(separate_values[0]) > 0:
            if separate_values[1] in condition_list:
                supplier_filter_query(
                    filterquery, i, separate_values[1], separate_values[0])
            else:
                flags = False
                break
    return filterquery, flags


def perform_supplier_filter_query(excludes_ids, filterquery, ordering, new_ordering, ordering_list_name, offset, limit):
    '''Perform supplier filter query'''
    if excludes_ids:
        excludes_ids = json.loads(excludes_ids)
        supplier_data = Supplier.objects.filter(
            Q(filterquery)).exclude(ID_SPR__in=excludes_ids).order_by(ordering)
    else:
        if new_ordering in ordering_list_name:
            supplier_data = Supplier.objects.filter(
                Q(filterquery)).order_by(*ordering)
        else:
            supplier_data = Supplier.objects.filter(
                Q(filterquery)).order_by(ordering)
    count = supplier_data.count()
    paginated_data = supplier_data[offset:offset + limit]
    response_data = SupplierListSerializer(
        paginated_data, many=True).data
    return response_data, count


def perform_manufacturer_filter_query(excludes_ids, filterquery, ordering, new_ordering, ordering_list_name, offset, limit):
    '''Perform manufacturer filter query'''
    if excludes_ids:
        excludes_ids = json.loads(excludes_ids)
        manufacturer_data = Manufacturer.objects.filter(
            Q(filterquery)).exclude(ID_MF__in=excludes_ids).order_by(ordering)
    else:
        if new_ordering in ordering_list_name:
            manufacturer_data = Manufacturer.objects.filter(
                Q(filterquery)).order_by(*ordering)
        else:
            manufacturer_data = Manufacturer.objects.filter(
                Q(filterquery)).order_by(ordering)
    count = manufacturer_data.count()
    paginated_data = manufacturer_data[offset:offset + limit]
    response_data = ManufacturerListSerializer(
        paginated_data, many=True).data
    return response_data, count


def perform_supplier_manufacturer_ordering(ordering, ordering_list, module_name, ordering_list_name):
    '''Perform supplier & manufacturer ordering'''
    if (ordering in ordering_list or ordering is None or ordering is not None) and module_name == 'manufacturer':
        ordering_list_name = ['NM_SPR', '-NM_SPR', 'CRT_BY_NM',
                              '-CRT_BY_NM', 'MDF_BY_NM', '-MDF_BY_NM', 'NM_MF', '-NM_MF']
        if ordering is not None and ordering != '':
            if ordering == 'PH_CMPL' or ordering == '-PH_CMPL' or ordering == 'EM_ADS' or ordering == '-EM_ADS':
                ordering = ordering.replace('PH_CMPL', 'ID_MF')
                ordering = ordering.replace('-PH_CMPL', '-ID_MF')
                ordering = ordering.replace('EM_ADS', 'ID_MF')
                ordering = ordering.replace('-EM_ADS', '-ID_MF')
            else:
                ordering = ordering_supplier_manufacturer(ordering)
        else:
            ordering = '-ID_MF'
    return ordering, ordering_list_name


def supplier_filter(module_name, page, page_size, search=None, request_data=None, ordering=None, excludes_ids=None):
    '''Supplier Filter'''
    if search == '':
        search = None
    filterquery = Q()
    limit = int(page_size)
    page = int(page)
    offset = (page - 1) * limit
    flags = True
    if request_data is not None:
        filterquery, flags = get_data_supp_manu_from_filter_query(
            filterquery, request_data, flags)
    if search is not None:
        create_supplier_manufacturer_search_query(
            filterquery, search, module_name)
    ordering_list = ['PH_CMPL',
                     'EM_ADS', '-PH_CMPL', '-EM_ADS']
    new_ordering = deepcopy(ordering)
    ordering_list_name = []
    if (ordering in ordering_list or ordering is None or ordering is not None) and module_name == 'supplier':
        ordering_list_name = ['NM_SPR', '-NM_SPR', 'CRT_BY_NM',
                              '-CRT_BY_NM', 'MDF_BY_NM', '-MDF_BY_NM', 'NM_MF', '-NM_MF']
        if ordering is not None and ordering != '':
            ordering = ordering_supplier_manufacturer(ordering)
        else:
            ordering = '-ID_SPR'
    ordering, ordering_list_name = perform_supplier_manufacturer_ordering(
        ordering, ordering_list, module_name, ordering_list_name)
    logger.info("Filter Query : %s", filterquery)

    # logger.info("Exclude Ids: %s", len(excludes_ids))
    if flags:
        if module_name == 'supplier':
            response_data, count = perform_supplier_filter_query(
                excludes_ids, filterquery, ordering, new_ordering, ordering_list_name, offset, limit)
        else:
            response_data, count = perform_manufacturer_filter_query(
                excludes_ids, filterquery, ordering, new_ordering, ordering_list_name, offset, limit)
    else:
        count = 0
        response_data = []
    return response_data, count
