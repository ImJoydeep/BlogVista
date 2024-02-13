from django.db.models import Q
import logging
import os
from globalsettings.models import BusinessUnitSetting, GlobalSetting
from size.common_date_filter_file import common_date_filter_query
from order.models import OrderBillingAddress, OrderItemDetails, OrderMaster, OrderShippingAddress
from order.serializers import OrderMasterSerializer
from copy import deepcopy
import pandas as pd
from django.core.mail import send_mail
from celery import shared_task
from django.contrib.auth.models import User

from django.conf import settings
from size.size_filter import global_export_datetime_format, s3_clients
from basics.notification_views import send_pushnotification
from size.size_filter import to_dict

from size.size_filter import separate_value

logger = logging.getLogger(__name__)


def create_query_for_not_not_type(filterquery, i, filter_type, filter_val):
    '''Create a query for not not type'''
    if i == 'OD_SA_PH':
        filterquery.add(Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_PH'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_ITM_AMT_REF':
        filterquery.add(Q(OD_ID__in=OrderItemDetails.objects.filter(
            **{'OD_ITM_AMT_REF'+str(filter_type): filter_val}).values_list('OD_ID', flat=True)), Q.AND)
    elif i == 'OD_BA_CT':
        filterquery.add(Q(OD_ID__in=OrderBillingAddress.objects.filter(
            **{'OD_BA_CT'+str(filter_type): filter_val}).values_list('OD_BA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_SA_CT':
        filterquery.add(Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_CT'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_BA_ST':
        filterquery.add(Q(OD_ID__in=OrderBillingAddress.objects.filter(
            **{'OD_BA_ST'+str(filter_type): filter_val}).values_list('OD_BA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_SA_ST':
        filterquery.add(Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_ST'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_BA_PIN':
        filterquery.add(Q(OD_ID__in=OrderBillingAddress.objects.filter(
            **{'OD_BA_PIN'+str(filter_type): filter_val}).values_list('OD_BA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_SA_PIN':
        filterquery.add(Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_PIN'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    return filterquery


def create_query_for_not_type(filterquery, i, filter_type, filter_val):
    '''Create a query for not not type'''
    if i == 'OD_SA_PH':
        filterquery.add(~Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_PH'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_ITM_AMT_REF':
        filterquery.add(~Q(OD_ID__in=OrderItemDetails.objects.filter(
            **{'OD_ITM_AMT_REF'+str(filter_type): filter_val}).values_list('OD_ID', flat=True)), Q.AND)
    elif i == 'OD_BA_CT':
        filterquery.add(~Q(OD_ID__in=OrderBillingAddress.objects.filter(
            **{'OD_BA_CT'+str(filter_type): filter_val}).values_list('OD_BA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_SA_CT':
        filterquery.add(~Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_CT'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_BA_ST':
        filterquery.add(~Q(OD_ID__in=OrderBillingAddress.objects.filter(
            **{'OD_BA_ST'+str(filter_type): filter_val}).values_list('OD_BA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_SA_ST':
        filterquery.add(~Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_ST'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_BA_PIN':
        filterquery.add(~Q(OD_ID__in=OrderBillingAddress.objects.filter(
            **{'OD_BA_PIN'+str(filter_type): filter_val}).values_list('OD_BA_OD_ID', flat=True)), Q.AND)
    elif i == 'OD_SA_PIN':
        filterquery.add(~Q(OD_ID__in=OrderShippingAddress.objects.filter(
            **{'OD_SA_PIN'+str(filter_type): filter_val}).values_list('OD_SA_OD_ID', flat=True)), Q.AND)
    return filterquery


def date_filter_query(filter_type, i, filter_val, filterquery):
    '''Common date filter query'''
    if filter_type == 'not-equals':
        filter_type = filter_type.replace(
            'not-equals', '__icontains')
        filterquery.add(
            ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        return filterquery
    else:
        filter_type = filter_type.replace(
            'equals', '__icontains')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        filterquery.add(
            Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        return filterquery


def get_the_filter_query_for_float_fields(filter_type, i, filterquery, filter_val):
    '''Get the filter query for float fields'''
    if filter_type.startswith('not'):
        filter_type = filter_type.replace('not-equals', '__exact')
        if i == 'OD_ITM_AMT_REF':
            filterquery.add(~Q(OD_ID__in=OrderItemDetails.objects.filter(
                **{'OD_ITM_AMT_REF'+str(filter_type): filter_val}).values_list('OD_ID', flat=True)), Q.AND)
        else:
            filterquery.add(
                ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    else:
        filter_type = filter_type.replace(
            'contains', '__exact')
        filter_type = filter_type.replace('equals', '__exact')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        if i == 'OD_ITM_AMT_REF':
            filterquery.add(Q(OD_ID__in=OrderItemDetails.objects.filter(
                **{'OD_ITM_AMT_REF'+str(filter_type): filter_val}).values_list('OD_ID', flat=True)), Q.AND)
        else:
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery


def create_order_filter_query(filterquery, i, filter_type, filter_val, temp_list):
    '''Create a filter query'''
    if i in ['OD_NT_AMT', 'OD_TL_AMT', 'OD_DIS_AMT', 'OD_TX_AMT', 'OD_PD_AMT', 'OD_ITM_AMT_REF']:
        filterquery = get_the_filter_query_for_float_fields(
            filter_type, i, filterquery, filter_val)
        return filterquery
    if i == 'OD_DATE':
        return date_filter_query(filter_type, i, filter_val, filterquery)
    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        if i in temp_list:
            create_query_for_not_type(filterquery, i, filter_type, filter_val)
        else:
            filterquery.add(
                ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        return filterquery
    else:
        filter_type = filter_type.replace(
            'end-with', '__iendswith')
        filter_type = filter_type.replace(
            'start-with', '__istartswith')
        filter_type = filter_type.replace(
            'contains', '__icontains')
        filter_type = filter_type.replace('equals', '__iexact')
        filter_type = filter_type.replace(
            'less-than', '__lt')
        filter_type = filter_type.replace(
            'greater-than', '__gt')
        filter_type = filter_type.replace(
            'greater-equal', '__gte')
        if i in temp_list:
            create_query_for_not_not_type(
                filterquery, i, filter_type, filter_val)
        else:
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery


def get_data_for_orders_filter(filterquery, request_data, flags, temp_list):
    '''Retrieve data for position filterquery'''
    for i in request_data:
        separate_values = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        if len(separate_values[0]) > 0:
            if separate_values[1] in condition_list:
                create_order_filter_query(
                    filterquery, i, separate_values[1], separate_values[0], temp_list)
            else:
                flags = False
                break
    return filterquery, flags


def order_list_filter(page, page_size, status_filter, search=None, request_data=None, ordering=None, device=None):
    filterquery = Q()
    limit = int(page_size)
    page = int(page)
    offset = (page - 1) * limit
    flags = True
    temp_list = ['OD_SA_PH', 'OD_BA_CT', 'OD_SA_CT',
                 'OD_BA_ST', 'OD_SA_ST', 'OD_BA_PIN', 'OD_SA_PIN']
    if status_filter in ['new', 'rtp', 'pickup', 'void', 'oh', 'cmp']:
        status_filter = status_filter.replace('rtp', 'ready_to_pick')
        status_filter = status_filter.replace('pickup', 'ready_for_pickup')
        status_filter = status_filter.replace('oh', 'on hold')
        status_filter = status_filter.replace('cmp', 'complete')
        filterquery.add(
            Q(OMS_OD_STS=status_filter), Q.AND
        )
    if request_data:
        filterquery, flags = get_data_for_orders_filter(
            filterquery, request_data, flags, temp_list)
    if search:
        filterquery.add(
            Q(CU_OD_ID__icontains=search) |
            Q(OD_CUS_NM__icontains=search) |
            Q(OD_CUS_EMAIL__icontains=search) |
            Q(OD_QTY__icontains=search) |
            Q(OD_TL_AMT__icontains=search) |
            Q(OD_DATE__icontains=search) |
            Q(OD_STS__icontains=search) |
            Q(OD_ID__in=OrderShippingAddress.objects.filter(OD_SA_PH__icontains=search).values_list('OD_SA_OD_ID', flat=True)) |
            Q(OD_STR_NM__icontains=search) |
            Q(OD_NT_AMT__icontains=search) |
            Q(OD_DIS_AMT__icontains=search) |
            Q(OD_TX_AMT__icontains=search) |
            Q(OD_PD_AMT__icontains=search) |
            Q(OD_ID__in=OrderItemDetails.objects.filter(OD_ITM_AMT_REF__icontains=search).values_list('OD_ID', flat=True)) |
            Q(PT_MD_NM__icontains=search) |
            Q(OD_ID__in=OrderBillingAddress.objects.filter(OD_BA_CT__icontains=search).values_list('OD_BA_OD_ID', flat=True)) |
            Q(OD_ID__in=OrderShippingAddress.objects.filter(OD_SA_CT__icontains=search).values_list('OD_SA_OD_ID', flat=True)) |
            Q(OD_ID__in=OrderBillingAddress.objects.filter(OD_BA_ST__icontains=search).values_list('OD_BA_OD_ID', flat=True)) |
            Q(OD_ID__in=OrderShippingAddress.objects.filter(OD_SA_ST__icontains=search).values_list('OD_SA_OD_ID', flat=True)) |
            Q(OD_ID__in=OrderBillingAddress.objects.filter(OD_BA_PIN__icontains=search).values_list('OD_BA_OD_ID', flat=True)) |
            Q(OD_ID__in=OrderShippingAddress.objects.filter(OD_SA_PIN__icontains=search).values_list('OD_SA_OD_ID', flat=True)) |
            Q(OD_INVC_NUM__icontains=search) |
            Q(OD_SHP_NUM__icontains=search) |
            Q(OD_INST__icontains=search),
            Q.AND
        )
    if ordering:
        ordering = ordering.replace(
            'OD_SA_PH', 'ordershippingaddress__OD_SA_PH')
        ordering = ordering.replace(
            'OD_ITM_AMT_REF', 'orderitemdetails__OD_ITM_AMT_REF')
        ordering = ordering.replace(
            'OD_BA_CT', 'orderbillingaddress__OD_BA_CT')
        ordering = ordering.replace(
            'OD_SA_CT', 'ordershippingaddress__OD_SA_CT')
        ordering = ordering.replace(
            'OD_BA_ST', 'orderbillingaddress__OD_BA_ST')
        ordering = ordering.replace(
            'OD_SA_ST', 'ordershippingaddress__OD_SA_ST')
        ordering = ordering.replace(
            'OD_BA_PIN', 'orderbillingaddress__OD_BA_PIN')
        ordering = ordering.replace(
            'OD_SA_PIN', 'ordershippingaddress__OD_SA_PIN')
        ordering = ordering.replace(
            '-OD_SA_PH', '-ordershippingaddress__OD_SA_PH')
        ordering = ordering.replace(
            '-OD_ITM_AMT_REF', '-orderitemdetails__OD_ITM_AMT_REF')
        ordering = ordering.replace(
            '-OD_BA_CT', '-orderbillingaddress__OD_BA_CT')
        ordering = ordering.replace(
            '-OD_SA_CT', '-ordershippingaddress__OD_SA_CT')
        ordering = ordering.replace(
            '-OD_BA_ST', '-orderbillingaddress__OD_BA_ST')
        ordering = ordering.replace(
            '-OD_SA_ST', '-ordershippingaddress__OD_SA_ST')
        ordering = ordering.replace(
            '-OD_BA_PIN', '-orderbillingaddress__OD_BA_PIN')
        ordering = ordering.replace(
            '-OD_SA_PIN', '-ordershippingaddress__OD_SA_PIN')
    else:
        ordering = "-OD_ID"
    if flags:
        if device:
            queryset_new = OrderMaster.objects.filter(
                OMS_OD_STS__in=["ready_to_pick", "new"])
        else:
            queryset_new = OrderMaster.objects.all()
        order_list_data = queryset_new.filter(
            Q(filterquery)).order_by(ordering)
        count = order_list_data.count()
        paginated_data = order_list_data[offset:offset + limit]
        response_data = OrderMasterSerializer(paginated_data, many=True).data
    else:
        count = 0
        response_data = []
    return response_data, count


def convert_order_datetime(new_df, date_format, timezone):
    '''Change time based on timezone'''
    if date_format == 'MM-dd-yyyy':
        dt_for = "%m-%d-%Y %H:%M:%S.%f%z"
    elif date_format == 'dd-MM-yyyy':
        dt_for = "%d-%m-%Y %H:%M:%S.%f%z"
    elif date_format == 'yyyy-MM-dd':
        dt_for = "%Y-%m-%d %H:%M:%S.%f%z"
    else:
        dt_for = "%d-%m-%Y %H:%M:%S.%f%z"
    if new_df['OD_DATE'].dropna().shape[0] == 0:
        new_df['OD_DATE'] = ''
        new_df['utime'] = ''
        new_df['udate'] = ''
    else:
        new_df['OD_DATE'] = pd.to_datetime(
            new_df['OD_DATE']).dt.tz_convert(timezone[4:])
        new_df['OD_DATE'] = new_df['OD_DATE'].astype(str).str[:19]
        new_df['utime'] = new_df['OD_DATE']
        new_df['utime'] = new_df['utime'].astype(str).str[11:19]
        new_df['udate'] = pd.to_datetime(
            new_df['OD_DATE']).dt.strftime(dt_for[:8])
        new_df['utime'] = pd.to_datetime(
            new_df['utime']).dt.strftime('%I:%M:%S %p')
        new_df['OD_DATE'] = new_df['udate']+' '+new_df['utime']
    return new_df


def create_dataframe_from_dict_for_export(new_df, bsn_unit_id, temp):
    '''Create dataframe for export'''
    if bsn_unit_id != '0':
        try:
            global_obj = GlobalSetting.objects.filter(
                ID_GB_STNG=BusinessUnitSetting.objects.get(ID_BSN_UN=bsn_unit_id).ID_GB_STNG.ID_GB_STNG)
            date_format = global_obj.last().ID_BA_DFMT.name
            timezone = global_obj.last().ID_BA_TZN.gmt_offset
            new_df = convert_order_datetime(
                new_df, date_format, timezone)
        except Exception as exp:
            logger.exception("Export Business Unit error: %s", exp)
            new_df = convert_order_datetime(
                new_df, temp['date_format'], temp['time_zone'])
    else:
        new_df = convert_order_datetime(
            new_df, temp['date_format'], temp['time_zone'])
    return new_df


@shared_task
def order_export(response, dynamic_column, bsn_unit_id, export_file_name, file_location, notification_data, device_flags, file_type):
    '''Color export function and send mail with notification'''
    response = to_dict(response[0])
    headers = [i for i in dynamic_column]
    temp_format = global_export_datetime_format
    try:
        df = pd.DataFrame.from_records(response)
        new_df = df[headers]
        new_df = create_dataframe_from_dict_for_export(
            new_df, bsn_unit_id, temp_format)
        new_df = new_df.drop(
            ['udate', 'utime'], axis=1)
    except Exception as e:
        logger.exception("Color Export Exception : %s", e)
        new_df = df.reindex(columns=df.columns.tolist() +
                            headers)
    new_df.rename(columns=dynamic_column, inplace=True)
    if str(file_type).lower() == 'xlsx':
        new_df.to_excel(export_file_name, index=False)
    else:
        new_df.to_csv(export_file_name, index=False)
    s3_clients.upload_file(
        export_file_name, settings.BUCKET_NAME, file_location)
    object_url = str(s3_clients._endpoint).split('(')[1].replace(
        ')', '/') + settings.BUCKET_NAME + '/' + str(file_location)
    users_email_id = User.objects.get(
        id=notification_data.get('user_id')).email
    export_messages = str(object_url)
    subjects = 'Order Export'
    from_email = os.getenv('MAIL')
    send_mail(subject=subjects, message=export_messages, from_email=from_email,
              recipient_list=[users_email_id])
    if device_flags:
        send_pushnotification(**notification_data)
    os.remove(export_file_name)
