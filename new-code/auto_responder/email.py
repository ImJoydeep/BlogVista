import logging
from auto_responder.import_config import load_dotenv, logger, re, Concat, Coalesce, V, render_to_string, \
    os, \
    SiteContactMethod, Location, WorkerPositionAssignment, Position, EmailAddress, PartyContactMethod, Department, \
    OrderMaster, OrderItemDetails, strip_tags, send_mail, EmailMultiAlternatives, TemplateActionMapping, \
    EmailAction, EmailTemplate, EmailDepartmentMapping, TemplateWarehouseMapping, WorkerOperatorAssignment, Operator
from django.utils import timezone
import json
import ast
from auto_responder.serializers import OrderDetailsSerializer
from django.conf import settings
from django.template import Template, Context

logger = logging.getLogger(__name__)


def send_instant_email(order_type, order):
    logger.info(
        "Send Instant Mail Payload Order Data : %s", order)

    if order_type == "Cancelled":
        temp_action = TemplateActionMapping.objects.filter(
            TM_AC__TA_NM="Order Cancel").last()
        each_template = temp_action.ET_TMP
        if not each_template.is_recurring and each_template.is_default:
            order_process_mail = OrderProcess()
            order_process_mail.order_cancel_process(each_template, order)

    if order_type == "Ready_for_Pickup":
        temp_action = TemplateActionMapping.objects.filter(
            TM_AC__TA_NM='Ready for Pickup').last()

        each_template = temp_action.ET_TMP
        if not each_template.is_recurring and each_template.is_default:
            order_process_mail = OrderProcess()
            order_process_mail.order_ready_for_pickup_process(
                each_template, order)

    if order_type == "Flag_Order":

        temp_action = TemplateActionMapping.objects.filter(
            TM_AC__TA_NM="Flag Order").last()
        each_template = temp_action.ET_TMP
        if not each_template.is_recurring and each_template.is_default:
            order_process_mail = OrderProcess()
            order_process_mail.order_flag_process(each_template, order)


def send_order_create_email(order_type, order):
    ''' Order Create Email '''
    logger.info("Order Type : %s and Order Data : %s", order_type, order)
    if order_type == "Order Create":
        temp_action = TemplateActionMapping.objects.filter(
            TM_AC__TA_NM="Order Create").last()
        logger.info("Template Action : %s", temp_action)
        each_template = temp_action.ET_TMP
        logger.info("Each Template : %s", each_template)
        if not each_template.is_recurring and each_template.is_default:
            order_process_mail = OrderProcess()
            order_process_mail.order_create_process(each_template, order)


