'''Invoice Filter'''
from copy import deepcopy

from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models.functions import Concat
from django.db.models import Value, CharField
from color.filter_ordering_by_user import ordering_by_crt_by
from style.style_filter import separate_value
from order.models import Customer, OrderInvoice, OrderMaster
from order.serializers_invoice import GetOrderInvoiceListSerializer


def get_query_for_not_query_customer_and_order_date(filter_val, filter_type, filterquery, i):
    '''Get filterquery for customer name and order date'''
    if i == 'CUST_NM':
        customer_fullname_query = Q()
        if len(filter_val.split(' ')) > 1:
            customer_fullname_query.add(
                Q(**{'CUST_FNM' + str(filter_type): str(filter_val).split(' ')[0]}) &
                Q(**{'CUST_LNM' + str(filter_type)                  : str(filter_val).split(' ')[1]}),
                Q.AND
            )
        else:
            customer_fullname_query.add(
                Q(**{'CUST_FNM' + str(filter_type)                  : str(filter_val).split(' ')[0]}),
                Q.AND
            )
        filterquery.add(~Q(OD_INVOE_OD_ID__OD_CUST__in=Customer.objects.filter(
            customer_fullname_query).values_list('id', flat=True)),
            Q.AND)
    elif i == 'OD_DATE':
        filterquery.add(
            ~Q(**{'OD_INVOE_OD_ID__OD_DATE__icontains': filter_val}), Q.AND)
    return filterquery


def get_query_for_not_query_of_customer_name_and_order_date(i, filter_type, filter_val, filterquery):
    '''Get not query for customer name and order date'''
    if i == 'CUST_NM':
        customer_name_query = Q()
        if len(filter_val.split(' ')) > 1:
            customer_name_query.add(
                Q(**{'CUST_FNM' + str(filter_type): str(filter_val).split(' ')[0]}) &
                Q(**{'CUST_LNM' + str(filter_type)
                  : str(filter_val).split(' ')[1]}),
                Q.AND
            )
        else:
            customer_name_query.add(
                Q(**{'CUST_FNM' + str(filter_type)
                  : str(filter_val).split(' ')[0]}),
                Q.AND
            )
        filterquery.add(Q(OD_INVOE_OD_ID__OD_CUST__in=Customer.objects.filter(
            customer_name_query).values_list('id', flat=True)),
            Q.AND)
    elif i == 'OD_DATE':
        if filter_type in ['__lt', '__gte']:
            filterquery.add(
                Q(**{'OD_INVOE_OD_ID__OD_DATE' + str(filter_type): filter_val}), Q.AND)
        else:
            filterquery.add(
                Q(**{'OD_INVOE_OD_ID__OD_DATE__icontains': filter_val}), Q.AND)
    return filterquery


def invoice_filter_query(filterquery, i, filter_type, filter_val):
    '''Invoice filter query'''
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        if i in ['CUST_NM', 'OD_DATE']:
            filterquery = get_query_for_not_query_customer_and_order_date(
                filter_val, filter_type, filterquery, i)
        else:
            i = i.replace('CU_OD_ID', 'OD_INVOE_OD_ID__CU_OD_ID')
            i = i.replace('OD_TL_AMT', 'OD_INVOE_OD_ID__OD_TL_AMT')
            i = i.replace('OD_TX_AMT', 'OD_INVOE_OD_ID__OD_TX_AMT')
            i = i.replace('OD_DATE', 'OD_INVOE_OD_ID__OD_DATE')
            i = i.replace('OD_SHP_AMT', 'OD_INVOE_OD_ID__OD_SHP_AMT')
            i = i.replace('OD_NT_AMT', 'OD_INVOE_OD_ID__OD_NT_AMT')
            i = i.replace('OD_STR_NM', 'OD_INVOE_OD_ID__OD_STR_NM')
            filterquery.add(
                ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        return filterquery
    else:
        filter_type = filter_type.replace(
            'end-with', '__iendswith')
        filter_type = filter_type.replace(
            'greater-than', '__gt')
        filter_type = filter_type.replace(
            'start-with', '__istartswith')
        filter_type = filter_type.replace(
            'contains', '__icontains')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        if i in ['CUST_NM', 'OD_DATE']:
            filterquery = get_query_for_not_query_of_customer_name_and_order_date(
                i, filter_type, filter_val, filterquery)
        else:
            i = i.replace('CU_OD_ID', 'OD_INVOE_OD_ID__CU_OD_ID')
            i = i.replace('OD_DATE', 'OD_INVOE_OD_ID__OD_DATE')
            i = i.replace('OD_STR_NM', 'OD_INVOE_OD_ID__OD_STR_NM')
            i = i.replace('OD_NT_AMT', 'OD_INVOE_OD_ID__OD_NT_AMT')
            i = i.replace('OD_TL_AMT', 'OD_INVOE_OD_ID__OD_TL_AMT')
            i = i.replace('OD_TX_AMT', 'OD_INVOE_OD_ID__OD_TX_AMT')
            i = i.replace('OD_SHP_AMT', 'OD_INVOE_OD_ID__OD_SHP_AMT')
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND)


