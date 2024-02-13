''' Party  Contact Details File'''
import logging
import os
import pandas as pd
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from rest_framework import serializers
from django.db import transaction
from celery import shared_task
from json import loads, dumps
from rest_framework import status
from globalsettings.models import BusinessUnitSetting, GlobalSetting
from basics.notification_views import send_pushnotification
from size.size_filter import global_export_datetime_format, s3_clients
from size.size_filter import convert_datetimeformat_without_error
from .models import (Telephone, EmailAddress,
                     PostalCodeReference, PartyContactMethod, Address, State)
from .serializers import (PostalCodeSerializer,
                          EmailAddressSerializer, TelephoneSerializer, AddressSerializer,
                          PartyContactMethodSerializer)


logger = logging.getLogger(__name__)


def contact_details_create(data, partyroleasign_id):
    ''' Create a new Party Contact Details '''
    result = {}
    if len(data['contact_details']) > 0:
        logger.info("Contact Details : %s",
                    data['contact_details'])
        for contact_detail in data['contact_details']:
            logger.info("Contact Detail : %s",
                        contact_detail)
            postal_code_id = None
            phone_id = None
            email_adds_id = None
            address_id = None

            state_name = contact_detail.get("ST_CNCT", None)

            if state_name:
                state_obj = State.objects.filter(NM_ST__iexact=state_name)
                if state_obj.exists():
                    state_id = state_obj.values_list(
                        "ID_ST", flat=True).first()
                    contact_detail['ID_ST'] = state_id

            if contact_detail.get('PH_CMPL'):
                phone_data = {
                    "CD_CY_ITU": contact_detail['CD_CY_ITU'],
                    "PH_CMPL": contact_detail.get('PH_CMPL'),
                    "TA_PH": str(contact_detail.get('PH_CMPL')).split()[0],
                    "TL_PH": str(contact_detail.get('PH_CMPL')).split()[1]
                }
                phone = TelephoneSerializer(data=phone_data)
                if not phone.is_valid():
                    result['errors'] = phone.errors
                    result['status'] = status.HTTP_400_BAD_REQUEST
                    return result
                phone_save = phone.save()
                phone_id = phone_save.ID_PH

            logger.info("Phone Id : %s", phone_id)

            if contact_detail.get('EM_ADS'):
                email_data = {
                    "EM_ADS_LOC_PRT": str(contact_detail['EM_ADS']).split('@')[0],
                    "EM_ADS_DMN_PRT": str(contact_detail['EM_ADS']).split('@')[1],
                }
                email = EmailAddressSerializer(data=email_data)
                if not email.is_valid():
                    result['errors'] = email.errors
                    result['status'] = status.HTTP_400_BAD_REQUEST
                    return result

                email_save = email.save()
                email_adds_id = email_save.ID_EM_ADS

            logger.info("Email Adds Id : %s",
                        email_adds_id)

            if contact_detail.get('CD_PSTL'):
                postal_address_data = {
                    "CD_PSTL": contact_detail['CD_PSTL'],
                    "CD_CY_ITU": contact_detail['CD_CY_ITU']}
                postal = PostalCodeSerializer(
                    data=postal_address_data)
                if not postal.is_valid():
                    result['errors'] = postal.errors
                    result['status'] = status.HTTP_400_BAD_REQUEST
                    return result

                postal_save = postal.save()
                postal_code_id = postal_save.ID_PSTL_CD

            address_data = {
                "FST_NM": contact_detail.get('FST_NM', ''),
                "LST_NM": contact_detail.get('LST_NM', ''),
                "A1_ADS": contact_detail['A1_ADS'],
                "A2_ADS": contact_detail['A2_ADS'],
                "CI_CNCT": contact_detail['CI_CNCT'],
                "CD_CY_ITU": contact_detail['CD_CY_ITU'],
                "ID_ST": contact_detail['ID_ST'],
                "ID_PSTL_CD": postal_code_id
            }
            address = AddressSerializer(data=address_data)
            if not address.is_valid():
                result['errors'] = address.errors
                result['status'] = status.HTTP_400_BAD_REQUEST
                return result
            address_save = address.save()
            address_id = address_save.ID_ADS
            logger.info("Address data : %s",
                        address_data)
            logger.info("Address Id : %s",
                        address_id)
            party_contact_data = {
                "CD_TYP_CNCT_PRPS": contact_detail['CD_TYP_CNCT_PRPS'],
                "CD_TYP_CNCT_MTH": contact_detail['CD_TYP_CNCT_MTH'],
                "ID_PRTY_RO_ASGMT": partyroleasign_id,
                "ID_ADS": address_id,
                "ID_EM_ADS": email_adds_id,
                "CD_STS": contact_detail.get('CD_STS', 'A'),
                "ID_PH": phone_id,
                "IS_SHIPPING": contact_detail.get('IS_SHIPPING', False),
                "IS_BILLING": contact_detail.get('IS_BILLING', False)
            }
            logger.info("Party Contact Data : %s",
                        party_contact_data)
            party_contact = PartyContactMethodSerializer(
                data=party_contact_data)
            if not party_contact.is_valid():
                logger.info("Party Contact Error")
                result['errors'] = party_contact.errors
                result['status'] = status.HTTP_400_BAD_REQUEST
                return result

            party_contact.save()
            logger.info(party_contact.data.get('ID_PRTY_CNCT_MTH'))

    else:
        logger.info("No Contact Details Found")

    return result