class OrderProcess():
    def order_cancel_process(self, template, order):
        cancel_orders = OrderMaster.objects.filter(
            OMS_OD_STS='void', OD_STS='canceled', CU_OD_ID=order.CU_OD_ID).first()

        order_template_attached = template
        scheduled_emails_obj = EmailAction.objects.filter(
            template=order_template_attached, is_active=True).first()
        curr_time_attached = timezone.now()
        scheduled_emails_obj.last_scheduled_time = curr_time_attached
        scheduled_emails_obj.save()
        common_email_class = CommonEmailParamClass()
        common_email_class.send_email(
            order_template_attached, curr_time_attached, cancel_orders)

    def order_create_process(self, template, order):
        create_orders = OrderMaster.objects.filter(
            OMS_OD_STS='new', OD_STS='pending', CU_OD_ID=order.CU_OD_ID).first()
        logger.info("Create Order Object : %s", create_orders)

        order_template_attached = template
        scheduled_emails_obj = EmailAction.objects.filter(
            template=order_template_attached, is_active=True).first()
        logger.info("Schedule Email Object : %s", scheduled_emails_obj)
        curr_time_attached = timezone.now()
        scheduled_emails_obj.last_scheduled_time = curr_time_attached
        scheduled_emails_obj.save()
        common_email_class = CommonEmailParamClass()
        common_email_class.send_email(
            order_template_attached, curr_time_attached, create_orders)

    def order_ready_for_pickup_process(self, template, order):
        orders_ready_for_pick = OrderMaster.objects.filter(
            OMS_OD_STS='ready_for_pickup', CU_OD_ID=order.CU_OD_ID).first()
        
        order_template_attached = template
        scheduled_emails_obj = EmailAction.objects.filter(
            template=order_template_attached, is_active=True).first()
        curr_time_attached = timezone.now()
        scheduled_emails_obj.last_scheduled_time = curr_time_attached
        scheduled_emails_obj.save()
        common_email_class = CommonEmailParamClass()
        common_email_class.send_email(
            order_template_attached, curr_time_attached, orders_ready_for_pick)

    def order_flag_process(self, template,  order):
        flag_orders = OrderMaster.objects.filter(
            OMS_OD_STS='on hold', OD_STS='on hold', CU_OD_ID=order.CU_OD_ID).first()
        order_templates = template
        scheduled_emails_fetch = EmailAction.objects.filter(
            template=order_templates, is_active=True).first()
        curr_time_check = timezone.now()
        scheduled_emails_fetch.last_scheduled_time = curr_time_check
        scheduled_emails_fetch.save()
        common_class = CommonEmailParamClass()
        common_class.send_email(order_templates, curr_time_check, flag_orders)

    def department_related_mail(self, department):
        department_link_list = department
        all_department = Department.objects.filter(
            department_id__in=department_link_list).values_list("department_id", flat=True)
        department_position_list = Position.objects.filter(
            department_id__in=all_department).values_list("ID_PST", flat=True)
        worker_list = WorkerPositionAssignment.objects.filter(
            ID_PST__in=department_position_list).values_list("ID_WRKR__ID_PRTY_RO_ASGMT", flat=True).distinct()
        worker_op_as_list = WorkerOperatorAssignment.objects.filter(ID_WRKR__in=worker_list).values_list(
            "ID_OPR", flat=True).distinct()

        emails_op_list = Operator.objects.filter(
            ID_OPR__in=worker_op_as_list).values_list("EMAIL_USR", flat=True)
        email_list_dept = []
        if emails_op_list.count() > 0:
            for mail in emails_op_list:
                email_list_dept.append(mail)

        return email_list_dept

    def store_manager_mail(self, store):
        store_list = store
        site_data_loc = Location.objects.filter(
            id__in=store_list).values_list("ID_STE", flat=True).distinct()
        email_data_site = SiteContactMethod.objects.filter(ID_STE__in=site_data_loc).exclude(ID_EM_ADS__EM_ADS_LOC_PRT__isnull=True, ID_EM_ADS__EM_ADS_DMN_PRT__isnull=True).values_list("ID_EM_ADS__EM_ADS_LOC_PRT",
                                                                                                                                                                                         "ID_EM_ADS__EM_ADS_DMN_PRT").annotate(email=Concat('ID_EM_ADS__EM_ADS_LOC_PRT', V('@'), 'ID_EM_ADS__EM_ADS_DMN_PRT')).values_list("email", flat=True)
        email_store_list = []
        if email_data_site.count() > 0:
            email_store_list.append(email_data_site)

        return email_store_list

    def cust_email(self, order):
        customer_email = order.OD_CUS_EMAIL
        return customer_email