def get_data_for_invoice_filter(filterquery, request_data, flags):
    '''Retrieve data for position filterquery'''
    for i in request_data:
        separate_values = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        if len(separate_values[0]) > 0:
            if separate_values[1] in condition_list:
                invoice_filter_query(
                    filterquery, i, separate_values[1], separate_values[0])
            else:
                flags = False
                break
    return filterquery, flags


def ordering_by_customer_name(ordering):
    '''Order by the CRT_BY'''
    if ordering == 'CUST_NM':
        ordering1 = ordering.replace(
            'CUST_NM', 'OD_INVOE_OD_ID__OD_CUST__CUST_FNM')
        ordering2 = ordering.replace(
            'CUST_NM', 'OD_INVOE_OD_ID__OD_CUST__CUST_LNM')
        ordering = [ordering1, ordering2]
    elif ordering == '-CUST_NM':
        ordering1 = ordering.replace(
            '-CUST_NM', '-OD_INVOE_OD_ID__OD_CUST__CUST_FNM')
        ordering2 = ordering.replace(
            '-CUST_NM', '-OD_INVOE_OD_ID__OD_CUST__CUST_LNM')
        ordering = [ordering1, ordering2]
    return ordering


def invoice_filter(page, page_size, search=None, request_data=None, ordering=None):
    '''Positon Filter'''
    if search == '':
        search = None
    filterquery = Q()
    flags = True
    if request_data is not None:
        filterquery, flags = get_data_for_invoice_filter(
            filterquery, request_data, flags)
    if search is not None:
        filterquery.add(
            Q(OD_INVOE_INCR_ID__icontains=search) |
            Q(OD_INVOE_OD_ID__CU_OD_ID__icontains=search) |
            Q(OD_INVOE_OD_ID__in=OrderMaster.objects.annotate(full_name=Concat(
                'OD_CUST__CUST_FNM', Value(' '), 'OD_CUST__CUST_LNM', output_field=CharField())).filter(full_name__icontains=search).values_list('OD_ID', flat=True)) |
            Q(OD_INVOE_OD_ID__OD_CUST__CUST_LNM__icontains=search) |
            Q(OD_INVOE_OD_ID__OD_DATE__icontains=search) |
            Q(OD_INVOE_OD_ID__OD_STR_NM__icontains=search) |
            Q(OD_INVOE_OD_ID__OD_TL_AMT__icontains=search) |
            Q(OD_INVOE_OD_ID__OD_SHP_AMT__icontains=search) |
            Q(OD_INVOE_OD_ID__OD_NT_AMT__icontains=search) |
            Q(OD_INVOE_OD_ID__OD_TX_AMT__icontains=search) |
            Q(OD_SHP_ID__OD_SHIP_CODE__icontains=search),
            Q.AND
        )
    ordering_copy_data = deepcopy(ordering)
    if ordering:
        ordering = ordering.replace('CU_OD_ID', 'OD_INVOE_OD_ID__CU_OD_ID')
        ordering = ordering.replace('OD_DATE', 'OD_INVOE_OD_ID__OD_DATE')
        ordering = ordering.replace('OD_STR_NM', 'OD_INVOE_OD_ID__OD_STR_NM')
        ordering = ordering.replace('OD_TL_AMT', 'OD_INVOE_OD_ID__OD_TL_AMT')
        ordering = ordering.replace('OD_TX_AMT', 'OD_INVOE_OD_ID__OD_TX_AMT')
        ordering = ordering.replace('OD_SHP_AMT', 'OD_INVOE_OD_ID__OD_SHP_AMT')
        ordering = ordering.replace('OD_NT_AMT', 'OD_INVOE_OD_ID__OD_NT_AMT')
        ordering = ordering.replace('-CU_OD_ID', '-OD_INVOE_OD_ID__CU_OD_ID')
        ordering = ordering.replace('-OD_DATE', '-OD_INVOE_OD_ID__OD_DATE')
        ordering = ordering.replace('-OD_STR_NM', '-OD_INVOE_OD_ID__OD_STR_NM')
        ordering = ordering.replace('-OD_TL_AMT', '-OD_INVOE_OD_ID__OD_TL_AMT')
        ordering = ordering.replace('-OD_TX_AMT', '-OD_INVOE_OD_ID__OD_TX_AMT')
        ordering = ordering.replace(
            '-OD_SHP_AMT', '-OD_INVOE_OD_ID__OD_SHP_AMT')
        ordering = ordering.replace('-OD_NT_AMT', '-OD_INVOE_OD_ID__OD_NT_AMT')
        ordering = ordering_by_customer_name(ordering)
    else:
        ordering = '-OD_INVOE_ID'
    if flags == True:
        limit = int(page_size)
        page = int(page)
        offset = (page - 1) * limit
        if ordering_copy_data in ['CUST_NM', '-CUST_NM']:
            invoice_data = OrderInvoice.objects.filter(
                Q(filterquery)).order_by(*ordering)
        else:
            invoice_data = OrderInvoice.objects.filter(
                Q(filterquery)).order_by(ordering)
        count_obj = invoice_data.count()
        invoice_paginated_data = invoice_data[offset:offset + limit]
        response_data = GetOrderInvoiceListSerializer(
            invoice_paginated_data, many=True).data
    else:
        count_obj = 0
        response_data = []
    return response_data, count_obj