def contact_details_delete(data, party_role_assign_id):
    '''Delete Party Contact Methods'''
    if party_role_assign_id is not None:
        instance = {'ID_PRTY_RO_ASGMT': party_role_assign_id}
        data = [party_role_assign_id]
    for contact_id in data:
        if party_role_assign_id is None:
            instance = {'ID_PRTY_CNCT_MTH': contact_id}
        party_contact_obj = PartyContactMethod.objects.filter(**instance)
        if party_contact_obj.exists():
            for temp_id in party_contact_obj:
                if temp_id.ID_ADS.ID_PSTL_CD is not None:
                    temp_id.ID_ADS.ID_PSTL_CD.delete()
                    logger.info("Postal Code deleted")

                if temp_id.ID_ADS is not None:
                    temp_id.ID_ADS.delete()
                    logger.info("Address deletedd")

                if temp_id.ID_EM_ADS is not None:
                    temp_id.ID_EM_ADS.delete()
                    logger.info("Email Address deleted")

                if temp_id.ID_PH is not None:
                    temp_id.ID_PH.delete()
                    logger.info("Telephone deleted")

                if temp_id:
                    temp_id.delete()
                    logger.info("Party Contact method deleted")


def phone_number_update(contact, phone_id):
    '''Update phone number'''
    if contact['PH_CMPL']:
        phone_data = {
            "CD_CY_ITU": contact['CD_CY_ITU'],
            "PH_CMPL": contact['PH_CMPL'],
            "TA_PH": str(contact['PH_CMPL']).split()[0],
            "TL_PH": str(contact['PH_CMPL']).split()[1]
        }
        result = save_phone_data(phone_data, phone_id)
        phone_id = result.get('ID_PH', None)
    return phone_id


def email_update(contact, email_adds_id):
    '''Update email'''
    if contact['EM_ADS']:
        email_data = {
            "EM_ADS_LOC_PRT": str(contact['EM_ADS']).split('@')[0],
            "EM_ADS_DMN_PRT": str(contact['EM_ADS']).split('@')[1],
        }
        result = save_email_data(email_data, email_adds_id)
        email_adds_id = result.get('ID_EM_ADS', None)
    return email_adds_id


def party_contact_method_update(prty_contact_method_id, party_contact, party_contact_data):
    '''Update Party contact method'''
    if prty_contact_method_id:
        prty_contact_obj = PartyContactMethod.objects.filter(
            ID_PRTY_CNCT_MTH=prty_contact_method_id)
        if prty_contact_obj:
            party_contact = PartyContactMethodSerializer(instance=prty_contact_obj.first(),
                                                         data=party_contact_data)

    if party_contact.is_valid(raise_exception=True):
        part_contact_save = party_contact.save()
        party_contact_id = part_contact_save.ID_PRTY_CNCT_MTH
        logger.info("Party Contact: %s",
                    party_contact_id)


