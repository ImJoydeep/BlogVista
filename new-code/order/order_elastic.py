from copy import deepcopy
import logging
from django.conf import settings
from accesscontrol.models import Operator, OperatorBusinessUnitAssignment
from dnbadmin.elastic_conf import es
from order.order_create_index import mapping_for_order_index
logger = logging.getLogger('__name__')


def order_save(data, index_name, order_id):
    '''Order save into elastic'''
    if not es.indices.exists(index=index_name):
        mapping_for_order_index(index_name)
    elastic_response = es.index(index=index_name, doc_type=settings.ELASTICSEARCH_DOC_TYPE,
                                id=order_id, body=data)
    return elastic_response


def get_order_by_id(index_name, data_id):
    '''Get order from elasticsearch'''
    elastic_response_data = es.get(
        index=index_name,
        id=data_id
    )
    return elastic_response_data


def delete_order_from_elastic(index_name, ids):
    '''Delete order from elasticsearch'''
    if get_order_by_id(index_name, ids) is not None:
        es.delete(index=index_name,
                  doc_type=settings.ELASTICSEARCH_DOC_TYPE, id=ids)


keyword_string = ".keyword"
all_data_key = "all_data."
common_status_type_key = "all_data.OMS_OD_STS.keyword"
ready_to_pick_key = 'Ready to Pick'
store_name_key = "all_data.OD_STR_NM.keyword"


def get_less_than_for_date_field_query(col_name, col_val):
    '''Get the less than query for date field'''
    data = {
        "range": {
            str(col_name)+keyword_string: {
                "lt": col_val
            }
        }
    }
    return data


def get_greater_equal_for_date_field_query(i, col_name, col_val):
    '''Get the greater equal query for date field'''
    if i == 'OD_DATE':
        data = {
            "range": {
                str(col_name)+keyword_string: {
                    "gte": col_val
                }
            }
        }
    else:
        data = {
            "range": {
                str(col_name): {
                    "gte": eval(col_val)
                }
            }
        }
    return data


def get_equal_filter_query(i, col_name, col_val):
    '''Get equal filter query'''
    if i == 'OD_DATE':
        data = {"wildcard": {str(col_name)+str(keyword_string): {"value": "*" + col_val + "*",
                                                                 "case_insensitive": True}}}
    else:
        try:
            if isinstance(eval(col_val), int) or isinstance(eval(col_val), float):
                data = {
                    'term': {str(col_name): col_val}}
        except Exception:
            data = {"wildcard": {str(col_name)+str(keyword_string): {"value": "" + col_val + "",
                                                                     "case_insensitive": True}}}
    return data


def get_not_equal_filter_query(col_name, i, col_val):
    '''Get not equal query'''
    if i == 'OD_DATE':
        data = {"wildcard": {str(col_name)+str(keyword_string): {"value": "*" + col_val + "*",
                                                                 "case_insensitive": True}}}
    else:
        try:
            if isinstance(eval(col_val), int) or isinstance(eval(col_val), float):
                data = {'match': {str(col_name): col_val}}
        except Exception:
            data = {"wildcard": {str(col_name)+str(keyword_string): {"value": "" + col_val + "",
                                                                     "case_insensitive": True}}}
    return data


