from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError
from .serializers import EmailTemplateListSerializer, EmailTempRetrieveSerializer, EmailTemplateCreateSerializer, \
EmailTempUpdateSerializer, EmailFieldTypeRetrieveSerializer, EmailFieldTypeListSerializer, CategoryListSerializer,\
TemplateActionListSerializer, LocationListSerializer, DeliveryChannelListSerializer

from drf_yasg import openapi
from .models import EmailTemplate, EmailFieldType, EmailAction, Category, TemplateAction, TemplateActionMapping,\
    Location, DeliveryChannel
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import filters
from .responder_filter  import template_list_filter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import (
    mixins,
    generics,
    views,
    permissions,
    filters,
    status,
    parsers,
    renderers
)
from django.shortcuts import get_object_or_404, render
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class EmailTemplateSettingCreate(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
    '''global setting create,list,get,delete'''
    queryset = EmailTemplate.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = '__all__'
    ordering = '-ET_ID'

    def __init__(self):
        self.columns = {"ET_NM": "Email Template Name",
                        "SC_ET": "Status",
                        "ET_SB": "Subject",
                        "ET_FRM_EMAIL": "From Email",
                        "ET_TO_EMAIL": "Email to Send",
                        "ET_RPLY_TO_EMAIL": "Reply To Email",
                        "ET_BCC_EMAIL": "Bcc Email",
                        "ET_INTERVAL": "Time Interval",
                        "ET_OD_STS": "Order Status",
                        "ET_TM_DF": "Time Definition",
                        "ET_AU_RSP_FR": "Auto Responder Applied For",
                        "ET_USR_CRT": "Created By", "CRT_DT": "Created Date & Time", "ET_USR_UPDT": "Updated By",
                        "UPDT_DT": "Updated Date & Times"}
        self.column_type = {"SC_ET": "status", "ET_NM": "str", "ET_OD_STS": "str", "ET_SB": "str",
                            "ET_FRM_EMAIL": "str", "ET_TO_EMAIL": "str", "ET_TM_DF": "str", "ET_INTERVAL": "str",
                            "ET_RPLY_TO_EMAIL": "str", "ET_BCC_EMAIL": "str", "ET_AU_RSP_FR": "str",
                            "ITM_WISE_OD_PROC": "str", "POSTAL_CD_LGH": "int", "BSN_UN_NM": "str", "STR_NM": "str",
                            "ET_USR_CRT": "str", "CRT_DT": "Datetime", "ET_USR_UPDT": "str",
                            "UPDT_DT": "Datetime"}

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmailTemplateCreateSerializer
        return EmailTemplateListSerializer


    @swagger_auto_schema(tags=['Auto Responder'],
                         operation_description="Add email template", operation_summary="Add email template")
    def post(self, request, *args, **kwargs):
        '''global setting create'''
        response = {}
        template_name = request.data.get("ET_NM")
        if EmailTemplate.objects.filter(ET_NM__iexact=template_name).exists():
            response["message"] =  "Template already exist with same name"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            return self.create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = EmailTemplate.objects.filter(is_deleted=False)
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['columns'] = self.columns
        response.data['column_type'] = self.column_type

        return response

    gsetting_params = [
        openapi.Parameter("ET_ID",
                          openapi.IN_PATH,
                          description="Email template ID",
                          type=openapi.TYPE_INTEGER
                          )
    ]

    @swagger_auto_schema(tags=['Auto Responder'],
                         operation_description="email template retrieve",
                         operation_summary="email template retrieve list object")
    def get(self, request, *args, **kwargs):
        '''Email template list'''
        response = {}

        queryset = EmailTemplate.objects.filter(is_deleted=False).order_by("-ET_ID")
        search = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', queryset.count())
        page = int(page)
        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('page', None)
        copy_request_data.pop('page_size', None)
        copy_request_data.pop('search', None)



        if len(copy_request_data) > 0 or (len(search) > 0 or request.GET.get('ordering') is not None):
            response_data = template_list_filter(
                int(page), int(page_size), search, copy_request_data, request.GET.get('ordering'))
            response["columns"] = self.columns
            response["column_type"] = self.column_type
            response["page"] = int(page)
            response["page_size"] = int(page_size)
            response["results"] = response_data[0]
            response["total"] = response_data[1]
            return Response(response, status=status.HTTP_200_OK)
        else:
            return self.list(request,*args,**kwargs)

class EmailTemplateStatusUpdate(generics.GenericAPIView):
    queryset = EmailTemplate.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def createStatUpdtMssg(self, succ_cnt, fail_cnt):
        success_message = ""
        failure_message = ""

        if succ_cnt == 1:
            success_message = f"status succesfully updated for {succ_cnt} item"
        elif succ_cnt > 1:
            success_message = f"status succesfully updated for {succ_cnt} items"

        if fail_cnt == 1:
            failure_message = f"failed to update status for {fail_cnt} item"
        elif fail_cnt > 1:
            failure_message = f"failed to update status for {fail_cnt} items"

        if success_message and failure_message:
            return f"{success_message} and {failure_message}"
        elif success_message or failure_message:
            return f"{success_message}{failure_message}"
        else:
            return "no status updated"

    def updateValidator(self, template_id, template_status):
        msg_od_id = ""
        msg_od_sts = ""
        if template_id is None:
            msg_od_id = "order id is missing, please enter order id"
        if template_status is None or len(template_status) == 0:
            msg_od_sts = "order status is missing, please enter order status to update"
        if msg_od_id and msg_od_sts:
            return f"{msg_od_id} and {msg_od_sts}"
        elif msg_od_id or msg_od_sts:
            return f"{msg_od_id}{msg_od_sts}"
        else:
            return True

    template_params = [
        openapi.Parameter("ET_ID",
                          openapi.IN_QUERY,
                          description="Template Id",
                          type=openapi.TYPE_INTEGER
                          ),
        openapi.Parameter("SC_ET",
                          openapi.IN_QUERY,
                          description="Email Template status",
                          type=openapi.TYPE_STRING
                          )
    ]

    @swagger_auto_schema(tags=['Auto Responder'], operation_description="multiple status update auto responder",
                         operation_summary="auto responder multiple status update", request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of Ids',
                                      items=openapi.Items(type=openapi.TYPE_STRING, description='email template Id')),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='email template status (A/I)'),
            }, required=['ids', 'status']
        ))
    def put(self, request, *args, **kwargs):
        logger.info("Email Template Status Update Data : %s", request.data)
        template_id = request.data['ids']
        template_status = request.data['status']
        msg = ""
        fail_cnt = 0
        succ_cnt = 0

        validator_msg = self.updateValidator(template_id, template_status)
        if validator_msg == True:
            try:
                for id in template_id:
                    data = self.queryset.get(ET_ID=id)
                    data.SC_ET = template_status
                    data.save()
                    succ_cnt += 1
            except Exception:
                fail_cnt += 1
            msg += self.createStatUpdtMssg(succ_cnt, fail_cnt)
            return Response({"message": msg}, status=status.HTTP_200_OK)
        else:
            return Response({"message": msg}, status=status.HTTP_400_BAD_REQUEST)