def contact_details_update(contact_details, partyroleasign_id):
    ''' Update contact Details'''
    result = {}
    for contact in contact_details:
        phone_id = contact.get('ID_PH', None)

        state_name = contact.get("ST_CNCT", None)

        if state_name is not None:
            state_obj = State.objects.filter(NM_ST__iexact=state_name)
            if state_obj.exists():
                state_id = state_obj.values_list(
                    "ID_ST", flat=True).first()
                contact['ID_ST'] = state_id
        phone_id = phone_number_update(contact, phone_id)
        logger.info("Phone Id : %s", phone_id)

        email_adds_id = contact.get('ID_EM_ADS', None)
        email_adds_id = email_update(contact, email_adds_id)
        logger.info("Email Adds Id : %s",
                    email_adds_id)

        postal_code_id = contact.get('ID_PSTL_CD', None)
        if contact['CD_PSTL']:
            postal_address_data = {
                "CD_PSTL": contact['CD_PSTL'],
                "CD_CY_ITU": contact['CD_CY_ITU']}
            result = save_postal_code(postal_address_data, postal_code_id)
            postal_code_id = result.get('ID_PSTL_CD', None)

        address_id = contact.get('ID_ADS', None)
        address_data = {
            "A1_ADS": contact['A1_ADS'],
            "A2_ADS": contact['A2_ADS'],
            "CI_CNCT": contact['CI_CNCT'],
            "CD_CY_ITU": contact['CD_CY_ITU'],
            "ID_ST": contact['ID_ST'],
            "ID_PSTL_CD": postal_code_id
        }
        address_serializer = AddressSerializer(data=address_data)
        if address_id is not None:
            address_obj = Address.objects.get(
                ID_ADS=address_id)

            address_serializer = AddressSerializer(
                instance=address_obj, data=address_data)

        if address_serializer.is_valid(raise_exception=True):
            address_save = address_serializer.save()
            address_id = address_save.ID_ADS

        prty_contact_method_id = contact.get(
            'ID_PRTY_CNCT_MTH', None)
        party_contact = None
        party_contact_data = {
            "CD_TYP_CNCT_PRPS": contact['CD_TYP_CNCT_PRPS'],
            "CD_TYP_CNCT_MTH": contact['CD_TYP_CNCT_MTH'],
            "ID_PRTY_RO_ASGMT": partyroleasign_id,
            "ID_ADS": address_id,
            "ID_EM_ADS": email_adds_id,
            "ID_PH": phone_id,
            "CD_STS": contact['CD_STS']}
        party_contact = PartyContactMethodSerializer(
            data=party_contact_data)
        party_contact_method_update(
            prty_contact_method_id, party_contact, party_contact_data)

    return result


def save_postal_code(postal_address_data, postal_code_id):
    ''' Save POstal Code '''
    result = {}
    postal_serializer = None
    if postal_code_id is not None:
        postal_obj = PostalCodeReference.objects.get(
            ID_PSTL_CD=postal_code_id)

        postal_serializer = PostalCodeSerializer(instance=postal_obj,
                                                 data=postal_address_data)
    else:
        postal_serializer = PostalCodeSerializer(
            data=postal_address_data)

    if postal_serializer.is_valid(raise_exception=True):
        postal_save = postal_serializer.save()
        postal_code_id = postal_save.ID_PSTL_CD
        result['ID_PSTL_CD'] = postal_code_id
    return result


def save_email_data(email_data, email_adds_id):
    ''' Save Email Data '''
    result = {}
    email_serializer = None

    email_serializer = EmailAddressSerializer(data=email_data)
    if email_adds_id is not None:
        email_obj = EmailAddress.objects.get(
            ID_EM_ADS=email_adds_id)

        email_serializer = EmailAddressSerializer(
            instance=email_obj, data=email_data)
    if email_serializer.is_valid(raise_exception=True):
        email_save = email_serializer.save()
        email_adds_id = email_save.ID_EM_ADS
        result['ID_EM_ADS'] = email_adds_id
    return result


def save_phone_data(phone_data, phone_id):
    ''' Save Phone Data '''
    result = {}
    phone_serializer = None
    if phone_id:
        phone_obj = Telephone.objects.get(
            ID_PH=phone_id)
        phone_serializer = TelephoneSerializer(
            instance=phone_obj, data=phone_data)
    else:
        phone_serializer = TelephoneSerializer(data=phone_data)

    if phone_serializer.is_valid(raise_exception=True):
        phone_save = phone_serializer.save()
        phone_id = phone_save.ID_PH
        result['ID_PH'] = phone_id
    return result


def to_dict(input_ordered_dict):
    return loads(dumps(input_ordered_dict, default=str))


