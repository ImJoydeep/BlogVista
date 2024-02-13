import os
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from celery import shared_task
import pandas as pd
from basics.notification_views import send_pushnotification
from size.size_filter import create_dataframe_from_data_for_export, global_export_datetime_format, s3_clients
from size.size_filter import to_dict

logger = logging.getLogger(__name__)


@shared_task
def employee_export(response, dynamic_columns, bsn_unit_id, file_name, location, notification_data, device_flag, file_type):
    '''Employee export function and send mail with notification'''
    response = to_dict(response[0])
    headers = [i for i in dynamic_columns]
    try:
        df = pd.DataFrame.from_records(response)
        new_df = df[headers]
        new_df.loc[df["SC_EM"] == 'A', "SC_EM"] = 'Enabled'
        new_df.loc[df["SC_EM"] == 'I', "SC_EM"] = 'Disabled'
        new_df = create_dataframe_from_data_for_export(
            new_df, global_export_datetime_format, bsn_unit_id, 'Size')
        new_df = new_df.drop(['ctime', 'cdate', 'udate', 'utime'], axis=1)
    except Exception as exp:
        logger.exception("Employee Export Exception : %s", exp)
        new_df = df.reindex(columns=df.columns.tolist() +
                            headers)
    new_df.rename(columns=dynamic_columns, inplace=True)
    if str(file_type).lower() == 'xlsx':
        new_df.to_excel(file_name, index=False)
    else:
        new_df.to_csv(file_name, index=False)
    s3_clients.upload_file(file_name, settings.BUCKET_NAME, location)
    fileobject_url = str(s3_clients._endpoint).split('(')[1].replace(
        ')', '/') + settings.BUCKET_NAME + '/' + str(location)
    user_email = User.objects.get(id=notification_data.get('user_id')).email
    message = str(fileobject_url)
    subject = 'Employee Export'
    from_email = os.getenv('MAIL')
    send_mail(subject=subject, message=message, from_email=from_email,
              recipient_list=[user_email])
    if device_flag:
        send_pushnotification(**notification_data)
    os.remove(file_name)