template_params = [
        openapi.Parameter("templateId",
                          openapi.IN_PATH,
                          description="Email Template id",
                          type=openapi.TYPE_INTEGER
                          )
    ]

class EmailTemplateSettingRetrieveUpdate(mixins.UpdateModelMixin, mixins.RetrieveModelMixin, generics.GenericAPIView):
    serializer_class = EmailTempUpdateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "templateId"

    def get_queryset(self):
        '''retrieve method'''
        temp_id = self.kwargs.get(self.lookup_url_kwarg)
        query = EmailTemplate.objects.filter(
            ET_ID=temp_id, is_deleted=False)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj



    @swagger_auto_schema(tags=['Auto Responder'], manual_parameters=template_params,
                         operation_description="Email template retrieve",
                         operation_summary="Email template retrieve single object")

    def get(self, request, *args, **kwargs):
        template_id = kwargs.get('templateId')

        if template_id:
            try:
                obj = EmailTemplate.objects.get(ET_ID=template_id, is_deleted=False)
                serilizer = EmailTempRetrieveSerializer(obj).data
                stat = status.HTTP_200_OK
            except Exception as e:
                logger.exception("Email Template retrieve Exception : %s", e)
                serilizer = {'message': "item does not exist"}
                stat = status.HTTP_400_BAD_REQUEST
            return Response(serilizer, status=stat)
        '''email template retrieve'''
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Auto Responder'], operation_description="Edit email template",
                         operation_summary="Edit order global settings")
    def put(self, request, *args, **kwargs):
        '''department update method'''
        logger.info("Template Update Request Data : %s", request.data)
        response = {}
        template_name = request.data.get("ET_NM")
        if EmailTemplate.objects.filter(ET_NM__iexact=template_name).exclude(ET_ID=request.data.get("ET_ID")).exists():
            response["message"] =  "Template already exist with same name"
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        else:
            return self.update(request, *args, **kwargs)


