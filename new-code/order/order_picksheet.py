from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from .models import PicksheetNote, PicksheetNoteStores, PicksheetNoteItemSKU
from .serializers import PickSheetSerializer,PickSheetGetSerializer,PickSheetSKUSerializer, PickSheetPostSerializer,PickSheetItemSKUSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, views
from rest_framework.pagination import PageNumberPagination
from copy import deepcopy
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from store.models import Location
from product.models import Item
from order.picksheet_filter import picksheet_filter
from django.db.models import Q
from django.core.paginator import Paginator
from itertools import chain
invalid_id_key = "Invalid Id"


def required_checks(store_ids, item_ids):
    response = {}
    for store_id in store_ids:
        if not Location.objects.filter(id=store_id).exists():
            response = {"message": "Store Not Found"}
            return response

    for item_id in item_ids:
        if not Item.objects.filter(ID_ITM=item_id).exists():
            response = {"message": "SKU Not Found"}
            return response

    for item_id in item_ids:
        if PicksheetNoteItemSKU.objects.filter(ITM_SKU_ID=item_id).exists():
            response = {"message": "SKU already assigned, Try another SKU"}
            return response
    return response

def all_stores(store_ids):
    response = {}

    if not store_ids:
        queryset = Location.objects.filter(Q(MAG_MAGEWORX_STR_ID__isnull=False))
        response = list(queryset.values_list('id', flat=True))

    return response




class PicksheetNoteAPIView(GenericAPIView, mixins.CreateModelMixin, mixins.ListModelMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    search_fields = ['PSN_NM', 'PSN_VIS',
                     'NT_DETAILS', 'PSN_STS']
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]

    queryset = PicksheetNote.objects.all().order_by('-PSN_ID')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PickSheetSerializer
        elif self.request.method == 'POST':
            return PickSheetPostSerializer
        else:
            return PickSheetSerializer

    def __init__(self):
        self.columns = {
            "PSN_NM": "PickSheet Name",
            "PSN_STS": "Status",
            "ITM_SKU_ID": "Product SKU",
            "ST_DT": "Start Date",
            "EN_DT": "End Date",
            "STR_NM": "Stores",
            "PSN_VIS": "Visibility",
            "CRT_DT": "Created Date & Time",
            "CRT_BY_NM": "Created By",
            "UPDT_DT": "Updated Date & Time",
            "MDF_BY_NM": "Updated By"
        }
        self.column_type = {
            "PSN_NM": "str",
            "PSN_STS": "status",
            "ITM_SKU_ID": "str",
            "ST_DT": "Datetime",
            "EN_DT": "Datetime",
            "STR_NM": "str",
            "PSN_VIS": "str",
            "CRT_DT": "Datetime",
            "CRT_BY_NM": "str",
            "UPDT_DT": "Datetime",
            "MDF_BY_NM": "str"
        }

    def get(self, request, *args, **kwargs):
        '''
        search, page_size, page
        '''

        picksheet_id = self.request.GET.get('PSN_ID')
        search = self.request.GET.get('search', '')
        page = self.request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', 10)

        copy_request_data = deepcopy(dict(request.GET))
        copy_request_data.pop('page', None)
        copy_request_data.pop('search', None)
        copy_request_data.pop('ordering', None)
        copy_request_data.pop('PSN_ID', None)
        copy_request_data.pop('page_size', None)

        if picksheet_id is not None:
            try:
                queryset = PicksheetNote.objects.get(PSN_ID=picksheet_id)
                response_data = PickSheetGetSerializer(queryset).data
                response_data.pop('links', None)
            except PicksheetNote.DoesNotExist:
                response_data = {"message": "No data found"}
            return Response(response_data)
        if (len(copy_request_data) > 0 and picksheet_id is None) or (len(search) > 0 or request.GET.get('ordering') is not None):
            response = picksheet_filter(int(page), int(page_size), search, copy_request_data)
            response = {
                
                "results": response[0],
                "page": int(page),
                "page_size": int(page_size),
                "total": response[1],
                "column_type": self.column_type,
                "columns": self.columns
                }
            return Response(response, status=status.HTTP_200_OK)
        
        result = self.list(request, *args, **kwargs).data
        result.pop('links', None)
        result["page"] = int(page)
        result["page_size"] = int(page_size)
        result['columns'] = self.columns
        result['column_type'] = self.column_type
        return Response(result)
    def post(self, request, *args, **kwargs):
        
        try:
            request_data = request.data
            picksheet_name = request_data.get('PSN_NM')
            state = request_data.get('PSN_STS')
            start_date = request_data.get('ST_DT', None)
            end_date = request_data.get('EN_DT', None)
            psn_visibility = request_data.get('PSN_VIS')
            item_ids = request_data.get('ITM_SKU_ID', [])
            store_ids = request_data.get('STR_ID', [])
            note_details = request_data.get('NT_DETAILS', '')
            current_user_id = request.user
            created_by = current_user_id.id

            err_res = required_checks(store_ids, item_ids)
            if err_res:
                return Response(err_res, status=status.HTTP_400_BAD_REQUEST)
            stores = all_stores(store_ids)
            if stores:
                store_ids = stores
            if PicksheetNote.objects.filter(PSN_NM__iexact=picksheet_name).exists():
                response = {
                    "message": f"Picksheet Name with {picksheet_name} already exists"}
                stat = status.HTTP_400_BAD_REQUEST
            else:
                psn_vis = ", ".join(psn_visibility)
                note_data = {
                    'PSN_VIS': psn_vis,
                    'PSN_NM': picksheet_name,
                    "ST_DT": start_date,
                    "EN_DT": end_date,
                    'NT_DETAILS': note_details,
                    'PSN_STS': state,
                    "CRT_BY": created_by,
                }
                serializer = PickSheetSerializer(data=note_data)
                if serializer.is_valid():
                    picksheet_instance = serializer.save()

                    for store_id in store_ids:
                        PicksheetNoteStores.objects.create(
                            PSN_ID=picksheet_instance, STR_ID_id=store_id)

                    for item_id in item_ids:
                        PicksheetNoteItemSKU.objects.create(
                            PSN_ID=picksheet_instance, ITM_SKU_ID_id=item_id)
                    response = {
                        "message": "Picksheet Note Created Successfully"}
                    stat = status.HTTP_200_OK
                else:
                    response = {"message": "Invalid Data Provided"}
                    stat = status.HTTP_400_BAD_REQUEST
            return Response(response, status=stat)

        except Exception as e:
            return Response({"message": repr(e)}, status=status.HTTP_400_BAD_REQUEST)