def create_elastic_query_for_filter(col_type, col_val, i, col_name, must_query, must_not_query):
    '''Create elastic query for filtering'''
    field_list = ['all_data.OD_QTY']
    if str(col_type) == 'equals':
        data = get_equal_filter_query(i, col_name, col_val)
        must_query.append(data)

    elif str(col_type) == 'not-equals':
        data = get_not_equal_filter_query(col_name, i, col_val)
        must_not_query.append(data)
    elif str(col_type) == 'contains':
        if col_name in field_list:
            data = {
                "query_string": {
                    "fields": [
                        col_name+str(keyword_string)
                    ],
                    "query": f"*{col_val}*",
                    "default_operator": "and"
                }
            }
        else:
            data = {"wildcard": {str(col_name)+str(keyword_string): {"value": "*" + col_val + "*",
                                                                     "case_insensitive": True}}}
        must_query.append(data)
    elif str(col_type) == 'end-with':
        data = {"wildcard": {str(col_name)+str(keyword_string): {"value": "*" + col_val,
                                                                 "case_insensitive": True}}}
        must_query.append(data)
    elif str(col_type) == 'start-with':
        data = {"wildcard": {str(col_name)+str(keyword_string): {"value": col_val + "*",
                                                                 "case_insensitive": True}}}
        must_query.append(data)

    elif str(col_type) == 'greater-than':
        data = {
            "range": {
                str(col_name): {
                    "gt": eval(col_val)
                }
            }
        }
        must_query.append(data)
    elif str(col_type) == 'not-contains':
        data = {"wildcard": {str(col_name)+str(keyword_string): {"value": "*" + col_val + "*",
                                                                 "case_insensitive": True}}}
        must_not_query.append(data)
    elif str(col_type) == 'greater-equal':
        data = get_greater_equal_for_date_field_query(i, col_name, col_val)
        must_query.append(data)
    elif str(col_type) == 'less-than':
        data = get_less_than_for_date_field_query(col_name, col_val)
        must_query.append(data)
    return must_query, must_not_query


def get_column_val_column_type_and_query(requested_datas, i, col_names, must_query, must_not_query):
    '''get column values and type with filter queries'''
    if len(requested_datas[i][0]) > 0:
        splited_datas = requested_datas[i][0].split(',')
        logger.info("Split Data: %s", splited_datas)
        if len(splited_datas) > 1:
            col_type = splited_datas[-1]
            logger.info("col_types: %s", col_type)
            splited_datas.pop(-1)
            col_val = ','.join(splited_datas)
        else:
            col_type = 'equals'
            col_val = requested_datas[i][0]

    logger.info("Column Values : %s and Type : %s", col_val, col_type)
    if col_val is not None and len(col_val) > 0:
        must_query, must_not_query = create_elastic_query_for_filter(
            col_type, col_val, i, col_names, must_query, must_not_query)
    return must_query, must_not_query


def get_must_query_for_app_store_wise_order(must_query, copy_request_data, store_list):
    '''Must query for app store wise order'''
    if copy_request_data.get('OD_STR_NM'):
        if copy_request_data.get('OD_STR_NM')[0] in store_list:
            must_query.append(
                {
                    "terms": {
                        store_name_key: copy_request_data.get('OD_STR_NM')
                    }
                }
            )
        else:
            must_query.append(
                {
                    "terms": {
                        store_name_key: store_list
                    }
                }
            )
    else:
        must_query.append(
            {
                "terms": {
                    store_name_key: store_list
                }
            }
        )
    return must_query


