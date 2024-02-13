from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from .models import Reason
from .serializers import ReasonSerializer, ReasonPostSerializer, ReasonStatusSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, views
from copy import deepcopy
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from order.crate_filter import reason_filter

invalid_id_key = "Invalid Id"

class ReasonAPIView(GenericAPIView, mixins.CreateModelMixin, mixins.ListModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    search_fields = ['RN_CD', 'RN_STD',
                     'IS_VISIBLE', 'RN_STS']
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]

    queryset = Reason.objects.all().order_by('-RN_ID')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ReasonSerializer
        return ReasonPostSerializer

    def __init__(self):
        self.columns = {
            "RN_STS": "Status",
            "RN_CD": "Reason Code",
            "RN_STD": "Reason Statement",
            "IS_VISIBLE": "Visibility",
            "CRT_DT": "Created Date & Time",
            "CRT_BY_NM": "Created By",
            "UPDT_DT": "Updated Date & Time",
            "MDF_BY_NM": "Updated By"
        }
        self.column_type = {
            "RN_STS": "status",
            "RN_CD": "str",
            "RN_STD": "str",
            "IS_VISIBLE": "str",
            "CRT_DT": "Datetime",
            "CRT_BY_NM": "str",
            "UPDT_DT": "Datetime",
            "MDF_BY_NM": "str"
        }

    def get(self, request, *args, **kwargs):
        '''
        search, page_size, page
        '''

        reason_id = self.request.GET.get('RN_ID')
        search = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', 10)

        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('page', None)
        copy_request_data.pop('search', None)
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('RN_ID', None)
        copy_request_data.pop('page_size', None)

        if reason_id is not None:
            try:
                queryset = Reason.objects.get(RN_ID=reason_id)
                response_data = ReasonSerializer(queryset).data
                response_data.pop('links', None)
            except Reason.DoesNotExist:
                response_data = {"message": "No data found"}
            return Response(response_data)
        if (len(copy_request_data) > 0 and reason_id is None) or (len(search) > 0 or request.GET.get('ordering') is not None):
            response = reason_filter(int(page), int(
                page_size), search, copy_request_data)
            response = {
                "page": int(page),
                "total": response[1],
                "results": response[0],
                "page_size": int(page_size),
                "column_type": self.column_type,
                "columns": self.columns
            }
            return Response(response, status=status.HTTP_200_OK)
        result = self.list(request, *args, **kwargs).data
        result["page_size"] = int(page_size)
        result["page"] = int(page)
        result['columns'] = self.columns
        result['column_type'] = self.column_type
        result.pop('links', None)
        return Response(result)

    def post(self, request, *args, **kwargs):

        try:
            data = request.data
            reason_code = data.get('RN_CD')
            visibility = data.get('IS_VISIBLE')
            state = data.get('RN_STS')
            reason_std = data.get('RN_STD', '')
            current_user_id = request.user
            created_by = current_user_id.id
            
            if Reason.objects.filter(RN_CD__iexact=reason_code).exists():
                response = {
                            "message": f"Reason with code {reason_code} already exists",
                            "RN_CD": "already exists"
                            }
                stat = status.HTTP_409_CONFLICT
            else:
                reason_data = {
                    'IS_VISIBLE': visibility,
                    'RN_CD': reason_code,
                    'RN_STD': reason_std,
                    'RN_STS': state,
                    "CRT_BY": created_by,
                }
                serializer = ReasonPostSerializer(data=reason_data)
                if serializer.is_valid():
                    serializer.save()
                    response = {"message": "Reason Created Successfully"}
                    stat = status.HTTP_201_CREATED
                else:
                    response = {"message": "Invalid Data Provided"}
                    stat = status.HTTP_400_BAD_REQUEST
            return Response(response, status=stat)

        except Exception as e:
            return Response({"message": repr(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReasonUpdateAPIView(GenericAPIView, mixins.UpdateModelMixin):
    serializer_class = ReasonSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        '''retrive method'''
        reason_id = self.kwargs.get('pk')
        query = Reason.objects.filter(
            RN_ID=reason_id)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj

    def put(self, request, *args, **kwargs):
        '''Update Reason'''
        data = request.data
        current_user = request.user.id
        data['UPDT_BY'] = current_user
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({"message": "Reason Updated Successfully"})
        except Exception as e:
            return Response({"message": repr(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReasonStatusUpdate(views.APIView):
    '''Reason status update'''

    def validate_ids(self, id_list):
        '''Reason validate id'''
        for each_id in id_list:
            try:
                Reason.objects.get(RN_ID=each_id)
            except (Reason.DoesNotExist, ValidationError):
                return False
        return True

    def put(self, request, *args, **kwargs):
        '''Reason multiple status update'''
        id_list = request.data['ids']
        status_val = request.data['status']
        current_user = request.user
        chk_stat = self.validate_ids(id_list=id_list)
        if chk_stat:
            instances = []
            for each_id in id_list:
                obj = Reason.objects.get(RN_ID=each_id)
                obj.RN_STS = status_val
                obj.UPDT_BY = current_user
                obj.save()
                instances.append(obj)
            serializer = ReasonStatusSerializer(instances, many=True)
            return Response(serializer.data, *args, **kwargs)
        else:
            response_data = {}
            response_data["message"] = invalid_id_key
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class ReasonDeleteAPIView(GenericAPIView, mixins.DestroyModelMixin):

    def validate_ids(self, id):
        '''Reason validate id'''
        for each_id in id:
            try:
                Reason.objects.get(RN_ID=each_id)
            except (Reason.DoesNotExist, ValidationError):
                return False
        return True

    def delete(self, request):
        '''Reason delete'''
        reason_id = request.data['ids']
        chk_stat = self.validate_ids(id=reason_id)
        if chk_stat:
            for each_id in reason_id:
                Reason.objects.filter(RN_ID=each_id).delete()
            return Response({"message": "Reason Deleted Successfully"}, status=status.HTTP_200_OK)
        else:
            response_data = {}
            response_data["message"] = invalid_id_key
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