class CommonEmailParamClass:
    def send_email(self, order_template, curr_time, each_order):
        str_email_body = ""
        content_type = None
        logger.info("Current time : %s", curr_time)
        try:
            order_subject = order_template.ET_SB
            subject = self.fetch_all_dynamic_subject(order_subject, each_order)
            html_content = order_template.ET_HTML_TXT
            str_content = order_template.ET_CN
            if html_content:
                str_email_body = str(html_content)
                content_type = "html"
            if str_content:
                str_email_body = str(str_content)
                content_type = "text"
            modified_body = str_email_body

            updated_body = self.updated_mail_body(each_order, modified_body)
            recipient_inst_list = self.fetch_applied_for_email(
                each_order, order_template)
            logger.info("recipient_inst_list : %s", recipient_inst_list)
            bcc_email_list = eval(order_template.ET_BCC_EMAIL)
            try:
                msg_email = EmailMultiAlternatives(
                    subject,
                    updated_body,
                    order_template.ET_FRM_EMAIL,
                    recipient_inst_list,
                    bcc=bcc_email_list
                )
                if content_type == "text":
                    msg_email.attach_alternative(updated_body, "text")
                    msg_email.send()
                if content_type == "html":
                    msg_email.attach_alternative(updated_body, "text/html")
                    msg_email.send()
            except Exception as e:
                logger.exception(
                    "Sending Exception Email Error Message : %s", e)

        except Exception as e:
            logger.exception("Email Sending Failure : %s", e)

    def fetch_applied_for_email(self, order, order_template):
        email_list_data = []
        email_fetch = ""
        if order_template.ET_AU_RSP_FR == "Customer":
            order_process_mail = OrderProcess()
            customer_email = order_process_mail.cust_email(order)
            email_list_data.append(customer_email)

        all_sending_options = order_template.template_sending_option_mapping.all()
        for option in all_sending_options:
            if option.ESO_TYPE == "Department":
                department_list_related = EmailDepartmentMapping.objects.filter(
                    ET_TMP=order_template).values_list('ET_DP', flat=True).distinct()
                order_process_mail = OrderProcess()
                email_fetch = order_process_mail.department_related_mail(
                    department_list_related)

            if option.ESO_TYPE == "Store Manager":
                store_list_related = TemplateWarehouseMapping.objects.filter(
                    ET_TMP=order_template).values_list('ET_STR', flat=True).distinct()
                order_process_mail = OrderProcess()
                email_fetch = order_process_mail.store_manager_mail(
                    store_list_related)
            email_list_data += email_fetch

        return email_list_data

    def fetch_all_dynamic_subject(self, subject, order):
        order_item = OrderItemDetails.objects.filter(OD_ID=order.OD_ID).last()
        existing_key_list = re.findall(r'\{(.+?)\}', subject)
        db_val = {
            "name_data": order_item.OD_ITM.NM_ITM if order_item and order_item.OD_ITM is not None else '',
            "sku_data": order_item.OD_ITM.AS_ITM_SKU if order_item and order_item.OD_ITM is not None else '',
            "customer_name_data": order.OD_CUS_NM,
            "order_currency_code_data": order.OD_CUR_COD,
            "custom_order_number_data": order.CU_OD_ID,
            "order_status_data": order.OMS_OD_STS,
            "payment_method_data": order.PT_MD_NM,

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
                        new_sub += " " + db_val[new_dict[i]]

            return new_sub

    def updated_mail_body(self, order, html_txt):
        json_data = {}
        order_item_obj = OrderItemDetails.objects.filter(
            OD_ID=order.OD_ID)
        items = OrderDetailsSerializer(order_item_obj, many=True).data
        if order.orderpaymentdetails_set.first():
            transaction_additional_info = order.orderpaymentdetails_set.first().OD_PAY_ADDT_INFO
            data_list = ast.literal_eval(transaction_additional_info)
            json_data = json.loads(data_list[0])
        card_type = json_data.get("card_type", '')
        card_number = json_data.get("acc_number", '')
        html = '''{%for item in items%}
                <tr>
                    <th style="border-bottom: 1px solid rgba(125, 128, 151, 0.5); font-size: 14px; color: #121212; padding: 12px 15px;" align="left">Items</th>
                    <th style="border-bottom: 1px solid rgba(125, 128, 151, 0.5); font-size: 14px; color: #121212; padding: 12px 15px;" align="right">Qty.</th>
                    <th style="border-bottom: 1px solid rgba(125, 128, 151, 0.5); font-size: 14px; color: #121212; padding: 12px 15px;" align="right">Price</th>                                
                </tr>
                <tr>                               
                    <td align="left" style="width:100%; padding: 8px 16px; font-size: 14px; color: #121212; padding: 10px 15px; border-bottom: 1px solid #DDDEE6;">
                        <div>
                            <b style="display: block;">{{item.product_name}}</b>
                            <span style="display: block; margin: 10px 0; font-weight: 400;">SKU : {{item.sku}}</span>
                        </div>
                    </td>
                    <td align="right" style="width:100%; padding: 8px 16px; font-size: 14px; color: #121212; padding: 10px 15px; font-weight: 500; border-bottom: 1px solid #DDDEE6;">
                        {{item.qty}}
                    </td>
                    <td align="right" style="width:100%; padding: 8px 16px; font-size: 14px; color: #121212; padding: 10px 15px; font-weight: 500; border-bottom: 1px solid #DDDEE6;">
                        ${{item.price}}
                    </td>
                </tr>
                {%endfor%}'''
        template = Template(str(html))
        items = {"items": items}
        rendered_html = template.render(Context(items))
        db_val_fetch = {
            "customer_name": order.OD_CUS_NM,
            "order_currency_code": order.OD_CUR_COD,
            "custom_order_number": order.CU_OD_ID,
            "first_name": order.OD_CUST.CUST_FNM,
            "card_type": str(card_type),
            "card_number": str(card_number),
            "store_city_name": order.orderbillingaddress_set.first().OD_BA_CT,
            "store_address_name": order.orderbillingaddress_set.first().OD_BA_ST + " " + order.orderbillingaddress_set.first().OD_BA_RGN +" " + 
            order.orderbillingaddress_set.first().OD_BA_CT + " " + order.orderbillingaddress_set.first().OD_BA_CTR_CODE + " " +
            order.orderbillingaddress_set.first().OD_BA_CTR_CODE + " " +
            order.orderbillingaddress_set.first().OD_BA_PIN,
            "store_ph_no": order.orderbillingaddress_set.first().OD_BA_PH,
            "product": rendered_html,
            "total_price": order.OD_TL_AMT,
            "shipping_price": order.OD_SHP_AMT if order.OD_SHP_AMT else '0.00',
            "grand_total_price": order.OD_NT_AMT,
            "verify_order": ""
        }

        html_txt = html_txt.format(**db_val_fetch)

        return html_txt
