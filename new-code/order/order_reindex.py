import logging
import os
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from celery import shared_task

from drf_yasg.utils import swagger_auto_schema
from collections import deque
from elasticsearch import helpers
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from dnbadmin.elastic_conf import es
from order.models import OrderMaster
from order.serializers import OrderElasticDataSerializer
from order.order_create_index import mapping_for_order_index

logger = logging.getLogger(__name__)


@shared_task
def reindx_for_order(user_id):
    '''Reindex the order elastic'''
    if es.indices.exists(index=settings.ES_ORDER_INDEX):
        es.indices.delete(settings.ES_ORDER_INDEX)
        logger.info("Order index deleted from elastic")
    if not es.indices.exists(index=settings.ES_ORDER_INDEX):
        mapping_for_order_index(settings.ES_ORDER_INDEX)
    order_instance = OrderMaster.objects.all().order_by('-OD_ID')
    bulk_order_data_list = []
    for order_data in order_instance:
        serialzied_data = OrderElasticDataSerializer(
            order_data).data
        elastic_data_dict = {
            "_index": settings.ES_ORDER_INDEX,
            "_id": order_data.OD_ID,
            "_source": serialzied_data
        }
        bulk_order_data_list.append(elastic_data_dict)
        if len(bulk_order_data_list) == 500:
            bulk = helpers.parallel_bulk(es, bulk_order_data_list)
            dq = deque(bulk, maxlen=0)
            logger.info("Deques : %s", dq)
            bulk_order_data_list = []
    bulk = helpers.parallel_bulk(es, bulk_order_data_list)
    dq = deque(bulk, maxlen=0)
    logger.info("Deque : %s", dq)
    user_email = User.objects.get(id=user_id).email
    logger.info("User Email : %s", user_email)
    message = "Order Reindexing Successfully Done."
    subject = 'Order Reindexing'
    from_email = os.getenv('MAIL')
    mail = EmailMessage(
        subject, message, from_email, [str(user_email)])
    mail.send()
    logger.info("Mail Response : %s", mail)


class OrderReindexView(GenericAPIView):
    '''Order reindex view in elastic'''
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['Order Reindex'], operation_description="Order Reindex", operation_summary="Order Reindex")
    def get(self, request, *args, **kwargs):
        '''Get api for order reindex'''
        logger.info("Order reindex in elastic")
        user_id = request.user.id
        reindx_for_order.delay(user_id)
        return Response({"message": "Order reindexing is running in background."})
