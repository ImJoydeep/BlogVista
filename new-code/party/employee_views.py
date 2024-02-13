''' Employee Views File '''
from copy import deepcopy
import logging
import time
from django.db import transaction
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from django.db.models import Q
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin, CreateModelMixin
from drf_yasg.utils import swagger_auto_schema
from accesscontrol.models import OperatorBusinessUnitAssignment, WorkerOperatorAssignment, Operator
from party.employee_export import employee_export
from party.employee_filter import employee_filter
from worker.models import Employee
from .models import (PartyContactMethod,
                     PartyType, PartyRole, )
from .serializers import (
    PartySerializer, PartyRoleAssignmentSerializer, PersonSerializer, WorkerSerializer, EmployeeSerializer,
    EmployeeDataSerializer, EmployeeListSerializer,
    EmployeeRetrieveSerializer)
from .contact_details import contact_details_update, contact_details_delete

logger = logging.getLogger(__name__)
employee_export_messages = "Employee Export"


class EmployeeViews(CreateModelMixin, GenericAPIView):
    ''' Employee Create Views Class '''
    permission_classes = [IsAuthenticated]
    serializer_class = PartySerializer

    @swagger_auto_schema(tags=['Employee'], operation_description="Create Employee",
                         operation_summary="Create Employee", request_body=EmployeeDataSerializer)
    def post(self, request, *args, **kwargs):
        ''' Create Employee Party '''
        body_data = []
        try:
            data = request.data
            logger.info("Request Data : %s", data)
            contact_details = data.get("contact_details")
            with transaction.atomic():
                partytype = PartyType.objects.get(CD_PRTY_TYP="PR")
                logger.info("Party Type : %s, Party Type ID : %s",
                            partytype, partytype.ID_PRTY_TYP)
                current_user = request.user
                created_by = current_user.id
                logger.info("Created By : %s", created_by)
                partytbldata = {
                    "ID_PRTY_TYP": partytype.ID_PRTY_TYP,
                    "BY_CRT_PRTY": created_by,
                }
                serializer = PartySerializer(data=partytbldata)
                if serializer.is_valid():
                    save_data = serializer.save()
                    body_data = serializer.data

                else:
                    transaction.set_rollback(True)
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )
                if save_data.ID_PRTY:
                    partyrole = PartyRole.objects.get(TY_RO_PRTY="WRK")
                    party_role_id = partyrole.ID_RO_PRTY
                    logger.info("Party Role : %s", party_role_id)
                    partyrole_asgmt_data = {
                        "ID_PRTY": save_data.ID_PRTY,
                        "ID_RO_PRTY": party_role_id
                    }
                    partyrole_asgmt = PartyRoleAssignmentSerializer(
                        data=partyrole_asgmt_data
                    )
                    if partyrole_asgmt.is_valid():
                        partyroleasign_save = partyrole_asgmt.save()
                        body_data.update(partyrole_asgmt.data)
                    else:
                        transaction.set_rollback(True)
                        return Response(
                            partyrole_asgmt.errors,
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    person_data = {
                        "ID_PRTY": save_data.ID_PRTY,
                        "FN_PRS": data["FN_PRS"],
                        "MD_PRS": data["MD_PRS"],
                        "LN_PRS": data["LN_PRS"],
                        "PRS_CRT_BY": created_by,

                    }
                    personserializer = PersonSerializer(data=person_data)
                    if personserializer.is_valid():
                        personserializer.save()
                        person_save_data = personserializer.data
                        body_data.update(person_save_data)
                    else:
                        transaction.set_rollback(True)
                        return Response(
                            personserializer.errors,
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if partyroleasign_save.ID_PRTY_RO_ASGMT:
                        workerdata = {
                            "ID_PRTY_RO_ASGMT": partyroleasign_save.ID_PRTY_RO_ASGMT,
                            "TY_WRKR": "EM",
                            "URL_PGPH_WRKR": data['URL_PGPH_WRKR'],
                            "WRKR_CRT_BY": created_by
                        }
                        workers = WorkerSerializer(data=workerdata)
                        if workers.is_valid():
                            worker_save = workers.save()
                            if worker_save.ID_WRKR:
                                employee_data = {
                                    "ID_WRKR": worker_save.ID_WRKR,
                                    "SC_EM": data['SC_EM'],
                                    "ID_USR_CRT": created_by
                                }
                                employee = EmployeeSerializer(
                                    data=employee_data)
                                if employee.is_valid():
                                    employee.save()
                                    employee_save_data = employee.data
                                    body_data.update(employee_save_data)
                                else:
                                    transaction.set_rollback(True)
                                    return Response(
                                        employee.errors, status=status.HTTP_400_BAD_REQUEST
                                    )
                            body_data.update(workers.data)
                        else:
                            transaction.set_rollback(True)
                            return Response(
                                workers.errors, status=status.HTTP_400_BAD_REQUEST
                            )
                        # ---------------------------------------
                        contact_id = PartyContactMethod.objects.filter(
                            ID_PRTY_RO_ASGMT=partyroleasign_save.ID_PRTY_RO_ASGMT)
                        if contact_id.count() > 0:
                            contact_id_list = contact_id.values_list(
                                'ID_PRTY_CNCT_MTH', flat=True)[::1]
                            logger.info("Contact ID List : %s",
                                        contact_id_list)
                            contact_details_delete(contact_id_list, None)

                        # ---------------------------------------
                        if contact_details:
                            contact = contact_details_update(
                                contact_details, partyroleasign_save.ID_PRTY_RO_ASGMT)
                            if contact.get('errors'):
                                return Response(contact.get('errors'),
                                                status=status.HTTP_400_BAD_REQUEST)

                return Response(body_data, status=status.HTTP_200_OK)
        except Exception as exp:
            logger.exception(exp)
            return Response({"error": exp.__class__.__name__}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeListViews(ListModelMixin, GenericAPIView):
    '''Employee List View Class '''
    permission_classes = [IsAuthenticated]
    queryset = Employee.objects.all()
    serializer_class = EmployeeListSerializer
    filter_backends = [DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ID_EM']
    ordering_fields = '__all__'
    ordering = ['-ID_EM']

    def __init__(self):
        self.columns = {
            "SC_EM": "Status", "employee_name": "Employee Name", "operator": "Operator", "position_name": "Position",
            "department_name": "Department",
            "PH_CMPL": "Mobile Number", "EM_ADS": "Email Address", "permission_set": "Permission Set",
            "CRT_DT": "Created Date & Time", "ID_USR_CRT": "Created By", "UPDT_DT": "Updated Date & Time",
            "ID_USR_UPDT": "Updated By"}
        self.column_type = {
            "SC_EM": "status", "employee_name": "str", "operator": "str", "position_name": "str",
            "department_name": "str", "PH_CMPL": "str", "EM_ADS": "str", "permission_set": "str",
            "CRT_DT": "Datetime", "ID_USR_CRT": "str", "UPDT_DT": "Datetime", "ID_USR_UPDT": "str"}

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['columns'] = self.columns
        response.data['column_type'] = self.column_type

        return response

    def employee_export_data(self, response, device_id, current_user, file_name, business_unit_id, file_type, device_flag):
        '''Export employee data'''
        if len(response[0]) > 0:
            notification_data = {"device_id": device_id, "message_title": employee_export_messages, "message_body": "Employee Export Successfully Done",
                                 "notification_type": employee_export_messages, "event_id": None, "user_id": current_user.id, "file_name": file_name, "export_flag": True}
            location = 'export_files/'+str(file_name)
            if device_id is None or device_id == '':
                device_flag = False
            if len(response[0]) > 1000:
                employee_export.delay(response, self.columns, business_unit_id,
                                      file_name, location, notification_data, device_flag, file_type)
                message = {
                    "message": "Export processing in background. You will get a file URL on Email as well as Notification."}
                stat = status.HTTP_200_OK
            else:
                employee_export(response, self.columns, business_unit_id,
                                file_name, location, notification_data, device_flag, file_type)
                message = {"file_name": file_name}
                stat = status.HTTP_200_OK
        else:
            message = {}
            message['error'] = {"message": 'No Data Found'}
            stat = status.HTTP_404_NOT_FOUND
        return message, stat

    @swagger_auto_schema(tags=['Employee'], operation_description="Get all employee", operation_summary="Get Employee")
    def get(self, request, *args, **kwargs):
        ''' Employee List '''
        try:
            user_id = request.GET.get('user_id', None)
            business_unit_id = request.GET.get('ID_BSN_UN', '0')
            employee_count = Employee.objects.count()
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', employee_count)
            logger.info("User ID : %s", user_id)
            employee_id = None
            limit = int(page_size)
            page = int(page)
            offset = (page - 1) * limit
            if user_id is not None:
                user_obj = User.objects.get(id=user_id)
                user_name = user_obj.username
                opr_obj = Operator.objects.get(NM_USR=user_name)
                operator_id = opr_obj.ID_OPR
                worker_obj = WorkerOperatorAssignment.objects.filter(
                    ID_OPR=operator_id).first()
                employee_obj = Employee.objects.get(
                    ID_WRKR=worker_obj.ID_WRKR.ID_WRKR)
                employee_id = employee_obj.ID_EM
            else:
                employee_id = request.GET.get('ID_EM')
            search = request.GET.get('search', '')
            device_id = request.GET.get('device_id', None)
            export_flag = request.GET.get('export_flag', 0)
            file_type = request.GET.get('type', 'xlsx')
            copy_request_data = deepcopy(dict(request.GET))
            copy_request_data.pop('ordering', None)
            copy_request_data.pop('page', None)
            copy_request_data.pop('search', None)
            copy_request_data.pop('user_id', None)
            copy_request_data.pop('ID_BSN_UN', None)
            copy_request_data.pop('ID_EM', None)
            copy_request_data.pop('page_size', None)
            copy_request_data.pop('export_flag', None)
            copy_request_data.pop('device_id', None)
            copy_request_data.pop('type', None)
            business_unit_query = Q()
            if export_flag == '1':
                logger.info(employee_export_messages)
                device_flag = True
                current_user = request.user
                file_name = 'Employee_Export_Data' + \
                    str(time.time())+'.'+str(file_type).lower()
                response = employee_filter(
                    business_unit_query, int(page), int(
                        page_size), search, copy_request_data,
                    request.GET.get('ordering'))
                message, stat = self.employee_export_data(response, device_id, current_user,
                                                          file_name, business_unit_id, file_type, device_flag)

                return Response(message, status=stat)

            if (len(copy_request_data) > 0 and user_id is None) or (
                    len(search) > 0 or request.GET.get('ordering') is not None):
                if business_unit_id is None or business_unit_id == "0":
                    business_unit_query = None

                response = employee_filter(
                    business_unit_query, int(page), int(
                        page_size), search, copy_request_data,
                    request.GET.get('ordering'))
                response = {
                    "total": response[1],
                    "page": int(page),
                    "page_size": int(page_size),
                    "results": response[0],
                    "columns": self.columns,
                    "column_type": self.column_type
                }
                return Response(response, status=status.HTTP_200_OK)

            elif employee_id is None:
                # logger.info("Employee ID None")
                employee_data = Employee.objects.filter(
                    Q(business_unit_query)).order_by('-ID_EM')
                count = employee_data.count()
                response_data = employee_data[offset:offset + limit]
            else:
                # logger.info("Employee ID  Not None")
                queryset = Employee.objects.get(
                    Q(business_unit_query) & Q(ID_EM=employee_id))
                employee_serializer = EmployeeRetrieveSerializer(queryset)
                response_data = employee_serializer.data
                response_data["previous_id"] = Employee.objects.filter(Q(business_unit_query) & Q(
                    ID_EM__gt=employee_id)).order_by("ID_EM").values_list("ID_EM", flat=True).first()
                response_data["next_id"] = Employee.objects.filter(Q(business_unit_query) & Q(
                    ID_EM__lt=employee_id)).order_by("-ID_EM").values_list("ID_EM", flat=True).first()
                return Response(response_data, status=status.HTTP_200_OK)

            response_serializer = EmployeeListSerializer(
                response_data, many=True).data
            response = {
                "total": count,
                "page": int(page),
                "page_size": int(page_size),
                "results": response_serializer,
                "columns": self.columns,
                "column_type": self.column_type
            }
            return Response(response, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response("User Not Exist", status=status.HTTP_400_BAD_REQUEST)
        except Exception as exp:
            logger.exception("Employee Get Exception : %s", exp)
            return Response({}, status=status.HTTP_200_OK)
