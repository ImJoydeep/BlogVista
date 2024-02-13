from auto_responder.import_config import load_dotenv, logger, re, Concat, Coalesce, V, render_to_string,\
os,\
SiteContactMethod, Location, WorkerPositionAssignment, Position, EmailAddress, PartyContactMethod, Department,\
OrderMaster, OrderItemDetails, strip_tags, send_mail, EmailMultiAlternatives,\
EmailAction, EmailTemplate, EmailDepartmentMapping, TemplateWarehouseMapping, Operator, WorkerOperatorAssignment
from django.utils import timezone
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Send scheduled emails'

    def handle(self, *args, **options):
        all_recurring_temp = EmailTemplate.objects.filter(is_recurring=True, is_default=True)
        for each_template in all_recurring_temp:
            if each_template.template_action_mapping.latest().TM_AC.TA_NM == "Order Create":
                order_creation_mail = OrderCreate()
                order_creation_mail.order_create_process(each_template)


class OrderCreate():
    def order_create_process(self, template):
        all_orders_list = OrderMaster.objects.filter(
            OMS_OD_STS='new', IS_VERIFIED=False).order_by("OD_ID")
        for each_order in all_orders_list:
            order_number = each_order.CU_OD_ID
            order_template = template
            scheduled_emails = EmailAction.objects.filter(
                template=order_template, is_active=True).first()
            curr_time = timezone.now()
            if order_template.ET_TM_DF == "Minute":
                time_interval = int(order_template.ET_INTERVAL)
            else:
                time_interval = int(order_template.ET_INTERVAL) * 60

            time_check = int(curr_time.minute) % time_interval
            if int(time_check) == 0:
                scheduled_emails.last_scheduled_time = curr_time
                common_class = CommonEmailParamClass()
                common_class.email_send(order_template, curr_time, each_order, order_number)

    def department_mail(self, department):
        department_link_list = department

        all_department = Department.objects.filter(department_id__in=department_link_list).values_list("department_id",flat=True)

        department_position_list = Position.objects.filter(department_id__in=all_department).values_list("ID_PST",flat=True)

        worker_list = WorkerPositionAssignment.objects.filter(ID_PST__in=department_position_list).values_list("ID_WRKR", flat=True).distinct()

        worker_op_list = WorkerOperatorAssignment.objects.filter(ID_WRKR__in=worker_list).values_list(
            "ID_OPR", flat=True).distinct()

        emails_contact_list = Operator.objects.filter(ID_OPR__in=worker_op_list).values_list("EMAIL_USR", flat=True)



        email_list = []
        if emails_contact_list.count() > 0:
            for mail in emails_contact_list:
                email_list.append(mail)

        return email_list



    def store_mail(self, store):
        store_list = store
        site_data = Location.objects.filter(id__in=store_list).values_list("ID_STE", flat=True).distinct()

        email_data = SiteContactMethod.objects.filter(ID_STE__in=site_data).exclude(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=True, ID_EM_ADS__EM_ADS_DMN_PRT__isnull=True).values_list("ID_EM_ADS__EM_ADS_LOC_PRT",
                                                                                            "ID_EM_ADS__EM_ADS_DMN_PRT").annotate(email=Concat('ID_EM_ADS__EM_ADS_LOC_PRT', V('@'),'ID_EM_ADS__EM_ADS_DMN_PRT')).values_list("email", flat=True)
        email_list = []
        if email_data.count() > 0:
            email_list.append(email_data)

        return email_list

    def cus_email(self, order):
        customer_email_data = order.OD_CUS_EMAIL
        return customer_email_data