def get_filter_and_search_query(search, request_data, status_filter, device, username):
    '''elastic search query for listing'''
    search_query = {}
    must_query = []
    must_not_query = []
    should_query = []
    filter_query = []
    copy_request_data = deepcopy(request_data)
    if device:
        request_data.pop('OD_STR_NM', None)
    if request_data is not None and len(request_data) > 0:
        logger.info("Request Data: %s", request_data)
        for i in request_data:
            col_name = all_data_key+i
            logger.info("Column Name : %s", col_name)
            must_query, must_not_query = get_column_val_column_type_and_query(
                request_data, i, col_name, must_query, must_not_query)
    if device:
        store_list = []
        op_instance = Operator.objects.filter(
            NM_USR__iexact=username)
        if op_instance.exists():
            store_list = list(OperatorBusinessUnitAssignment.objects.filter(
                ID_OPR=op_instance.first().ID_OPR).values_list('ID_LCN__MAG_MAGEWORX_STR_NM', flat=True))
        must_query = get_must_query_for_app_store_wise_order(
            must_query, copy_request_data, store_list)
        must_query.append(
            {
                "terms": {
                    common_status_type_key: [
                        ready_to_pick_key, 'Picking', 'New']
                }
            }
        )
    if status_filter in ['new', 'rtp', 'pickup', 'void', 'oh', 'cmp']:
        if status_filter == 'rtp':
            must_query.append(
                {
                    "terms": {
                        common_status_type_key: [ready_to_pick_key, 'Picking']
                    }
                }
            )
        else:
            status_filter = status_filter.replace('new', 'New')
            status_filter = status_filter.replace('void', 'Void')
            status_filter = status_filter.replace('pickup', 'Ready for Pickup')
            status_filter = status_filter.replace('oh', 'Attention')
            status_filter = status_filter.replace('cmp', 'Completed')
            must_query.append(
                {
                    "term": {
                        common_status_type_key: status_filter
                    }
                }
            )
    if search is not None and len(search) > 0:
        search = str(search).replace('$', ' ')
        search = str(search).replace('/', ' ')
        search = str(search).replace('%', ' ')
        search = str(search).replace(',', ' ')
        search = str(search).replace('&', ' ')
        search = str(search).replace('?', ' ')
        search = str(search).replace('#', ' ')
        search_query = {
            "query_string": {
                "fields": [
                    "all_data.CU_OD_ID.keyword",
                    "all_data.OD_BA_CT",
                    "all_data.OD_BA_ST",
                    "all_data.OD_CUS_EMAIL.keyword",
                    "all_data.OD_CUS_NM",
                    "all_data.OD_DATE.keyword",
                    "all_data.OD_DIS_AMT.keyword",
                    "all_data.OD_INST.keyword",
                    "all_data.OD_ITM_AMT_REF.keyword",
                    "all_data.OD_NT_AMT.keyword",
                    "all_data.OD_PD_AMT.keyword",
                    "all_data.OD_SA_CT.keyword",
                    "all_data.OD_SA_PIN.keyword",
                    "all_data.OD_BA_PIN.keyword",
                    "all_data.OD_SA_ST",
                    "all_data.OD_STR_NM",
                    "all_data.OD_TL_AMT.keyword",
                    "all_data.OD_TX_AMT.keyword",
                    "all_data.OD_TYPE",
                    "all_data.OMS_OD_STS",
                    "all_data.PT_MD_NM",
                    "all_data.OD_QTY.keyword",
                    "all_data.OD_SA_PH.keyword",
                    "all_data.OD_PICK_BY",
                    "all_data.OD_SHIP_CODE"
                ],
                "query": f"*{str(search)}*",
                "default_operator": "and"
            }
        }
        must_query.append(search_query)

    search_query = {
        "bool": {
            "must": must_query,
            "must_not": must_not_query,
            "should": should_query,
            "filter": filter_query
        }
    }

    return search_query


def get_order_list_from_elastic(index_name, page, page_size, status_filter, search, request_data, device, ordering, username):
    '''Get order listing from elastic'''
    order_all_data_list = []
    limit = int(page_size)
    page = int(page)
    offset = (page - 1) * limit
    orderby = "all_data.OD_DATE.keyword"
    order = "DESC"
    total_count = 0

    date_type_ordering = ["OD_QTY", "OD_TL_AMT", "OD_NT_AMT",
                          "OD_DIS_AMT", "OD_TX_AMT", "OD_PD_AMT", "OD_ITM_AMT_REF"]
    orderby_data = None
    if ordering:
        orderby_data = ordering
        order = "ASC"
        if orderby_data[0] == '-':
            orderby_data = orderby_data[1:]
            order = "DESC"
        if orderby_data in date_type_ordering:
            orderby = {
                "_script": {
                    "type": "number",
                    "script": {
                        "source": f"Double.parseDouble(doc['{all_data_key+orderby_data+keyword_string}'].value)",
                        "lang": "painless"
                    },
                    "order": order
                }
            }
        else:
            orderby = {
                all_data_key+str(orderby_data)+keyword_string: {
                    "order": order
                }
            }
    else:
        orderby = {
            orderby: {
                "order": order
            }
        }

    search_query = get_filter_and_search_query(
        search, request_data, status_filter, device, username)
    body = {
        "query": search_query,
        "from": offset,
        "size": limit,
        "sort": [orderby],
        "aggs": {},
        "track_total_hits": True
    }
    logger.info("Body: %s", body)
    try:
        res = es.search(index=index_name, body=body)
        result = res['hits']['hits']
        total_count = res['hits']['total']['value']
        for i in result:
            order_all_data_list.append(i['_source'].get('all_data'))

    except Exception as exp:
        logger.exception("Order Elastic Get Exception : %s", exp)
    return order_all_data_list, total_count
