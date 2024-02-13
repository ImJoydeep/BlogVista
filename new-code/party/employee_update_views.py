''' Employee Update Views '''
import logging
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from drf_yasg.utils import swagger_auto_schema
from position.models import WorkerPositionAssignment
from worker.models import Employee
from workerschedule.models import WorkerAvailability
from accesscontrol.models import Operator, WorkerOperatorAssignment
from .models import (Person, Telephone, EmailAddress,
                     PostalCodeReference, Address, PartyContactMethod)
from .serializers import (PersonSerializer, PostalCodeSerializer, WorkerSerializer,
                          EmailAddressSerializer, TelephoneSerializer, AddressSerializer,
                          PartyContactMethodSerializer,
                          WorkerPositionAsgmtSerializer, WorkerAvailabilitySerializer,
                          EmployeeUpdateSerializer, WorkerOperatorAsgmtSerializer)
from .contact_details import contact_details_update, contact_details_delete

logger = logging.getLogger(__name__)


class EmployeeUpdateViews(GenericAPIView):
    ''' Employee Update Views Class '''
    permission_classes = (IsAuthenticated,)
    serializer_class = EmployeeUpdateSerializer
    lookup_url_kwarg = "employee_id"

    def get_queryset(self):
        employee_id = self.kwargs.get(self.lookup_url_kwarg)
        query = Employee.objects.filter(
            ID_EM=employee_id)
        return query

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset)
        return obj

    @swagger_auto_schema(tags=['Employee'], operation_description="Employee Update",
                         operation_summary="Employee Update")
    def put(self, request, *args, **kwargs):
        ''' Update Employee '''
        try:
            data = request.data
            logger.info("Employee Update Request Data : %s", data)
            position_details = data.get('position_details', None)
            work_availability = data.get('work_availability', None)
            operator_details = data.get('operator_details', None)
            contact_details = data.get('contact_details', None)
            employee_id = self.kwargs.get(self.lookup_url_kwarg)
            first_name = data.get('FN_PRS', None)
            middle_name = data.get('MD_PRS', None)
            last_name = data.get('LN_PRS', None)
            worker_image = data.get('URL_PGPH_WRKR', None)
            logger.info("Employee ID : %s", employee_id)

            current_user = request.user
            logger.info("Current User : %s", current_user)
            with transaction.atomic():
                employee_obj = Employee.objects.get(ID_EM=employee_id)
                employee_status = data['SC_EM'] if data.get('SC_EM') else None
                if employee_status is not None:
                    employee_obj.SC_EM = employee_status
                    employee_obj.ID_USR_UPDT = current_user
                    employee_obj.save()
                worker_obj = employee_obj.ID_WRKR
                logger.info("Worker Object : %s", worker_obj)
                party_obj = worker_obj.ID_PRTY_RO_ASGMT.ID_PRTY
                # logger.info("Party Obj : %s", party_obj)
                person_obj = Person.objects.get(ID_PRTY=party_obj)
                # logger.info("Person Id : %s", person_obj)

                if first_name is not None and last_name is not None:
                    person_data = {"FN_PRS": first_name,
                                   "LN_PRS": last_name, "MD_PRS": middle_name,
                                   "ID_PRTY": party_obj.ID_PRTY}
                    person_serializer = PersonSerializer(
                        instance=person_obj, data=person_data)
                    if person_serializer.is_valid():
                        person_serializer.save()
                        opr_wrkr_obj = WorkerOperatorAssignment.objects.filter(
                            ID_WRKR=worker_obj)
                        # logger.info(
                        # "Operator Worker Object : %s", opr_wrkr_obj)
                        if opr_wrkr_obj.exists():
                            opr_usr_name = opr_wrkr_obj.last().ID_OPR.NM_USR
                            logger.info("Operato Username : %s", opr_usr_name)
                            usr_obj = User.objects.filter(
                                username=opr_usr_name).update(first_name=first_name, last_name=last_name)
                    else:
                        return Response(
                            person_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                if worker_image is not None:
                    workerdata = {
                        "ID_PRTY_RO_ASGMT": worker_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT,
                        "URL_PGPH_WRKR": worker_image,
                        "WRKR_MDF_BY": current_user.id
                    }
                    workers = WorkerSerializer(
                        instance=worker_obj, data=workerdata)
                    if workers.is_valid():
                        worker_save = workers.save()
                        logger.info(
                            "Worker saved : %s", worker_save)
                    else:
                        return Response(
                            workers.errors,
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                # ! Create or Update Employee Contact Detail
                # ---------------------------------------
                contact_id = PartyContactMethod.objects.filter(
                    ID_PRTY_RO_ASGMT=worker_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT)
                if not (position_details or work_availability or operator_details):
                    contact_id_list = contact_id.values_list(
                        'ID_PRTY_CNCT_MTH', flat=True)[::1]
                    logger.info("Contact ID List : %s", contact_id_list)
                    contact_details_delete(contact_id_list, None)

                if contact_details:
                    contact_details_update(
                        contact_details, worker_obj.ID_PRTY_RO_ASGMT.ID_PRTY_RO_ASGMT)
                # ---------------------------------------
                # ! Create or Update Employee Position
                if position_details is not None and len(position_details) > 0:
                    wrkr_position_list = [d.get('ID_ASGMT_WRKR_PSN', None)
                                          for d in position_details if d.get('ID_ASGMT_WRKR_PSN') is not None]
                    logger.info("New Worker Position List : %s",
                                wrkr_position_list)
                    WorkerPositionAssignment.objects.filter(ID_WRKR=worker_obj.ID_WRKR).exclude(
                        ID_ASGMT_WRKR_PSN__in=wrkr_position_list).delete()
                    for position in position_details:
                        psn_wrkr_id = position['ID_ASGMT_WRKR_PSN']
                        position["ID_WRKR"] = worker_obj.ID_WRKR
                        if psn_wrkr_id is not None:
                            psn_wrkr_obj = WorkerPositionAssignment.objects.get(
                                ID_ASGMT_WRKR_PSN=psn_wrkr_id)
                            logger.info(
                                "Position Worker Instance : %s", psn_wrkr_obj)
                            position_serializer = WorkerPositionAsgmtSerializer(instance=psn_wrkr_obj,
                                                                                data=position)
                            if position_serializer.is_valid():
                                position_obj = position_serializer.save()
                                logger.info(
                                    "Position Updated : %s", position_obj)
                            else:
                                return Response(
                                    position_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                                )
                        else:
                            position.pop('ID_ASGMT_WRKR_PSN')
                            logger.info("Position Details : %s",
                                        position)
                            position_serializer = WorkerPositionAsgmtSerializer(
                                data=position)
                            if position_serializer.is_valid():
                                position_obj = position_serializer.save()
                                logger.info(
                                    "Position Updated : %s", position_obj)
                            else:
                                return Response(
                                    position_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                                )
                elif position_details is not None and len(position_details) == 0:
                    logger.info("Position Details Not Found")
                    WorkerPositionAssignment.objects.filter(
                        ID_WRKR=worker_obj.ID_WRKR).delete()

                # ! Create or Update Worker Availability
                if work_availability is not None and len(work_availability) > 0:
                    wrkr_avlb_list = [d.get('ID_WRKR_AVLB', None)
                                      for d in work_availability if d.get('ID_WRKR_AVLB') is not None]
                    logger.info("New Worker Availability List : %s",
                                wrkr_avlb_list)
                    WorkerAvailability.objects.filter(ID_WRKR=worker_obj.ID_WRKR).exclude(
                        ID_WRKR_AVLB__in=wrkr_avlb_list).delete()
                    for work_available in work_availability:
                        wrkr_avlb_id = work_available['ID_WRKR_AVLB']
                        work_available['ID_WRKR'] = worker_obj.ID_WRKR
                        if wrkr_avlb_id is not None:
                            logger.info("Worker Avlb Not None")
                            wrkr_avlb_obj = WorkerAvailability.objects.get(
                                ID_WRKR_AVLB=wrkr_avlb_id)
                            logger.info(
                                " Worker Available Instance : %s", wrkr_avlb_obj)
                            workavl_serializer = WorkerAvailabilitySerializer(instance=wrkr_avlb_obj,
                                                                              data=work_available)
                            if workavl_serializer.is_valid():
                                workavl_serializer.save()

                            else:
                                return Response(
                                    workavl_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                                )
                        else:
                            work_available.pop('ID_WRKR_AVLB')
                            workavl_serializer = WorkerAvailabilitySerializer(
                                data=work_available)
                            if workavl_serializer.is_valid():
                                workavl_serializer.save()

                            else:
                                return Response(
                                    workavl_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                                )
                elif work_availability is not None and len(work_availability) == 0:
                    logger.info("Worker Availability Not Found")
                    WorkerAvailability.objects.filter(
                        ID_WRKR=worker_obj.ID_WRKR).delete()

                # ! Create or Update Employee Operator Tag
                if operator_details is not None and len(operator_details) > 0:
                    wrkr_opr_list = [d.get('ID_ASGMT_WRKR_OPR', None)
                                     for d in operator_details if d.get('ID_ASGMT_WRKR_OPR') is not None]
                    logger.info("New Worker Operator List : %s", wrkr_opr_list)
                    WorkerOperatorAssignment.objects.filter(ID_WRKR=worker_obj.ID_WRKR).exclude(
                        ID_ASGMT_WRKR_OPR__in=wrkr_opr_list).delete()
                    for operator in operator_details:
                        logger.info("Operator Details")
                        operator_id = operator['ID_OPR']
                        asgmt_status = operator['SC_ASGMT']
                        operator_obj = Operator.objects.get(
                            ID_OPR=operator_id)
                        logger.info("Operator Obj : %s",
                                    operator_obj)
                        opr_usr_name = operator_obj.NM_USR
                        opr_pswrd = operator_obj.PW_ACS_OPR
                        opr_email = operator_obj.EMAIL_USR
                        is_superuser = operator_obj.is_superuser
                        password = make_password(opr_pswrd)

                        person_obj = Person.objects.get(ID_PRTY=party_obj)
                        logger.info("Person Id : %s", person_obj)

                        user_exist = User.objects.filter(
                            username=opr_usr_name).exists()
                        logger.info(
                            "Operator Username : %s and Password : %s", opr_usr_name, password)
                        usr_data = {"username": opr_usr_name,
                                    "password": password, "first_name": person_obj.FN_PRS,
                                    "last_name": person_obj.LN_PRS, "email": opr_email, "is_superuser": is_superuser}
                        if user_exist:
                            if asgmt_status == 'A':
                                usr_data['is_active'] = True
                            else:
                                usr_data['is_active'] = False
                            usr_obj = User.objects.filter(
                                username=opr_usr_name).update(**usr_data)
                            logger.info("User Object : %s", usr_obj)
                        else:
                            usr_obj = User.objects.create(**usr_data)
                            logger.info("User Object : %s", usr_obj)
                        opr_wrkr_asgmt_id = operator['ID_ASGMT_WRKR_OPR']
                        logger.info("Operator Wrkr Asgmt : %s",
                                    opr_wrkr_asgmt_id)
                        operator['ID_WRKR'] = worker_obj.ID_WRKR
                        if opr_wrkr_asgmt_id is not None:
                            logger.info("Opr Worker Asgmt Not None")
                            opr_wrkr_obj = WorkerOperatorAssignment.objects.get(
                                ID_ASGMT_WRKR_OPR=opr_wrkr_asgmt_id)
                            logger.info(
                                " Worker Available Instance : %s", opr_wrkr_obj)
                            opr_wrkr_serializer = WorkerOperatorAsgmtSerializer(instance=opr_wrkr_obj,
                                                                                data=operator)
                            if opr_wrkr_serializer.is_valid():
                                logger.info("Operator is valid")
                                opr_wrkr_obj = opr_wrkr_serializer.save()
                            else:
                                return Response(
                                    opr_wrkr_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                                )
                        else:
                            operator.pop('ID_ASGMT_WRKR_OPR')
                            operator['ID_WRKR'] = worker_obj.ID_WRKR
                            opr_wrkr_serializer = WorkerOperatorAsgmtSerializer(
                                data=operator)
                            if opr_wrkr_serializer.is_valid():
                                opr_wrkr_obj = opr_wrkr_serializer.save()
                                logger.info(
                                    "Operator Worker Asgmt Obj : %s", opr_wrkr_obj)

                            else:
                                return Response(
                                    opr_wrkr_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                                )
                elif operator_details is not None and len(operator_details) == 0:
                    logger.info("Operator details Not Found")
                    WorkerOperatorAssignment.objects.filter(
                        ID_WRKR=worker_obj.ID_WRKR).delete()

                return Response({"message": "Update Successfully"}, status=status.HTTP_200_OK)

        except Exception as exp:
            logger.exception(exp)
            return Response({"error": exp.__class__.__name__},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
