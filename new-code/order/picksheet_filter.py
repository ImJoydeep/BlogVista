'''Picksheet Note Filter'''
from copy import deepcopy
from .models import PicksheetNote,PicksheetNoteStores,PicksheetNoteItemSKU
from .serializers import PickSheetSerializer, PickSheetStoreSerializer
from copy import deepcopy
from product.models import Item
from size.size_filter import separate_value
from django.db.models import Q
from party.customer_filter import get_user_and_date

def filter_query(filterquery, i, filter_type, filter_val):
    '''Filter query for a filter'''
    user_and_date = get_user_and_date(filterquery, i, filter_type, filter_val)
    if user_and_date:
        return user_and_date
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        if i == 'STR_NM':
            filterquery.add(
                ~Q(PSN_ID__in=list(PicksheetNoteStores.objects.filter(Q(**{"STR_ID__NM_LCN"+str(filter_type): filter_val}) & 
                                                                      Q(**{"STR_ID__CD_LCN_TYP__DE_LCN_TYP"+str(filter_type): "STR"})).values_list('PSN_ID', flat=True))), 
                Q.AND
                )
        elif i == 'ITM_SKU_ID':
            filterquery.add(
                ~Q(PSN_ID__in=list(PicksheetNoteItemSKU.objects.filter(Q(**{"ITM_SKU_ID"+str(filter_type): filter_val})).values_list('PSN_ID', flat=True))), 
                Q.AND
                )

        else:
            filterquery.add(~Q(**{str(i) + str(filter_type): filter_val}),
                            Q.AND
                            )
        return filterquery
    else:
        filter_type = filter_type.replace(
            'contains', '__icontains')
        filter_type = filter_type.replace(
            'start-with', '__istartswith')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace(
            'end-with', '__iendswith')
        filter_type = filter_type.replace(
            'greater-than', '__gt')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        if i == 'STR_NM':
            filterquery.add(
                Q(PSN_ID__in=list(PicksheetNoteStores.objects.filter(
                    Q(**{"STR_ID__NM_LCN"+str(filter_type): filter_val}) & Q(**{"STR_ID__CD_LCN_TYP__DE_LCN_TYP"+str(filter_type): "STR"})).values_list('PSN_ID', flat=True))), Q.AND
            )
        elif i == 'ITM_SKU_ID':
            filterquery.add(
                Q(PSN_ID__in=list(PicksheetNoteItemSKU.objects.filter(
                    Q(**{"ITM_SKU_ID__AS_ITM_SKU"+str(filter_type): filter_val})).values_list('PSN_ID', flat=True))), Q.AND
            )
        else:
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND
            )
    return filterquery


def get_data_for_cartes_filter(filterquery, request_data, flags):
    '''Retrieve data for Picksheet Note filterquery'''
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


def picksheet_filter(page, page_size, search=None, request_data=None):
    '''Picksheet Note Filter'''
    filterquery = Q()
    flags = True
    if search == '':
        search = None
    if request_data is not None:
        filterquery, flags = get_data_for_cartes_filter(
            filterquery, request_data, flags)
    if search is not None:
        filterquery.add(
            Q(PSN_NM__icontains=search) |
            Q(PSN_STS__icontains=search) |
            Q(ST_DT__icontains=search) |
            Q(EN_DT__icontains=search) |
            Q(PSN_VIS__icontains=search) |
            Q(NT_DETAILS__icontains=search) |
            
            Q(PSN_ID__in=list(PicksheetNoteStores.objects.filter(
                Q(STR_ID__NM_LCN__icontains=search)).values_list('PSN_ID', flat=True)))|
            Q(PSN_ID__in=list(PicksheetNoteItemSKU.objects.filter(
                Q(ITM_SKU_ID__AS_ITM_SKU__icontains=search)).values_list('PSN_ID', flat=True))),
            Q.AND
        )
    if flags == True:
        count_obj = PicksheetNote.objects.filter(
            Q(filterquery)).count()
        limit = int(page_size)
        page = int(page)
        offset = (page - 1) * limit
        position_data = PicksheetNote.objects.filter(
            Q(filterquery)).order_by('-PSN_ID')
        position_ordered_data = position_data[offset:offset + limit]
        response_data = PickSheetSerializer(
            position_ordered_data, many=True).data
    else:
        count_obj = 0
        response_data = []
    return response_data, count_obj
