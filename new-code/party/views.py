''' Party Views File '''
import logging
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import filters
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from party.serializers import (ContactPurposeTypeSerializer, ContactMethodTypeSerializer,
                               ITUCountrySerializer, StateSerializer, LegalStatusTypeSerializer)
from party.models import (
    ContactPurposeType, ContactMethodType, ITUCountry, State, LegalStatusType)
# Create your views here.
logger = logging.getLogger(__name__)
application_json_examples = "application/json"
total_list_count_messages = "total list count"

CntPrpsTypeList_response_schema_dict = {
    "200": openapi.Response(
        description="Return Contact Purpose Type List",
        examples={
            application_json_examples: {
                "total": total_list_count_messages,
                "contactpurposetype_list": [
                    {
                        "code": "Contact Purpose Type Code",
                        "name": "Name for the code denoting a reason"
                    }
                ]
            }
        }
    )
}


class ContactPurposeTypeList(ListModelMixin, GenericAPIView):
    ''' Contact Purpose Type Views Class '''
    queryset = ContactPurposeType.objects.all()
    serializer_class = ContactPurposeTypeSerializer
    permission_classes = (AllowAny,)
    authentication_class = JWTAuthentication
    pagination_class = None

    @swagger_auto_schema(tags=['Employee Contact'], operation_description="Employee Contact Purpose List", operation_summary="Contact Purpose Type")
    def get(self, request, *args, **kwargs):
        ''' Get All Contact Purpose Type '''
        return self.list(request, *args, **kwargs)


CntMthdTypeList_response_schema_dict = {
    "200": openapi.Response(
        description="Return Contact Method List",
        examples={
            application_json_examples: {
                "total": total_list_count_messages,
                "contactmethodtype_list": [
                    {
                        "code": "Contact Method Type Code",
                        "name": "Name for the code denoting a Type"
                    }
                ]
            }
        }
    )
}


class ContactMethodTypeList(ListModelMixin, GenericAPIView):
    ''' Contact Method Type Views Class '''
    queryset = ContactMethodType.objects.all()
    serializer_class = ContactMethodTypeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_class = JWTAuthentication
    pagination_class = None

    @swagger_auto_schema(tags=['Employee Contact'], operation_description="Employee Contact Method List", operation_summary="Contact Method Type")
    def get(self, request, *args, **kwargs):
        ''' Get All Contact Purpose Type '''
        return self.list(request, *args, **kwargs)


CountryList_response_schema_dict = {
    "200": openapi.Response(
        description="Return Country List",
        examples={
            application_json_examples: {
                "total": total_list_count_messages,
                "country_list": [
                    {
                        "code": "ISO Country Code",
                        "name": "Country Name"
                    }
                ]
            }
        }
    )
}


class GetCountryList(ListModelMixin, CreateModelMixin, UpdateModelMixin, GenericAPIView):
    ''' Country List Views Class '''
    permission_classes = (AllowAny,)
    authentication_class = JWTAuthentication
    queryset = ITUCountry.objects.all().order_by('-CD_CY_ITU')

    def get_serializer_class(self):
        return ITUCountrySerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        return response

    @swagger_auto_schema(tags=['Country'],
                         operation_description="Country List",
                         operation_summary="Country List",
                         responses=CountryList_response_schema_dict)
    def get(self, request, *args, **kwargs):
        ''' Get Country List '''
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['Country'],
                         operation_description="Country Create",
                         operation_summary="Country Create")
    def post(self, request, *args, **kwargs):
        ''' Get Country List '''
        return self.create(request, *args, **kwargs)


class GetStateList(ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericAPIView):
    ''' State List View Class '''
    queryset = State.objects.all()
    permission_classes = (AllowAny,)
    authentication_class = JWTAuthentication
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['CD_CY_ITU', 'ID_ST']
    ordering = ['-ID_ST']

    def get_serializer_class(self):
        return StateSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        return response

    @swagger_auto_schema(tags=['State'], operation_description="get State list",
                         operation_summary="State list")
    def get(self, request, *args, **kwargs):
        ''' Get State List '''
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(tags=['State'], operation_description="State Create",
                         operation_summary="State list", request_body=StateSerializer(many=True))
    def post(self, request, *args, **kwargs):
        ''' State Create '''
        logger.info("State Request Data : %s", request.data)
        try:
            state_serializer = StateSerializer(data=request.data,many=True)
            if state_serializer.is_valid():
                state_serializer.save()
            else:
                logger.info("State Serializer Error : %s", state_serializer.errors)
            return Response({"message" : "State Successfully Created"})
        except Exception as exp:
            logger.exception(exp)
            return Response({"message" : "Server Error"})



class LegalStatusTypeList(ListModelMixin, GenericAPIView):
    ''' LegalStatusType Views Class '''
    queryset = LegalStatusType.objects.all().order_by('-ID_LGL_STS')
    serializer_class = LegalStatusTypeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_class = JWTAuthentication
    pagination_class = None

    @swagger_auto_schema(tags=['Legal Status Type'],
                         operation_description="Legal Status Type List",
                         operation_summary="Legal Status Type")
    def get(self, request, *args, **kwargs):
        ''' Get All LegalStatusType '''
        return self.list(request, *args, **kwargs)
