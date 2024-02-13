''' Employee Multiple Status Update and Delete Views '''
import logging
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from requests import delete
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from position.models import WorkerPositionAssignment
from worker.models import Employee
from workerschedule.models import WorkerAvailability
from accesscontrol.models import WorkerOperatorAssignment, Operator
from .models import (PartyContactMethod)

logger = logging.getLogger(__name__)
invalid__employee_position_messages = "Invalid  Employee Position Assignment ID's"


def employee_id_validate(id_list):
    '''Employee Id validation'''
    for employee_id in id_list:
        try:
            Employee.objects.get(ID_EM=employee_id)
        except (Employee.DoesNotExist, ValidationError):
            return False
    return True


def contact_id_validate(id_list):
    '''Contact Id validation'''
    for contact_id in id_list:
        try:
            PartyContactMethod.objects.get(
                ID_PRTY_CNCT_MTH=contact_id)
        except (PartyContactMethod.DoesNotExist, ValidationError):
            return False
    return True


def worker_position_id_validate(id_list):
    '''Validate position Id'''
    for wrkr_position_id in id_list:
        try:
            WorkerPositionAssignment.objects.get(
                ID_ASGMT_WRKR_PSN=wrkr_position_id)
        except (WorkerPositionAssignment.DoesNotExist, ValidationError):
            return False
    return True


def work_availability_id_validate(id_list):
    '''Validate worker availability id'''
    for wrkr_avlb_id in id_list:
        try:
            WorkerAvailability.objects.get(
                ID_WRKR_AVLB=wrkr_avlb_id)
        except (WorkerAvailability.DoesNotExist, ValidationError):
            return False
    return True


def validate_ids(id_list, id_type):
    ''' validate  ids'''
    if id_type == 'employee':
        return employee_id_validate(id_list)

    elif id_type == 'contacts':
        return contact_id_validate(id_list)

    elif id_type == 'positions':
        return worker_position_id_validate(id_list)

    elif id_type == 'work_availability':
        return work_availability_id_validate(id_list)

    elif id_type == 'permissions':
        for wrkr_operator_id in id_list:
            try:
                WorkerOperatorAssignment.objects.get(
                    ID_ASGMT_WRKR_OPR=wrkr_operator_id)
            except (WorkerOperatorAssignment.DoesNotExist, ValidationError):
                return False
        return True


