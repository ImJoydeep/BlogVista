'''Crate Filter'''
from copy import deepcopy

from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models.functions import Concat
from django.db.models import Value, CharField
from color.filter_ordering_by_user import ordering_by_crt_by
from size.common_date_filter_file import common_date_filter_query
from store.models import Location
from order.serializers import CratesSerializer, ReasonSerializer
from order.models import Crates, OrderCrates, Reason
from size.size_filter import retrieve_user_details, separate_value
from datetime import datetime
from order.models import AssociateCrate


def filter_query(filterquery, i, filter_type, filter_val):
    '''Filter query for a filter'''
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        if i == 'STR_ASGN':
            filterquery.add(
                ~Q(CRT_ID__in=list(AssociateCrate.objects.filter(
                    Q(**{"STR_ID__NM_LCN"+str(filter_type): filter_val}) & Q(**{"STR_ID__CD_LCN_TYP__DE_LCN_TYP"+str(filter_type): "STR"})).values_list('CRT_ID', flat=True))), Q.AND
            )
        elif i == 'CLRS':
            filterquery.add(
                ~Q(**{'CLRS__NM_CLR'+str(filter_type): filter_val}), Q.AND
            )
        else:
            filterquery.add(
                ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND
            )
        return filterquery
    else:
        filter_type = filter_type.replace(
            'start-with', '__istartswith')
        filter_type = filter_type.replace(
            'contains', '__icontains')
        filter_type = filter_type.replace(
            'end-with', '__iendswith')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        filter_type = filter_type.replace(
            'greater-than', '__gt')
        if i == 'STR_ASGN':
            filterquery.add(Q(CRT_ID__in=list(AssociateCrate.objects.filter(
                Q(**{"STR_ID__NM_LCN"+str(filter_type): filter_val}) & Q(**{"STR_ID__CD_LCN_TYP__DE_LCN_TYP"+str(filter_type): "STR"})).values_list('CRT_ID', flat=True))), Q.AND)
        elif i == 'BR_CD':
            filterquery.add(Q(**{'BR_CD'+str(filter_type): filter_val}), Q.AND)
        elif i == 'CRT_CD':
            filterquery.add(
                Q(**{'CRT_CD'+str(filter_type): filter_val}), Q.AND)
        elif i == 'CLRS':
            filterquery.add(
                Q(**{'CLRS__NM_CLR'+str(filter_type): filter_val}), Q.AND)
        elif i == 'STR_NM':
            filterquery.add(
                Q(CRT_ID__in=AssociateCrate.objects.filter(STR_ID__in=Location.objects.filter(Q(Q(MAG_MAGEWORX_STR_NM__iexact=filter_val) | Q(NM_LCN__iexact=filter_val))).values_list('id', flat=True)).values_list('CRT_ID', flat=True)), Q.AND)
            filterquery.add(~Q(CRT_ID__in=OrderCrates.objects.filter(AC_ID__in=AssociateCrate.objects.filter(STR_ID__in=Location.objects.filter(
                Q(Q(MAG_MAGEWORX_STR_NM__iexact=filter_val) | Q(NM_LCN__iexact=filter_val))).values_list('id', flat=True)).values_list('AC_ID', flat=True)).values_list('AC_ID__CRT_ID', flat=True)), Q.AND)
            filterquery.add(Q(CRT_STS="A"), Q.AND)
        else:
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND
            )
    return filterquery


def get_data_for_cartes_filter(filterquery, request_data, flags):
    '''Retrieve data for position filterquery'''
    for i in request_data:
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        separate_values = separate_value(request_data, i)
        if len(separate_values[0]) > 0:

            if separate_values[1] in condition_list:
                filter_query(filterquery, i, separate_values[1], separate_values[0]
                             )
            else:
                flags = False
                break
    return filterquery, flags


def crates_filter(page, page_size, search=None, request_data=None):
    '''Crates Filter'''
    filterquery = Q()
    flags = True
    if search == '':
        search = None
    if request_data is not None:
        filterquery, flags = get_data_for_cartes_filter(
            filterquery, request_data, flags)
    if search is not None:
        filterquery.add(
            Q(CRT_CD__icontains=search) |
            Q(BR_CD__icontains=search) |
            Q(DES__icontains=search) |
            Q(MTRL_TYPE__icontains=search) |
            Q(CLRS__NM_CLR__icontains=search) |
            Q(CRT_ID__in=list(AssociateCrate.objects.filter(
                Q(STR_ID__NM_LCN__icontains=search)).values_list('CRT_ID', flat=True))),
            Q.AND
        )
    if flags == True:
        count_obj = Crates.objects.filter(
            Q(filterquery)).count()
        limit = int(page_size)
        page = int(page)
        offset = (page - 1) * limit
        position_data = Crates.objects.filter(
            Q(filterquery)).order_by('-CRT_ID')
        position_ordered_data = position_data[offset:offset + limit]
        response_data = CratesSerializer(
            position_ordered_data, many=True).data
    else:
        count_obj = 0
        response_data = []
    return response_data, count_obj


def reason_filter_query(filterquery, i, filter_type, filter_val):
    '''Filter query for Reason Code Filter'''
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        filterquery.add(~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        return filterquery
    else:
        filter_type = filter_type.replace(
            'start-with', '__istartswith')
        filter_type = filter_type.replace(
            'end-with', '__iendswith')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace(
            'contains', '__icontains')
        filter_type = filter_type.replace(
            'greater-than', '__gt')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filterquery.add(Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery


def reason_get_data_for_cartes_filter(filterquery, request_data, flags):
    '''Retrieve data for position filterquery'''
    for i in request_data:
        separate_val = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        if len(separate_val[0]) > 0:
            if separate_val[1] in condition_list:
                reason_filter_query(
                    filterquery, i, separate_val[1], separate_val[0])
            else:
                flags = False
                break
    return filterquery, flags


def reason_filter(page, page_size, search=None, request=None):
    '''Reason Filter'''
    filterquery = Q()
    if search == '':
        search = None
    flags = True
    if request is not None:
        filterquery, flags = reason_get_data_for_cartes_filter(
            filterquery, request, flags)
    if search is not None:
        filterquery.add(
            Q(RN_CD__icontains=search) |
            Q(RN_STD__icontains=search),
            Q.AND
        )
    if flags == True:
        count_obj = Reason.objects.filter(
            Q(filterquery)).count()
        page = int(page)
        limit = int(page_size)
        position_data = Reason.objects.filter(
            Q(filterquery)).order_by('-RN_ID')
        offset = (page - 1) * limit
        position_ordered_data = position_data[offset:offset + limit]
        response_data = ReasonSerializer(position_ordered_data, many=True).data
    else:
        count_obj = 0
        response_data = []
    return response_data, count_obj