class CommonEmailParamClass:
    def email_send(self, order_template, curr_time, each_order, order_number):
        str_email_body = ""
        content_type = None
        try:
            order_subject = order_template.ET_SB
            subject = self.fetch_dynamic_subject(order_subject, each_order)

            html_content = order_template.ET_HTML_TXT
            str_content = order_template.ET_CN
            if html_content:
                str_email_body = str(html_content)
                content_type = "html"
            if str_content:
                str_email_body = str(str_content)
                content_type = "text"

            current_url = os.getenv('EMAIL_REDIRECT_LINK')
            modified_body = str_email_body.format(
                verify_order=current_url + "/orders/all-orders/view/" + order_number,
                product_name="", first_name="", customer_name="")
            updated_body = self.updated_body(each_order, modified_body)

            recipient_list = self.fetch_store_email(each_order, order_template)
            print(recipient_list)
            print(curr_time)
            bcc_list = eval(order_template.ET_BCC_EMAIL)
            try:
                msg = EmailMultiAlternatives(
                    subject,
                    updated_body,
                    order_template.ET_FRM_EMAIL,
                    recipient_list,
                    bcc=bcc_list
                )
                if content_type == "html":
                    msg.attach_alternative(updated_body, "text/html")
                    msg.send()

                if content_type == "text":
                    msg.attach_alternative(updated_body, "text")
                    msg.send()

            except Exception as e:
                logger.exception("Sending Exception : %s", e)


        except Exception as e:
            logger.exception("Email Sending Exception : %s", e)


    def fetch_store_email(self, order, order_template):
        email_list = []
        email = ""
        if order_template.ET_AU_RSP_FR == "Customer":
            order_creation_mail = OrderCreate()
            cus_email = order_creation_mail.cus_email(order)
            email_list.append(cus_email)

        all_sending_option = order_template.template_sending_option_mapping.all()
        for option in all_sending_option:
            if option.ESO_TYPE == "Department":
                department_list = EmailDepartmentMapping.objects.filter(ET_TMP=order_template).values_list('ET_DP', flat=True).distinct()
                order_creation_mail = OrderCreate()
                email = order_creation_mail.department_mail(department_list)

            if option.ESO_TYPE == "storeManager":
                store_list = TemplateWarehouseMapping.objects.filter(ET_TMP=order_template).values_list('ET_STR', flat=True).distinct()
                order_creation_mail = OrderCreate()
                email = order_creation_mail.store_mail(store_list)
            email_list += email
        return email_list


    def fetch_dynamic_subject(self, subject, order):
        order_item = OrderItemDetails.objects.filter(OD_ID=order.OD_ID).last()

        existing_key_list = re.findall(r'\{(.+?)\}', subject)

        db_val = {
            "name_data": order_item.OD_ITM.NM_ITM  if order_item and order_item.OD_ITM is not None else '',
            "sku_data": order_item.OD_ITM.AS_ITM_SKU if order_item and order_item.OD_ITM is not None else '',
            "customer_name_data": order.OD_CUS_NM,
            "order_currency_code_data": order.OD_CUR_COD,
            "custom_order_number_data": order.CU_OD_ID,
            "payment_method_data": order.PT_MD_NM,
            "order_status_data": order.OMS_OD_STS
        }

        new_dict = {
            "sku": "sku_data",
            "customer_name": "customer_name_data",
            "product_name": "name_data",
            "custom_order_number": "custom_order_number_data",
            "order_currency_code": "order_currency_code_data"
        }

        if order_item and order:
            new_sub = subject.split("{")[0]
            if len(existing_key_list) > 0:
                for i in existing_key_list:
                    if i in new_dict:
                        new_sub += " " +db_val[new_dict[i]]

            return new_sub

    def updated_body(self, order, html_txt):
        order_item = OrderItemDetails.objects.filter(OD_ID=order.OD_ID).last()
        existing_key_list = re.findall(r'\{(.+?)\}', html_txt)

        db_val = {
            "name_data": order_item.OD_ITM.NM_ITM  if order_item and order_item.OD_ITM is not None else '',
            "sku_data": order_item.OD_ITM.AS_ITM_SKU if order_item and order_item.OD_ITM is not None else '',
            "customer_name_data": order.OD_CUS_NM,
            "order_currency_code_data": order.OD_CUR_COD,
            "custom_order_number_data": order.CU_OD_ID
        }

        new_dict = {
            "sku": "sku_data",
            "customer_name": "customer_name_data",
            "product_name": "name_data",
            "custom_order_number": "custom_order_number_data",
            "order_currency_code": "order_currency_code_data"
        }

        if order_item and order:
            for i in existing_key_list:
                if i in new_dict:
                    html_txt = html_txt.format(db_val[new_dict[i]])

        return html_txt