class PicksheetUpdateAPIView(GenericAPIView, mixins.UpdateModelMixin):
    serializer_class = PickSheetSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        '''retrive method'''
        picksheet_id = self.kwargs.get('pk')
        query = PicksheetNote.objects.filter(
            PSN_ID=picksheet_id)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj

    def put(self, request, *args, **kwargs):
        '''Update of Picksheet Note and Associated tables'''
        try:
            instance = self.get_object()
            current_user = request.user
            name = request.data.get('PSN_NM')
            state = request.data.get('PSN_STS')
            start_dt = request.data.get('ST_DT', None)
            end_dt = request.data.get('EN_DT', None)
            psn_visibility = request.data.get('PSN_VIS')
            item_ids = request.data.get('ITM_SKU_ID', [])
            store_ids = request.data.get('STR_ID', [])
            nt_details = request.data.get('NT_DETAILS', '')
    
            vis = ", ".join(psn_visibility)
            update_data = {
                'PSN_VIS': vis,
                'PSN_NM': name,
                "ST_DT": start_dt,
                "EN_DT": end_dt,
                'NT_DETAILS': nt_details,
                'PSN_STS': state,
                "UPDT_BY":current_user.id
                
            }
            
            serializer = self.get_serializer(
                instance, data=update_data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            store_ids = request.data.get('STR_ID', [])
            item_ids = request.data.get('ITM_SKU_ID', [])
            related_store_name = 'picksheetnotestores_set'
            related_sku_name = 'picksheetnoteitemsku_set'
            related_store_manager = getattr(instance, related_store_name)
            related_sku_manager = getattr(instance, related_sku_name)
            related_store_manager.all().delete()
            related_sku_manager.all().delete()
            
            stores = all_stores(store_ids)
            if stores:
                store_ids = stores

            for store_id in store_ids:
                PicksheetNoteStores.objects.create(
                    PSN_ID=instance, STR_ID_id=store_id)

            for item_id in item_ids:
                PicksheetNoteItemSKU.objects.create(
                    PSN_ID=instance, ITM_SKU_ID_id=item_id)

            return Response({"message": "Picksheet Note Updated"})
        except Exception as e:
            return Response({"message": repr(e)}, status=status.HTTP_400_BAD_REQUEST)


class PicksheetStatusUpdate(views.APIView):
    '''Picksheet status update'''

    def validate_ids(self, id_list):
        '''Picksheet validate id'''
        for each_id in id_list:
            try:
                PicksheetNote.objects.get(PSN_ID=each_id)
            except (PicksheetNote.DoesNotExist, ValidationError):
                return False
        return True

    def put(self, request, *args, **kwargs):
        '''Picksheet multiple status update'''
        id_list = request.data['ids']
        status_val = request.data['status']
        current_user = request.user
        chk_stat = self.validate_ids(id_list=id_list)
        if chk_stat:
            instances = []
            for each_id in id_list:
                obj = PicksheetNote.objects.get(PSN_ID=each_id)
                obj.PSN_STS = status_val
                obj.UPDT_BY = current_user
                obj.save()
                instances.append(obj)
            serializer = PickSheetSerializer(instances, many=True)
            return Response(serializer.data, *args, **kwargs)
        else:
            response_data = {}
            response_data["message"] = invalid_id_key
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class PicksheetDeleteAPIView(GenericAPIView, mixins.DestroyModelMixin):

    def validate_ids(self, id):
        '''Picksheet validate id'''
        for each_id in id:
            try:
                PicksheetNote.objects.get(PSN_ID=each_id)
            except (PicksheetNote.DoesNotExist, ValidationError):
                return False
        return True

    def delete(self, request):
        '''Picksheet delete'''
        picksheet_id = request.data['ids']
        chk_stat = self.validate_ids(id=picksheet_id)
        if chk_stat:
            for each_id in picksheet_id:
                try:
                    str_instance = PicksheetNoteStores.objects.filter(PSN_ID=each_id).all()
                    sku_instance = PicksheetNoteItemSKU.objects.filter(PSN_ID=each_id).all()
                    str_instance.delete()
                    sku_instance.delete()
                    PicksheetNote.objects.filter(PSN_ID=each_id).delete()
                except Exception:
                    return Response({"message": "Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Picksheet Note Deleted"}, status=status.HTTP_200_OK)
        else:
            response_data = {}
            response_data["message"] = invalid_id_key
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class GetAssignedSKU(GenericAPIView, mixins.ListModelMixin):
    serializer_class = PickSheetItemSKUSerializer
    queryset = PicksheetNoteItemSKU.objects.all()
    pagination_class = PageNumberPagination
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page_number = request.GET.get('page', 1)
        page_size = self.request.GET.get('page_size', 10)
        search = self.request.GET.get('search', '')
        psn_id = request.GET.get('PSN_ID')
        itm_sku_ids = queryset.values_list('ITM_SKU_ID', flat=True)
        excluded_items = Item.objects.exclude(ID_ITM__in=itm_sku_ids)
        if search is not None:
            excluded_items = excluded_items.filter(Q(AS_ITM_SKU__icontains=search))
        if psn_id is not None:
            assign_sku = queryset.filter(PSN_ID=psn_id).values_list('ITM_SKU_ID', flat=True)
            included_items = Item.objects.filter(ID_ITM__in=assign_sku)
            combined_items = list(chain(included_items,excluded_items))
            paginator = Paginator(combined_items, page_size)
            serializer = self.get_serializer(paginator.page(page_number), many=True)
            return serializer.data
            
        paginator = Paginator(excluded_items, page_size)
        serializer = self.get_serializer(paginator.page(page_number), many=True)
        return serializer.data
    
    def get(self, request, *args, **kwargs):
            page = self.request.GET.get('page', 1)
            page_size = self.request.GET.get('page_size', 10)
            self.pagination_class.page = page
            self.pagination_class.page_size = page_size
            response = self.list(request, *args, **kwargs)
            response = {
                "results": response,
                "page": int(page),
                "page_size": int(page_size),
                }
            return Response(response)


    