@shared_task
def supplier_export(response, dynamic_columns, bsn_unit_id, file_names, location, notification_data, device_flag, file_types):
    '''Vendor export function and send mail with notification'''
    response = to_dict(response[0])
    headers = list(dynamic_columns)
    temp = global_export_datetime_format
    try:
        df = pd.DataFrame.from_records(response)
        new_df = df[headers]
        new_df.loc[df["SC_SPR"] == 'A', "SC_SPR"] = 'Enabled'
        new_df.loc[df["SC_SPR"] == 'I', "SC_SPR"] = 'Disabled'
        if bsn_unit_id != '0':
            try:
                global_obj = GlobalSetting.objects.filter(
                    ID_GB_STNG=BusinessUnitSetting.objects.get(ID_BSN_UN=bsn_unit_id).ID_GB_STNG.ID_GB_STNG)
                date_format = global_obj.last().ID_BA_DFMT.name
                timezone = global_obj.last().ID_BA_TZN.gmt_offset
                convert_datetimeformat_without_error(
                    new_df, date_format, timezone, 'MDF_DT')
                new_df = new_df.drop(
                    ['ctime', 'cdate', 'udate', 'utime'], axis=1)
            except Exception as exp:
                logger.info("Businessunit exception : %s", exp)
                convert_datetimeformat_without_error(
                    new_df, temp['date_format'], temp['time_zone'], 'MDF_DT')
                new_df = new_df.drop(
                    ['ctime', 'cdate', 'udate', 'utime'], axis=1)
        else:
            convert_datetimeformat_without_error(
                new_df, temp['date_format'], temp['time_zone'], 'MDF_DT')
            new_df = new_df.drop(
                ['ctime', 'cdate', 'udate', 'utime'], axis=1)
    except Exception as exp:
        logger.info("Response has no data exception : %s", exp)
        new_df = df.reindex(columns=df.columns.tolist() +
                            headers)
    new_df.rename(columns=dynamic_columns, inplace=True)
    if str(file_types).lower() == 'xlsx':
        new_df.to_excel(file_names, index=False)
    else:
        new_df.to_csv(file_names, index=False)
    s3_clients.upload_file(file_names, settings.BUCKET_NAME, location)
    object_urls = str(s3_clients._endpoint).split('(')[1].replace(
        ')', '/') + settings.BUCKET_NAME + '/' + str(location)
    user_email = User.objects.get(id=notification_data.get('user_id')).email
    messages = str(object_urls)
    subject = 'Vendor Export'
    from_email = os.getenv('MAIL')
    send_mail(subject=subject, message=messages, from_email=from_email,
              recipient_list=[user_email])
    if device_flag:
        send_pushnotification(**notification_data)
    os.remove(file_names)


def manufacturer_export(response, dynamic_columns, bsn_unit_id, file_name, location, notification_data, device_flag, file_type):
    '''Manufacturer export function and send mail with notification'''
    response = to_dict(response[0])
    headers = list(dynamic_columns)
    temp = global_export_datetime_format
    try:
        df = pd.DataFrame.from_records(response)
        new_dataframe = df[headers]
        new_dataframe.loc[df["SC_MF"] == 'A', "SC_MF"] = 'Enabled'
        new_dataframe.loc[df["SC_MF"] == 'I', "SC_MF"] = 'Disabled'
        if bsn_unit_id != '0':
            try:
                global_obj = GlobalSetting.objects.filter(
                    ID_GB_STNG=BusinessUnitSetting.objects.get(ID_BSN_UN=bsn_unit_id).ID_GB_STNG.ID_GB_STNG)
                date_format = global_obj.last().ID_BA_DFMT.name
                timezone = global_obj.last().ID_BA_TZN.gmt_offset
                convert_datetimeformat_without_error(
                    new_dataframe, date_format, timezone, 'MDF_DT')
                new_dataframe = new_dataframe.drop(
                    ['ctime', 'cdate', 'udate', 'utime'], axis=1)
            except Exception as exp:
                logger.info("Businessunit exception : %s", exp)
                convert_datetimeformat_without_error(
                    new_dataframe, temp['date_format'], temp['time_zone'], 'MDF_DT')
                new_dataframe = new_dataframe.drop(
                    ['ctime', 'cdate', 'udate', 'utime'], axis=1)
        else:
            convert_datetimeformat_without_error(
                new_dataframe, temp['date_format'], temp['time_zone'], 'MDF_DT')
            new_dataframe = new_dataframe.drop(
                ['ctime', 'cdate', 'udate', 'utime'], axis=1)
    except Exception as exp:
        logger.info("Response has no data exception : %s", exp)
        new_dataframe = df.reindex(columns=df.columns.tolist() +
                                   headers)
    new_dataframe.rename(columns=dynamic_columns, inplace=True)
    if str(file_type).lower() == 'xlsx':
        new_dataframe.to_excel(file_name, index=False)
    else:
        new_dataframe.to_csv(file_name, index=False)
    s3_clients.upload_file(file_name, settings.BUCKET_NAME, location)
    objects_url = str(s3_clients._endpoint).split('(')[1].replace(
        ')', '/') + settings.BUCKET_NAME + '/' + str(location)
    user_email = User.objects.get(id=notification_data.get('user_id')).email
    msg = str(objects_url)
    subject = 'Manufacturer Export'
    from_email = os.getenv('MAIL')
    send_mail(subject=subject, message=msg, from_email=from_email,
              recipient_list=[user_email])
    if device_flag:
        send_pushnotification(**notification_data)
    os.remove(file_name)
