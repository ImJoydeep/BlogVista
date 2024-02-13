from django.db.models import Q
from style.style_filter import separate_value
from order.serializers_shipment import ShipmentListSerializer

from order.models import ItemShipmentList, ShipmentMaster


def shipment_filter_query(filterquery, i, filter_type, filter_val):
    '''Shipment filter query'''
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        if i == 'CRT_DT':
            filterquery.add(
                ~Q(**{'CRT_DT__date': filter_val}), Q.AND)
        else:
            filterquery.add(
                ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        return filterquery
    else:
        filter_type = filter_type.replace(
            'start-with', '__istartswith')
        filter_type = filter_type.replace(
            'end-with', '__iendswith')
        filter_type = filter_type.replace(
            'contains', '__icontains')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace(
            'greater-than', '__gt')
        if i == 'CRT_DT':
            filterquery.add(
                Q(**{'CRT_DT__date' + str(filter_type): filter_val}), Q.AND)
        else:
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND)


def get_data_for_shipment_filter(filterquery, request_data, flags):
    '''Retrieve data for position filterquery'''
    for i in request_data:
        separate_values = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        if len(separate_values[0]) > 0:
            if separate_values[1] in condition_list:
                shipment_filter_query(
                    filterquery, i, separate_values[1], separate_values[0])
            else:
                flags = False
                break
    return filterquery, flags


def shipment_filter(page, page_size, search=None, request_data=None, ordering=None):
    '''shipment Filter'''
    if search == '':
        search = None
    filterquery = Q()
    flags = True
    filterquery.add(Q(IS_GENERATED=True), Q.AND)
    if request_data is not None:
        filterquery, flags = get_data_for_shipment_filter(
            filterquery, request_data, flags)
    if search is not None:
        filterquery.add(
            Q(OD_SHIP_CODE__icontains=search) |
            Q(OD_SHP_STS__icontains=search) |
            Q(TOT_PICK_QTY__icontains=search) |
            Q(TOT_AMT__icontains=search) |
            Q(TOT_NET_AMT__icontains=search) |
            Q(TOT_TAX_AMT__icontains=search) |
            Q(TOT_DIS_AMT__icontains=search) |
            Q(MUL_OD_ID__icontains=search) |
            Q(MUL_OD_STR_NM__icontains=search) |
            Q(CRT_DT__date__icontains=search),
            Q.AND
        )
    if not ordering:
        ordering = '-OD_SHP_ID'
    if flags == True:
        limit = int(page_size)
        page = int(page)
        offset = (page - 1) * limit
        shipment_data = ShipmentMaster.objects.filter(
            Q(filterquery)).order_by(ordering)
        count_obj = shipment_data.count()
        shipment_paginated_data = shipment_data[offset:offset + limit]
        response_data = ShipmentListSerializer(
            shipment_paginated_data, many=True).data
    else:
        count_obj = 0
        response_data = []
    return response_data, count_obj