class EmployeeMultipleStatusUpdate(APIView):
    '''Employee  multiple status update and delete'''
    permission_classes = (IsAuthenticated,)

    multiple_update_response_schema = {
        "200": openapi.Response(
            description="Status Successfully Updated",
        ),
        "400": openapi.Response(
            description="Bad Request"
        )
    }

    def update_employee_status(self, employee_id_list, employee_status, current_user):
        '''Update employee status'''
        user_name = []
        emp_obj = Employee.objects.filter(
            ID_EM__in=employee_id_list)
        emp_obj.update(SC_EM=employee_status,
                       ID_USR_UPDT=current_user)
        worker_id = list(
            emp_obj.values_list('ID_WRKR', flat=True))
        logger.info("Worker ID List : %s", worker_id)
        user_name = list(WorkerOperatorAssignment.objects.filter(
            ID_WRKR__in=worker_id).values_list('ID_OPR__NM_USR', flat=True))
        logger.info(
            "Worker Operator User Name List : %s", user_name)
        logger.info("User Name : %s", user_name)
        if employee_status == 'A':
            User.objects.filter(
                username__in=user_name).update(is_active=True)
        else:
            User.objects.filter(
                username__in=user_name).update(is_active=False)
        response = {}
        response["message"] = "Status Successfully Updated"
        response_status = status.HTTP_200_OK
        return response, response_status

    def update_employee_contact_status(self, contacts):
        '''Update employee contact status'''
        contact_id_list = contacts['ids']
        contact_status = contacts['status']
        contact_chk = validate_ids(
            id_list=contact_id_list, id_type='contacts')
        if contact_chk:
            PartyContactMethod.objects.filter(
                ID_PRTY_CNCT_MTH__in=contact_id_list).update(CD_STS=contact_status)
            response = {}
            response["message"] = "Employee Contact Status Successfully Updated"
            response_status = status.HTTP_200_OK
        else:
            response = {}
            response["message"] = "Invalid  Employee Contact ID's"
            response_status = status.HTTP_400_BAD_REQUEST
        return response, response_status

    def update_employee_position_status(self, positions):
        '''Update employee position status'''
        positions_id_list = positions['ids']
        position_status = positions['status']
        position_chk = validate_ids(
            id_list=positions_id_list, id_type='positions')
        if position_chk:
            WorkerPositionAssignment.objects.filter(
                ID_ASGMT_WRKR_PSN__in=positions_id_list).update(SC_EM_ASGMT=position_status)
            response = {}
            response["message"] = "Employee Position Status Successfully Updated"
            response_status = status.HTTP_200_OK
        else:
            response = {}
            response["message"] = invalid__employee_position_messages
            response_status = status.HTTP_400_BAD_REQUEST
        return response, response_status

    def update_employee_work_availability_status(self, work_availability):
        '''Update employee work availability status'''
        work_avlb_id_list = work_availability['ids']
        work_avlb_status = work_availability['status']
        work_avlb_chk = validate_ids(
            id_list=work_avlb_id_list, id_type='work_availability')
        if work_avlb_chk:
            WorkerAvailability.objects.filter(
                ID_WRKR_AVLB__in=work_avlb_id_list).update(ST_WRKR_AVLB=work_avlb_status)
            response = {}
            response["message"] = "Work Availability Status Successfully Updated"
            response_status = status.HTTP_200_OK
        else:
            response = {}
            response["message"] = "Invalid Work Availability ID's"
            response_status = status.HTTP_400_BAD_REQUEST
        return response, response_status

    def update_employee_permissions_status(self, permissions, employee_status):
        '''Update employee permissions status'''
        permissions_id_list = permissions['ids']
        permissions_status = permissions['status']
        permissions_chk = validate_ids(
            id_list=permissions_id_list, id_type='permissions')
        if permissions_chk:
            wrkr_opr_obj = WorkerOperatorAssignment.objects.filter(
                ID_ASGMT_WRKR_OPR__in=permissions_id_list)
            wrkr_opr_obj.update(
                SC_ASGMT=permissions_status)
            user_name = list(wrkr_opr_obj.values_list(
                'ID_OPR__NM_USR', flat=True))
            logger.info(
                "Worker Operator User Name List : %s", user_name)
            logger.info("User Name : %s", user_name)
            if employee_status == 'A':
                User.objects.filter(
                    username__in=user_name).update(is_active=True)
            else:
                User.objects.filter(
                    username__in=user_name).update(is_active=False)

            response = {}
            response["message"] = "Permissions Status Successfully Updated"
            response_status = status.HTTP_200_OK
        else:
            response = {}
            response["message"] = invalid__employee_position_messages
            response_status = status.HTTP_400_BAD_REQUEST
        return response, response_status

    @swagger_auto_schema(tags=['Employee'], operation_description="Employee multiple status update",
                         operation_summary="Employee multiple status update", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Ids',
                                  items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Id')),
            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Employee status (A/I)'),
            'contacts': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of contact Ids and status',
                                       properties={
                                           'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Contact Ids',
                                                                 items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Contacts Ids')),
                                           'status': openapi.Schema(type=openapi.TYPE_STRING, description='Contact status (A/I)'),
                                       }),
            'positions': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of Employee Position Ids and status',
                                        properties={
                                            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Employee Position Ids',
                                                                  items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Position Ids')),
                                            'status': openapi.Schema(type=openapi.TYPE_STRING, description='Employee Position status (A/I)'),
                                        }),
            'permissions': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of Employee Permissions Ids and status',
                                          properties={
                                              'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Employee Permissions Ids',
                                                                    items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Permissions Ids')),
                                              'status': openapi.Schema(type=openapi.TYPE_STRING, description='Employee Position status (A/I)'),
                                          }),
            'work_availability': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of Employee Work Availability Ids and status',
                                                properties={
                                                    'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Employee Work Availability Ids',
                                                                          items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Work Availability Ids')),
                                                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Employee Work Availability status (A/I)'),
                                                }),
        }, required=['ids']
    ), responses=multiple_update_response_schema)
    def put(self, request):
        '''Employee multiple status update'''
        logger.info("Employee Update Status Request Data : %s", request.data)
        employee_id_list = request.data['ids']
        employee_status = request.data['status']
        contacts = request.data.get('contacts', None)
        positions = request.data.get('positions', None)
        work_availability = request.data.get('work_availability', None)
        permissions = request.data.get('permissions', None)
        response = {}
        response_status = None
        try:
            with transaction.atomic():
                chk_stat = validate_ids(
                    id_list=employee_id_list, id_type='employee')
                current_user = request.user
                if chk_stat:
                    if employee_status is not None:
                        response, response_status = self.update_employee_status(
                            employee_id_list, employee_status, current_user)
                    else:
                        if contacts:
                            response, response_status = self.update_employee_contact_status(
                                contacts)

                        elif positions:
                            response, response_status = self.update_employee_position_status(
                                positions)

                        elif work_availability:
                            response, response_status = self.update_employee_work_availability_status(
                                work_availability)

                        elif permissions:
                            response, response_status = self.update_employee_permissions_status(
                                permissions, employee_status)

                else:
                    response = {}
                    response["message"] = "Invalid Employee ID's"
                    response_status = status.HTTP_400_BAD_REQUEST
        except Exception as exp:
            logger.exception(exp)
            response = {}
            response["message"] = "Invalid Data"
            response_status = status.HTTP_400_BAD_REQUEST
        return Response(response, status=response_status)

    multiple_delete_response_schema = {
        "204": openapi.Response(
            description="Successfully Deleted",
        ),
        "400": openapi.Response(
            description="Bad Request"
        )
    }

    @ swagger_auto_schema(tags=['Employee'], operation_description="Delete employee", operation_summary="Delete Employee", request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Ids',
                                  items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Id')),
            'contacts': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of contact Ids and status',
                                       properties={
                                           'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Contact Ids',
                                                                 items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Contacts Ids')),
                                       }),
            'positions': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of Employee Position Ids and status',
                                        properties={
                                            'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Employee Position Ids',
                                                                  items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Position Ids')),
                                        }),
            'permissions': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of Employee Permissions Ids and status',
                                          properties={
                                              'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Employee Permissions Ids',
                                                                    items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Permissions Ids')),
                                          }),
            'work_availability': openapi.Schema(type=openapi.TYPE_OBJECT, description='List of Employee Work Availability Ids and status',
                                                properties={
                                                    'ids': openapi.Schema(type=openapi.TYPE_ARRAY, description='List of Employee Work Availability Ids',
                                                                          items=openapi.Items(type=openapi.TYPE_INTEGER, description='Employee Work Availability Ids')),
                                                }),
        }, required=['ids']
    ), responses=multiple_delete_response_schema)
    def delete(self, request):
        '''Employee multiple delete '''
        employee_id_list = request.data['ids']
        contacts = request.data.get('contacts', None)
        positions = request.data.get('positions', None)
        work_availability = request.data.get('work_availability', None)
        permissions = request.data.get('permissions', None)
        response = {}
        response_status = None
        try:
            with transaction.atomic():
                chk_stat = validate_ids(
                    id_list=employee_id_list, id_type='employee')
                if chk_stat:
                    if contacts:
                        contact_id_list = contacts['ids']
                        contact_chk = validate_ids(
                            id_list=contact_id_list, id_type='contacts')
                        if contact_chk:
                            for contact_id in contact_id_list:
                                obj = PartyContactMethod.objects.get(
                                    ID_PRTY_CNCT_MTH=contact_id)
                                obj.delete()
                            response = {}
                            response["message"] = "Employee Contact Successfully Deleted"
                            response_status = status.HTTP_204_NO_CONTENT
                        else:
                            response = {}
                            response["message"] = "Invalid  Employee Contact ID's"
                            response_status = status.HTTP_400_BAD_REQUEST
                    elif positions:
                        positions_id_list = positions['ids']
                        position_chk = validate_ids(
                            id_list=positions_id_list, id_type='positions')
                        if position_chk:
                            for wrkr_position_id in positions_id_list:
                                obj = WorkerPositionAssignment.objects.get(
                                    ID_ASGMT_WRKR_PSN=wrkr_position_id)
                                obj.delete()
                            response = {}
                            response["message"] = "Employee Position Successfully Deleted"
                            response_status = status.HTTP_204_NO_CONTENT
                        else:
                            response = {}
                            response["message"] = invalid__employee_position_messages
                            response_status = status.HTTP_400_BAD_REQUEST
                    elif work_availability:
                        work_avlb_id_list = work_availability['ids']
                        work_avlb_chk = validate_ids(
                            id_list=work_avlb_id_list, id_type='work_availability')
                        if work_avlb_chk:
                            for work_avlb_id in work_avlb_id_list:
                                obj = WorkerAvailability.objects.get(
                                    ID_WRKR_AVLB=work_avlb_id)
                                obj.delete()
                            response = {}
                            response["message"] = "Work Availability Successfully Deleted"
                            response_status = status.HTTP_204_NO_CONTENT
                        else:
                            response = {}
                            response["message"] = "Invalid Work Availability ID's"
                            response_status = status.HTTP_400_BAD_REQUEST
                    elif permissions:
                        permissions_id_list = permissions['ids']
                        permissions_chk = validate_ids(
                            id_list=permissions_id_list, id_type='permissions')
                        if permissions_chk:
                            for wrkr_permission_id in permissions_id_list:
                                obj = WorkerOperatorAssignment.objects.get(
                                    ID_ASGMT_WRKR_OPR=wrkr_permission_id)
                                operator_id = obj.ID_OPR
                                operator_obj = Operator.objects.get(
                                    ID_OPR=operator_id.ID_OPR)
                                logger.info("Operator Obj : %s",
                                            operator_obj)
                                opr_usr_name = operator_obj.NM_USR
                                User.objects.filter(
                                    username=opr_usr_name).delete()
                                obj.delete()
                            response = {}
                            response["message"] = "Employee Position Successfully Deleted"
                            response_status = status.HTTP_204_NO_CONTENT
                        else:
                            response = {}
                            response["message"] = invalid__employee_position_messages
                            response_status = status.HTTP_400_BAD_REQUEST
                    else:
                        for employee_id in employee_id_list:
                            obj = Employee.objects.get(
                                ID_EM=employee_id)
                            logger.info("Employee Obj : %s", obj)
                            worker_id = obj.ID_WRKR
                            logger.info("Worker ID : %s", worker_id)
                            WorkerAvailability.objects.filter(
                                ID_WRKR=worker_id).delete()
                            WorkerPositionAssignment.objects.filter(
                                ID_WRKR=worker_id).delete()
                            wrkr_opr_list = WorkerOperatorAssignment.objects.filter(
                                ID_WRKR=worker_id).values_list('ID_OPR', flat=True)
                            logger.info(
                                "Worker Operator Obj : %s", wrkr_opr_list)
                            if len(wrkr_opr_list) > 0:
                                for index, value in enumerate(wrkr_opr_list):
                                    operator_id = value
                                    logger.info(
                                        "Operator Id : %s", operator_id)
                                    operator_obj = Operator.objects.get(
                                        ID_OPR=operator_id)
                                    logger.info("Operator Obj : %s",
                                                operator_obj)
                                    opr_usr_name = operator_obj.NM_USR
                                    logger.info(
                                        "Operator Username : %s", opr_usr_name)
                                    User.objects.filter(
                                        username=opr_usr_name).delete()
                            WorkerOperatorAssignment.objects.filter(
                                ID_WRKR=worker_id).delete()
                            obj.delete()
                        response = {}
                        response["message"] = "Employee Successfully Deleted"
                        response_status = status.HTTP_204_NO_CONTENT

                else:
                    response = {}
                    response["message"] = "Invalid Employee ID's"
                    response_status = status.HTTP_400_BAD_REQUEST
        except Exception as exp:
            logger.exception(exp)
            response = {}
            response["message"] = "Invalid Data"
            response_status = status.HTTP_400_BAD_REQUEST
        return Response(response, status=response_status)
