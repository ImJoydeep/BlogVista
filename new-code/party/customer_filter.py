'''Customer Filter'''
from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from position.position_filter import filter_with_start_end_columns
from color.filter_ordering_by_user import ordering_by_crt_by
from party.customer_serializers import CustomerListSerializer
from party.models import Person
from size.common_date_filter_file import common_date_filter_query
from order.models import Customer
from size.size_filter import retrieve_user_details, separate_value
from copy import deepcopy

def get_user_and_date(filterquery, i, filter_type, filter_val):
    if i == 'CRT_BY' or i == 'UPDT_BY':
        retrieve_user_details(filter_type, filterquery, i, filter_val)
        return filterquery
    if i == 'start_date' or i == 'end_date':
        filter_with_start_end_columns(filterquery, i, filter_type, filter_val)
        return filterquery
    if i == 'UPDT_DT' or i == 'CRT_DT' or i == 'MDF_DT' or i == 'createddate' or i == 'updateddate' or i == 'CREATED_AT':
        return common_date_filter_query(filter_type, i, filter_val, filterquery)
    if i == 'CRT_BY' or i == 'UPDT_BY':
        i = i.replace(
            'CRT_BY', 'CRT_BY__username')
        i = i.replace(
            'UPDT_BY', 'UPDT_BY__username')
        
def cust_nm_query(filterquery, i, filter_type, filter_val):
    if i == 'CUST_NM':
        if len(filter_val.split(' ')) > 1:
            filterquery.add(
                Q(**{'CUST_FNM'+str(filter_type):str(filter_val).split()[0], 'CUST_LNM'+str(filter_type):str(filter_val).split()[1]}),Q.AND)
        else:
            filterquery.add(
                Q(**{'CUST_FNM'+str(filter_type):str(filter_val)}),Q.AND
            )
    else:
        filterquery.add(
            Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery

def filter_query(filterquery, i, filter_type, filter_val):
    '''Filter query for a filter'''
    users_and_date = get_user_and_date(filterquery, i, filter_type, filter_val)
    if users_and_date:
        return users_and_date
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        if i == 'CUST_NM':
            if len(filter_val.split(' ')) > 1:
                filterquery.add(
                    ~Q(**{'CUST_FNM'+str(filter_type):str(filter_val).split()[0], 'CUST_LNM'+str(filter_type):str(filter_val).split()[1]}),Q.AND)
            else:
                filterquery.add(
                    ~Q(**{'CUST_FNM'+str(filter_type):str(filter_val)}),Q.AND
                )
        else:
            filterquery.add(
                ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        return filterquery
    else:
        filter_type = filter_type.replace('contains', '__icontains')
        filter_type = filter_type.replace('start-with', '__istartswith')
        filter_type = filter_type.replace('less-than', '__lt')
        filter_type = filter_type.replace('end-with', '__iendswith')
        filter_type = filter_type.replace('greater-than', '__gt')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace('greater-equal', '__gte')
        cust_search = cust_nm_query(filterquery, i, filter_type, filter_val)
        if cust_search:
            return cust_search
    return filterquery


def get_data_for_cartes_filter(filterquery, request_data, flags):
    '''Retrieve data for position filterquery'''
    for i in request_data:
        separate_values = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals',
                          'not-contains','greater-equal', 'greater-than']
        if len(separate_values[0]) > 0:
            if separate_values[1] in condition_list:
                filter_query(filterquery, i, separate_values[1], separate_values[0])
            else:
                flags = False
                break
    return filterquery, flags


def customer_filter(page, page_size, search=None, request_data=None, ordering=None):
    '''Crates Filter'''
    flags = True
    cust_query = Q()
    filterquery = Q()
    
    if search == '':
        search = None
    if request_data is not None:
        filterquery, flags = get_data_for_cartes_filter(filterquery, request_data, flags)
    
    if search is not None:
        cust_search = search.split(' ')
        if len(cust_search) > 1:
            cust_query.add(
                Q(CUST_FNM__icontains=cust_search[0]) &
                Q(CUST_LNM__icontains=cust_search[1]),Q.AND
            )
        else:
            cust_query.add(
                Q(CUST_FNM__icontains=str(search).split(' ')[0]) |
                Q(CUST_LNM__icontains=str(search).split(' ')[0]),Q.AND
            )
        filterquery.add(
            Q(cust_query)|
            Q(CUST_FNM__icontains=search) |
            Q(CUST_LNM__icontains=search) |
            Q(CUST_EMAIL__icontains=search) |
            Q(CUST_PH__icontains=search) |
            Q(IS_GUST__icontains=search) |
            Q(CUST_ST__icontains=search)|
            Q(UPDT_DT__date__icontains=search) |
            Q(CRT_DT__date__icontains=search) |
            Q(CRT_BY__in=list(User.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name',
                                output_field=CharField())).filter(
                full_name__icontains=search).values_list('id', flat=True))) |
            Q(UPDT_BY__in=list(User.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name',
                                output_field=CharField())).filter(
                full_name__icontains=search).values_list('id', flat=True))),
        Q.AND)

    temp_ordering = deepcopy(ordering)
    ordering_lists = ['CRT_BY', '-CRT_BY', 'UPDT_BY', '-UPDT_BY','CUST_NM','-CUST_NM']
    if ordering is not None and ordering != '':
        ordering = order_customer(ordering)
    else:
        ordering = '-id'
    if flags == True:
        count_obj = Customer.objects.filter(Q(filterquery)).count()
        limit = int(page_size)
        offset = (page - 1) * limit
        page = int(page)
        if temp_ordering in ordering_lists:
            customer_data = Customer.objects.filter(Q(filterquery)).order_by(*ordering)
        else:
            customer_data = Customer.objects.filter(
                Q(filterquery)).order_by(ordering)
        customer_ordered_data = customer_data[offset:offset + limit]
        response_data = CustomerListSerializer(
            customer_ordered_data, many=True).data
    else:
        response_data = []
        count_obj = 0
    return response_data, count_obj

def order_customer(ordering):
    if ordering == 'CUST_NM':
        ordering1 = ordering.replace(
            'CUST_NM', 'CUST_FNM')
        ordering2 = ordering.replace(
            'CUST_NM', 'CUST_LNM')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == '-CUST_NM':
        ordering1 = ordering.replace(
            '-CUST_NM', '-CUST_FNM')
        ordering2 = ordering.replace(
            '-CUST_NM', '-CUST_LNM')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == 'CRT_BY':
        ordering1 = ordering.replace(
            'CRT_BY', 'CRT_BY__first_name')
        ordering2 = ordering.replace(
            'CRT_BY', 'CRT_BY__last_name')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == '-CRT_BY':
        ordering1 = ordering.replace(
            '-CRT_BY', '-CRT_BY__first_name')
        ordering2 = ordering.replace(
            '-CRT_BY', '-CRT_BY__last_name')
        ordering = [ordering1, ordering2]
    if ordering == 'UPDT_BY':
        ordering1 = ordering.replace(
            'UPDT_BY', 'UPDT_BY__first_name')
        ordering2 = ordering.replace(
            'UPDT_BY', 'UPDT_BY__last_name')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == '-UPDT_BY':
        ordering1 = ordering.replace(
            '-UPDT_BY', '-UPDT_BY__first_name')
        ordering2 = ordering.replace(
            '-UPDT_BY', '-UPDT_BY__last_name')
        ordering = [ordering1, ordering2]
    return ordering