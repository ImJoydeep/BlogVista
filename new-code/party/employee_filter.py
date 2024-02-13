'''Employee Filter'''
import logging
from copy import deepcopy
from django.db.models import Q
from django.db.models.functions import Concat
from django.db.models import Value, CharField
from django.contrib.auth.models import User
from accesscontrol.models import OperatorGroup, WorkerOperatorAssignment
from color.color_filter import get_user_details
from size.common_date_filter_file import common_date_filter_query
from party.serializers import EmployeeListSerializer
from party.models import EmailAddress, PartyContactMethod, Person, Telephone
from worker.models import Employee
from position.models import WorkerPositionAssignment
from size.size_filter import separate_value

logger = logging.getLogger(__name__)


def filter_columns(filterquery, i, filter_type, filter_val):
    '''Employee filter by columns'''
    if i == 'position_name':
        filterquery.add(Q(ID_WRKR__in=WorkerPositionAssignment.objects.filter(
            Q(**{'ID_PST__NM_TTL' + str(filter_type): filter_val})).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'permission_set':
        filterquery.add(Q(ID_WRKR__in=WorkerOperatorAssignment.objects.filter(Q(ID_OPR__in=OperatorGroup.objects.filter(
            **{'ID_GP_WRK__NM_GP_WRK' + str(filter_type): filter_val}).values_list('ID_OPR', flat=True)
        )).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'operator':
        filterquery.add(Q(ID_WRKR__in=WorkerOperatorAssignment.objects.filter(
            Q(**{'ID_OPR__NM_USR' + str(filter_type): filter_val})).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'department_name':
        filterquery.add(Q(ID_WRKR__in=WorkerPositionAssignment.objects.filter(
            Q(**{'ID_PST__department_id__name' + str(filter_type): filter_val})).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'EM_ADS':
        email_ids = EmailAddress.objects.annotate(email=Concat(
            'EM_ADS_LOC_PRT', Value('@'), 'EM_ADS_DMN_PRT', output_field=CharField())).filter(
            **{'email' + str(filter_type): filter_val}).exclude(EM_ADS_LOC_PRT__exact='',
                                                                EM_ADS_DMN_PRT__exact='').values_list(
            'ID_EM_ADS', flat=True)
        filter_queries = PartyContactMethod.objects.filter(
            Q(ID_EM_ADS__in=email_ids) & Q(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=False) & Q(
                ID_EM_ADS__EM_ADS_DMN_PRT__isnull=False) & Q(
                CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
        filterquery.add(Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=filter_queries),
                        Q.AND)
    elif i == 'employee_name':
        employee_queries = Q()
        if len(filter_val.split(' ')) > 1:
            employee_queries.add(
                Q(**{'FN_PRS' + str(filter_type): str(filter_val).split(' ')[0]}) &
                Q(**{'LN_PRS' + str(filter_type)
                  : str(filter_val).split(' ')[1]}),
                Q.AND
            )
        else:
            employee_queries.add(
                Q(**{'FN_PRS' + str(filter_type): str(filter_val).split(' ')[0]}) |
                Q(**{'LN_PRS' + str(filter_type)
                  : str(filter_val).split(' ')[0]}),
                Q.AND
            )
        filterquery.add(Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY__in=Person.objects.filter(
            employee_queries).values_list('ID_PRTY', flat=True)),
            Q.AND)
    elif i == 'PH_CMPL':
        telephone_obj = Telephone.objects.filter(
            **{'PH_CMPL' + str(filter_type): filter_val}).values_list('ID_PH', flat=True)
        filterqueries = PartyContactMethod.objects.filter(
            Q(ID_PH__in=telephone_obj) & Q(CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
        filterquery.add(Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=filterqueries),
                        Q.AND)
    return filterquery


def filter_data_employee_for_not_query(filterquery, filter_type, filter_val, i):
    '''Filter data for not query for employee'''
    if i == 'position_name':
        filterquery.add(~Q(ID_WRKR__in=WorkerPositionAssignment.objects.filter(
            Q(**{'ID_PST__NM_TTL' + str(filter_type): filter_val})).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'permission_set':
        filterquery.add(~Q(ID_WRKR__in=WorkerOperatorAssignment.objects.filter(
            Q(ID_OPR__in=OperatorGroup.objects.filter(
                **{'ID_GP_WRK__NM_GP_WRK' + str(filter_type): filter_val}).values_list('ID_OPR', flat=True)
              )).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'operator':
        filterquery.add(~Q(ID_WRKR__in=WorkerOperatorAssignment.objects.filter(
            Q(**{'ID_OPR__NM_USR' + str(filter_type): filter_val})).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'department_name':
        filterquery.add(~Q(ID_WRKR__in=WorkerPositionAssignment.objects.filter(
            Q(**{'ID_PST__department_id__name' + str(filter_type): filter_val})).values_list('ID_WRKR', flat=True)),
            Q.AND)
    elif i == 'EM_ADS':
        email_id = EmailAddress.objects.annotate(email=Concat(
            'EM_ADS_LOC_PRT', Value('@'), 'EM_ADS_DMN_PRT', output_field=CharField())).filter(
            **{'email' + str(filter_type): filter_val}).exclude(EM_ADS_LOC_PRT__exact='',
                                                                EM_ADS_DMN_PRT__exact='').values_list(
            'ID_EM_ADS', flat=True)
        filterqueries = PartyContactMethod.objects.filter(
            Q(ID_EM_ADS__in=email_id) & Q(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=False) & Q(
                ID_EM_ADS__EM_ADS_DMN_PRT__isnull=False) & Q(
                CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
        filterquery.add(~Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=filterqueries),
                        Q.AND)
    elif i == 'employee_name':
        employee_query = Q()
        if len(filter_val.split(' ')) > 1:
            employee_query.add(
                Q(**{'FN_PRS' + str(filter_type): str(filter_val).split(' ')[0]}) &
                Q(**{'LN_PRS' + str(filter_type)
                  : str(filter_val).split(' ')[1]}),
                Q.AND
            )
        else:
            employee_query.add(
                Q(**{'FN_PRS' + str(filter_type)
                  : str(filter_val).split(' ')[0]}),
                Q.AND
            )
        filterquery.add(~Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY__in=Person.objects.filter(
            employee_query).values_list('ID_PRTY', flat=True)),
            Q.AND)
    elif i == 'PH_CMPL':
        telephone_obj = Telephone.objects.filter(
            **{'PH_CMPL' + str(filter_type): filter_val}).values_list('ID_PH', flat=True)
        filterqueries = PartyContactMethod.objects.filter(
            Q(ID_PH__in=telephone_obj) & Q(CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
        filterquery.add(~Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=filterqueries),
                        Q.AND)
    else:
        filterquery.add(
            ~Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery


def filter_query(filterquery, i, filter_type, filter_val):
    '''Filter query for a filter'''
    field_list = ['position_name', 'permission_set',
                  'operator', 'department_name', 'EM_ADS', 'employee_name', 'PH_CMPL']
    if filter_val == 'Annonymous' or filter_val == 'AnonymousUser':
        filterquery = {}
        return filterquery
    if i == 'ID_USR_CRT':
        get_user_details(filter_type, filterquery, i, filter_val)
        return filterquery
    if i == 'ID_USR_UPDT':
        get_user_details(filter_type, filterquery, i, filter_val)
        return filterquery
    if i == 'UPDT_DT' or i == 'CRT_DT' or i == 'createddate' or i == 'updateddate' or i == 'CREATED_AT':
        return common_date_filter_query(filter_type, i, filter_val, filterquery)

    if filter_type.startswith('not'):
        filter_type = filter_type.replace(
            'not-equals', '__iexact')
        filter_type = filter_type.replace(
            'not-contains', '__icontains')
        filter_data_employee_for_not_query(
            filterquery, filter_type, filter_val, i)
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
        if i in field_list:
            filter_columns(filterquery, i, filter_type, filter_val)
        else:
            filterquery.add(
                Q(**{str(i) + str(filter_type): filter_val}), Q.AND)
    return filterquery


def get_data_for_employee_filtering(request_data, filterquery, flags):
    '''Retrieve employee filter data'''
    for i in request_data:
        separate_values = separate_value(request_data, i)
        condition_list = ['start-with', 'less-than', 'end-with', 'contains', 'equals', 'not-equals', 'not-contains',
                          'greater-equal', 'greater-than']
        if len(separate_values[0]) > 0:
            if separate_values[1] in condition_list:
                filter_query(
                    filterquery, i, separate_values[1], separate_values[0])
            else:
                flags = False
                break
    return filterquery, flags


def get_employee_search_query(filterquery, search, employee_name_query):
    '''Creating search query of employee'''
    crt_search = search.split(' ')
    if len(crt_search) > 1:
        employee_name_query.add(
            Q(FN_PRS__icontains=crt_search[0]) &
            Q(LN_PRS__icontains=crt_search[1]),
            Q.AND
        )
    else:
        employee_name_query.add(
            Q(FN_PRS__icontains=str(search).split(' ')[0]) |
            Q(LN_PRS__icontains=str(search).split(' ')[0]),
            Q.AND
        )
    email_id = EmailAddress.objects.annotate(email=Concat(
        'EM_ADS_LOC_PRT', Value('@'), 'EM_ADS_DMN_PRT', output_field=CharField())).filter(
        email__icontains=search).exclude(EM_ADS_LOC_PRT__exact='', EM_ADS_DMN_PRT__exact='').values_list(
        'ID_EM_ADS', flat=True)
    filterqueries = PartyContactMethod.objects.filter(
        Q(ID_EM_ADS__in=email_id) & Q(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=False) & Q(
            ID_EM_ADS__EM_ADS_DMN_PRT__isnull=False) & Q(
            CD_STS='A')).values_list('ID_PRTY_RO_ASGMT', flat=True)
    filterquery.add(Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY__in=list(Person.objects.filter(
        employee_name_query).values_list('ID_PRTY', flat=True))) | Q(
        ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=list(filterqueries))
        | Q(
        ID_WRKR__in=list(
            WorkerOperatorAssignment.objects.filter(Q(ID_OPR__NM_USR__icontains=search)).values_list(
                'ID_WRKR', flat=True)))
        | Q(
        ID_WRKR__in=list(
            WorkerPositionAssignment.objects.filter(Q(ID_PST__NM_TTL__icontains=search)).values_list(
                'ID_WRKR', flat=True)))
        | Q(ID_WRKR__in=list(WorkerPositionAssignment.objects.filter(
            Q(ID_PST__department_id__name__icontains=search)).values_list('ID_WRKR', flat=True)))
        | Q(ID_WRKR__in=list(WorkerOperatorAssignment.objects.filter(
            Q(ID_OPR__in=OperatorGroup.objects.filter(ID_GP_WRK__NM_GP_WRK__icontains=search).values_list('ID_OPR',
                                                                                                          flat=True)
              )).values_list('ID_WRKR', flat=True))) |
        Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=PartyContactMethod.objects.filter(
            ID_PH__in=Telephone.objects.filter(TL_PH=search).values_list('ID_PH',
                                                                         flat=True)).values_list(
            'ID_PRTY_RO_ASGMT', flat=True)) |
        Q(ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY_RO_ASGMT__in=PartyContactMethod.objects.filter(
            ID_PH__in=Telephone.objects.filter(PH_CMPL=search).values_list('ID_PH',
                                                                           flat=True)).values_list(
            'ID_PRTY_RO_ASGMT', flat=True)) |
        Q(UPDT_DT__date__icontains=search) |
        Q(CRT_DT__date__icontains=search) |
        Q(ID_USR_CRT__in=list(User.objects.annotate(
            full_name=Concat('first_name', Value(' '), 'last_name',
                             output_field=CharField())).filter(
            full_name__icontains=search).values_list('id', flat=True))) |
        Q(ID_USR_UPDT__in=list(User.objects.annotate(
            full_name=Concat('first_name', Value(' '), 'last_name',
                             output_field=CharField())).filter(
            full_name__icontains=search).values_list('id', flat=True))),
        Q.AND)


def employee_filter(business_unit_query, page, page_size, search=None, request_data=None, ordering=None):
    '''Employee Filter'''
    if search == '':
        search = None
    filterquery = Q()
    employee_name_query = Q()
    limit = int(page_size)
    page = int(page)
    offset = (page - 1) * limit
    flags = True
    if request_data is not None:
        filterquery, flags = get_data_for_employee_filtering(
            request_data, filterquery, flags)
    if search is not None:
        get_employee_search_query(filterquery, search, employee_name_query)
    ordering_list_name = ['EM_ADS', '-EM_ADS',
                          'employee_name', '-employee_name', 'ID_USR_CRT', '-ID_USR_CRT', 'ID_USR_UPDT', '-ID_USR_UPDT']
    temp_ordering = deepcopy(ordering)
    if ordering is not None and ordering != '':
        ordering = order_employees(ordering)
    else:
        ordering = '-ID_EM'
    if flags:
        if business_unit_query is not None:
            employee_data = Employee.objects.filter(
                Q(business_unit_query) & Q(filterquery)).order_by(ordering)
        else:
            if temp_ordering in ordering_list_name:
                employee_data = Employee.objects.filter(
                    Q(filterquery)).order_by(*ordering)
            else:
                employee_data = Employee.objects.filter(
                    Q(filterquery)).order_by(ordering)
        count = employee_data.count()
        response_data = employee_data[offset:offset + limit]
        response_data = EmployeeListSerializer(
            response_data, many=True).data
    else:
        count = 0
        response_data = []
    return response_data, count


def order_employees(ordering):
    ''' Order Employee List '''
    if ordering == 'EM_ADS':
        ordering1 = ordering.replace(
            'EM_ADS', 'ID_WRKR__ID_PRTY_RO_ASGMT__party_contact_method_ID_PRTY_RO_ASGMT__ID_EM_ADS__EM_ADS_LOC_PRT')
        ordering2 = ordering.replace(
            'EM_ADS', 'ID_WRKR__ID_PRTY_RO_ASGMT__party_contact_method_ID_PRTY_RO_ASGMT__ID_EM_ADS__EM_ADS_DMN_PRT')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == '-EM_ADS':
        ordering1 = ordering.replace(
            '-EM_ADS', '-ID_WRKR__ID_PRTY_RO_ASGMT__party_contact_method_ID_PRTY_RO_ASGMT__ID_EM_ADS__EM_ADS_LOC_PRT')
        ordering2 = ordering.replace(
            '-EM_ADS', '-ID_WRKR__ID_PRTY_RO_ASGMT__party_contact_method_ID_PRTY_RO_ASGMT__ID_EM_ADS__EM_ADS_DMN_PRT')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == 'employee_name':
        ordering1 = ordering.replace(
            'employee_name', 'ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__FN_PRS')
        ordering2 = ordering.replace(
            'employee_name', 'ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__LN_PRS')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == '-employee_name':
        ordering1 = ordering.replace(
            '-employee_name', '-ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__FN_PRS')
        ordering2 = ordering.replace(
            '-employee_name', '-ID_WRKR__ID_PRTY_RO_ASGMT__ID_PRTY__person_party_id__LN_PRS')
        ordering = [ordering1, ordering2]
        return ordering
    ordering = ordering.replace(
        'position_name', 'ID_WRKR__worker_position_assignment_worker_id__ID_PST__NM_TTL')
    ordering = ordering.replace(
        '-position_name', '-ID_WRKR__worker_position_assignment_worker_id__ID_PST__NM_TTL')
    ordering = ordering.replace(
        'operator', 'ID_WRKR__worker_operator_assignment_worker_id__ID_OPR__NM_USR')
    ordering = ordering.replace(
        '-operator', '-ID_WRKR__worker_operator_assignment_worker_id__ID_OPR__NM_USR')
    ordering = ordering.replace(
        'department_name', 'ID_WRKR__worker_position_assignment_worker_id__ID_PST__department_id__name')
    ordering = ordering.replace(
        '-department_name', '-ID_WRKR__worker_position_assignment_worker_id__ID_PST__department_id__name')
    ordering = ordering.replace(
        'PH_CMPL', 'ID_WRKR__ID_PRTY_RO_ASGMT__party_contact_method_ID_PRTY_RO_ASGMT__ID_PH__PH_CMPL')
    ordering = ordering.replace(
        '-PH_CMPL', '-ID_WRKR__ID_PRTY_RO_ASGMT__party_contact_method_ID_PRTY_RO_ASGMT__ID_PH__PH_CMPL')
    ordering = ordering.replace(
        'permission_set', 'ID_WRKR__worker_operator_assignment_worker_id__ID_OPR__operator_group_operator_id__ID_GP_WRK__NM_GP_WRK')
    ordering = ordering.replace(
        '-permission_set', '-ID_WRKR__worker_operator_assignment_worker_id__ID_OPR__operator_group_operator_id__ID_GP_WRK__NM_GP_WRK')
    if ordering == 'ID_USR_CRT':
        ordering1 = ordering.replace(
            'ID_USR_CRT', 'ID_USR_CRT__first_name')
        ordering2 = ordering.replace(
            'ID_USR_CRT', 'ID_USR_CRT__last_name')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == '-ID_USR_CRT':
        ordering1 = ordering.replace(
            '-ID_USR_CRT', '-ID_USR_CRT__first_name')
        ordering2 = ordering.replace(
            '-ID_USR_CRT', '-ID_USR_CRT__last_name')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == 'ID_USR_UPDT':
        ordering1 = ordering.replace(
            'ID_USR_UPDT', 'ID_USR_UPDT__first_name')
        ordering2 = ordering.replace(
            'ID_USR_UPDT', 'ID_USR_UPDT__last_name')
        ordering = [ordering1, ordering2]
        return ordering
    if ordering == '-ID_USR_UPDT':
        ordering1 = ordering.replace(
            '-ID_USR_UPDT', '-ID_USR_UPDT__first_name')
        ordering2 = ordering.replace(
            '-ID_USR_UPDT', '-ID_USR_UPDT__last_name')
        ordering = [ordering1, ordering2]
        return ordering
    return ordering
