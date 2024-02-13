from size.size_filter import separate_value
from django.db.models import Value, CharField
from django.db.models.functions import Concat, Cast
from .models import EmailFieldType, EmailTemplate, Category
from .serializers import  EmailTemplateListSerializer
from django.db.models import Q
import logging
import os
from copy import deepcopy
from django.core.mail import send_mail
from celery import shared_task
from django.contrib.auth.models import User
from color.color_filter import get_user_details
from django.conf import settings

logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)

def filter_query_for_list_type_field(filter_type, i, filter_val, filterquery):
    filter_type = filter_type.replace(
        'end-with', '__iendswith')
    filter_type = filter_type.replace('equals', '__iexact')
    if i == 'ET_BCC_EMAIL' or i == "ET_TO_EMAIL" and filter_type == '__iexact':
        filter_val = str(filter_val.split(','))
        filterquery.add(
            Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    filter_type = filter_type.replace(
        'start-with', '__istartswith')
    filter_type = filter_type.replace(
        'contains', '__icontains')
    filter_type = filter_type.replace(
        'greater-than', '__gt')
    filter_type = filter_type.replace(
        'greater-equal', '__gte')
    filter_type = filter_type.replace(
        'less-than', '__lt')

    filterquery.add(
        Q(**{str(i)+str(filter_type): filter_val}), Q.AND)
    return filterquery

def date_filter_query(filter_type, i, filter_val, filterquery):
    '''Common date filter query'''
    if i == 'UPDT_DT' or i == 'CRT_DT' or i == 'updateddate' or i == 'createddate':
        if filter_type == 'not-equals':
            filter_type = filter_type.replace(
                'not-equals', '__date')
            filterquery.add(
                ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
        else:
            filter_type = filter_type.replace('less-than', '__date__lt')
            filter_type = filter_type.replace(
                'greater-than', '__date__gt')
            filter_type = filter_type.replace('equals', '__date')
            filter_type = filter_type.replace(
                'greater-equal', '__date__gte')
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND)


def create_email_filter_query(filterquery, i, filter_type, filter_val):
    '''Create a filter query'''
    if i == 'CRT_DT' or i == 'UPDT_DT':
        return date_filter_query(filter_type, i, filter_val, filterquery)
    if i == 'ET_USR_CRT' or i == 'ET_USR_UPDT':
        return get_user_details(filter_type, filterquery, i, filter_val)
    elif filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        filterquery.add(
            ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)

    else:
        filterquery = filter_query_for_list_type_field(
            filter_type, i, filter_val, filterquery)
    return filterquery


def get_data_for_template_filter(filterquery, request_data, flags):
    '''Retrieve data for position filterquery'''
    for i in request_data:
        separate_values = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        if len(separate_values[0]) > 0:
            if separate_values[1] in condition_list:
                create_email_filter_query(
                    filterquery, i, separate_values[1], separate_values[0])
            else:
                flags = False
                break
    return filterquery, flags


def template_list_filter(page, page_size, search=None, request_data=None, ordering=None):
    filterquery = Q()
    limit = int(page_size)
    page = int(page)
    offset = (page - 1) * limit
    flags = True
    if request_data:
        filterquery, flags = get_data_for_template_filter(
            filterquery, request_data, flags)
    if search:
        filterquery.add(
            Q(ET_NM__icontains=search) |
            Q(ET_DS__icontains=search) |
            Q(ET_SB__icontains=search) |
            Q(ET_Type__icontains=search) |
            Q(ET_FRM_EMAIL__icontains=search) |
            Q(ET_RPLY_TO_EMAIL__icontains=search) |
            Q(ET_BCC_EMAIL__icontains=search) |
            Q(ET_TO_EMAIL__icontains=search) |
            Q(ET_TM_DF__icontains=search) |
            Q(ET_INTERVAL__icontains=search) |
            Q(ET_AU_RSP_FR__icontains=search) |
            Q(ET_OD_STS__icontains=search) |
            Q(CRT_DT__date__icontains=search) |
            Q(ET_USR_CRT__in=User.objects.annotate(full_name=Concat(
                'first_name', Value(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search).values_list('id', flat=True)) |
            Q(UPDT_DT__date__icontains=search) |
            Q(ET_USR_UPDT__in=User.objects.annotate(full_name=Concat(
                'first_name', Value(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search).values_list('id', flat=True)),
            Q.AND
        )
    if not ordering:
        ordering = "-ET_ID"
    if flags:
        template_list_data = EmailTemplate.objects.filter(
            Q(filterquery)).order_by(ordering)
        count = template_list_data.count()
        paginated_data = template_list_data[offset:offset + limit]
        response_data = EmailTemplateListSerializer(
            paginated_data, many=True).data
    else:
        count = 0
        response_data = []
    return response_data, count