class EmailTemplateDeleteMultipleView(APIView):
    '''global setting multiple delete'''
    def validate_ids(self, id_list):
        '''global setting validate id'''
        for each_id in id_list:
            try:
                EmailTemplate.objects.get(ET_ID=each_id)
            except (EmailTemplate.DoesNotExist, ValidationError):
                return False
        return True

    @swagger_auto_schema(tags=['Auto Responder'], operation_description="multiple delete email template",
                         operation_summary="Auto responder multiple delete", request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='Array of Ids',
                                              items=openapi.Items(type=openapi.TYPE_STRING,
                                              description='Email Template Id'))}, required=['ids']
        ))
    def delete(self, request, *args, **kwargs):
        delete_response = {}
        valid_count = 0
        invalid_count = 0

        id_list = request.data.get('ids', [])

        if len(id_list) < 1:
            return Response({'message': "no item selected"}, status=status.HTTP_400_BAD_REQUEST)

        for each_id in id_list:
            try:
                data = EmailTemplate.objects.filter(
                    ET_ID=each_id).exists()
                logger.info("Location object: %s", data)
                if data:
                    EmailTemplate.objects.filter(
                        ET_ID=each_id).delete()
                    valid_count += 1
                else:
                    invalid_count += 1
            except Exception as e:
                logger.exception("Email Template Delete Exception : %s", e)
                invalid_count += 1
        if valid_count != 0 and invalid_count != 0:
            delete_response['message'] = str(
                valid_count) + " Email Template deleted successfully and " + str(
                invalid_count) + " Email Template not updated."
        elif valid_count != 0:
            delete_response['message'] = str(
                valid_count) + " Email Templates deleted successfully"
        elif invalid_count != 0:
            delete_response['message'] = str(
                invalid_count) + " Email Template not deleted."
        return Response(delete_response, status=status.HTTP_200_OK)

class EmailFiledTypeList(mixins.RetrieveModelMixin, mixins.ListModelMixin, generics.GenericAPIView):
    '''global setting create,list,get,delete'''
    queryset = EmailFieldType.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ETY_CAT__CT_ID']
    ordering_fields = '__all__'
    ordering = '-ETY_ID'

    def __init__(self):
        self.columns = {"ETY_ID": "Field Type Table Id",
                        "ETY_NM_LABEL": "Email Field Label",
                        "ETY_VALUE": "Field Value",
                        "ETY_CAT": "Field Category"}
        self.column_type = {"ETY_NM_LABEL": "str", "ETY_VALUE": "str",
                            "ETY_CAT": "dict"}

    def get_serializer_class(self):
        return EmailFieldTypeListSerializer


    def get_queryset(self):
        queryset = EmailFieldType.objects.all()
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['columns'] = self.columns
        response.data['column_type'] = self.column_type

        return response

    gsetting_params = [
        openapi.Parameter("ETY_CAT__CT_ID",
                          openapi.IN_PATH,
                          description="Category ID",
                          type=openapi.TYPE_INTEGER
                          )
    ]

    @swagger_auto_schema(tags=['Auto Responder'],
                         operation_description="email field type retrieve",
                         operation_summary="email field type retrieve list object")
    def get(self, request, *args, **kwargs):
        '''Email template list'''
        response = {}
        category_id = request.GET.get('ETY_CAT__CT_ID')
        if category_id:
            try:
                obj = EmailFieldType.objects.filter(ETY_CAT=category_id)
                serilizer = EmailFieldTypeRetrieveSerializer(obj, many=True).data
                response["results"] = serilizer
                stat = status.HTTP_200_OK
            except Exception:
                serilizer = {'message': "item does not exist"}
                response["results"] = serilizer
                stat = status.HTTP_400_BAD_REQUEST
            return Response(response, status=stat)
        else:
            return self.list(request,*args,**kwargs)


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    '''category list'''
    @swagger_auto_schema(tags=['Auto Responder'], operation_description="category list",
                         operation_summary="Auto responder category list", request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ))
    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)

        return response


class TemplateActionView(generics.GenericAPIView):
    """
       A viewset that provides the standard actions to logged-in user
    """
    queryset = TemplateAction.objects.all()
    serializer_class = TemplateActionListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    @swagger_auto_schema(operation_summary="Order Action Type By Option",
                         query_serializer=TemplateActionListSerializer,
                         tags=['Auto Responder'])
    def get(cls, request, *args, **kwargs):
        type_data = request.query_params.get("TA_TYPE")
        action_type = TemplateAction.objects.filter(TA_TYPE=type_data)
        matchedurl_serializer = cls.serializer_class(action_type, many=True)
        if matchedurl_serializer:
            return Response({"status" : 1, "ActionList" : matchedurl_serializer.data})


class StoreListView(generics.ListAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    '''Store list'''
    @swagger_auto_schema(tags=['Auto Responder'], operation_description="Store/WareHouse list",
                         operation_summary="Auto responder store list", request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ))
    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)

        return response


class DeliveryChannelListView(generics.ListAPIView):
    queryset = DeliveryChannel.objects.all()
    serializer_class = DeliveryChannelListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    '''DeliveryChannel list'''
    @swagger_auto_schema(tags=['Auto Responder'], operation_description="DeliveryChannel list",
                         operation_summary="Auto responder DeliveryChannel list", request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
        ))
    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)

        return response