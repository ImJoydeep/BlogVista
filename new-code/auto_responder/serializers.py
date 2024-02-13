import logging
from celery.beat import ScheduleEntry
from celery import current_app
import json

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import EmailFieldType, EmailTemplate, EmailAction, Category, TemplateAction, DeliveryChannel, \
    TemplateActionMapping, DeliveryChannelMapping, TemplateWarehouseMapping, EmailSendingOptionMapping, \
    EmailDepartmentMapping, EmailFieldTemplateMapping
from department.models import Department
from store.models import Location
from color.color_filter import get_user_details
from .tasks import send_scheduled_email
from django.utils import timezone
from datetime import timedelta
from celery import Celery
from order.models import OrderItemDetails, OrderMaster
app = Celery('dnbadmin')
logger = logging.getLogger(__name__)
created_user_exception_messages = "Created type Exception : %s"


class TemplateActionListSerializer(serializers.ModelSerializer):
    '''TemplateAction List'''

    class Meta:
        ''' Meta class '''
        model = TemplateAction
        fields = '__all__'


class TemplateActionMappingListSerializer(serializers.ModelSerializer):
    '''TemplateAction List'''

    class Meta:
        ''' Meta class '''
        model = TemplateActionMapping
        fields = '__all__'


class EmailFieldTypeRetrieveSerializer(serializers.ModelSerializer):
    '''email Template  retrieve serializer'''
    ETY_CAT = serializers.CharField(source="ETY_CAT.CT_NM")

    class Meta:
        model = EmailFieldType
        fields = ["ETY_ID", "ETY_NM_LABEL", "ETY_VALUE", "ETY_CAT"]
        depth = 1


class EmailTemplateListSerializer(serializers.ModelSerializer):
    '''Email Template List'''
    ET_USR_UPDT = serializers.SerializerMethodField(read_only=True)
    ET_USR_CRT = serializers.SerializerMethodField(read_only=True)
    ET_BCC_EMAIL = serializers.SerializerMethodField(read_only=True)
    ET_TO_EMAIL = serializers.SerializerMethodField(read_only=True)

    def get_ET_USR_UPDT(self, obj):
        ''' Get Updated User Name '''
        try:
            if obj.ET_USR_UPDT:
                return obj.ET_USR_UPDT.get_full_name()
            else:
                return ''
        except Exception as user_exp:
            logger.exception(created_user_exception_messages, user_exp)
            return ''

    def get_ET_USR_CRT(self, obj):
        ''' Get Created User Name '''
        try:
            if obj.ET_USR_CRT:
                return obj.ET_USR_CRT.get_full_name()
            else:
                return ''
        except Exception as user_exp:
            logger.exception(created_user_exception_messages, user_exp)
            return ''

    def get_ET_BCC_EMAIL(self, obj):
        if obj.ET_BCC_EMAIL:

            try:
                bcc_list = eval(obj.ET_BCC_EMAIL)
                bcc_email = ", ".join(bcc_list)
            except Exception as e:
                bcc_email = obj.ET_BCC_EMAIL

        else:
            bcc_email = ""

        return bcc_email

    def get_ET_TO_EMAIL(self, obj):
        if obj.ET_TO_EMAIL:

            try:
                to_email_list = eval(obj.ET_TO_EMAIL)
                to_email = ", ".join(to_email_list)
            except Exception as e:
                to_email = obj.ET_TO_EMAIL

        else:
            to_email = ""

        return to_email

    class Meta:
        ''' Meta class '''
        model = EmailTemplate
        fields = '__all__'


class EmailFieldTypeListSerializer(serializers.ModelSerializer):
    '''Email Template List'''
    ETY_CAT = serializers.IntegerField(source='ETY_CAT.CT_ID')

    class Meta:
        ''' Meta class '''
        model = EmailFieldType
        fields = '__all__'


class CategoryListSerializer(serializers.ModelSerializer):
    '''Category List'''

    class Meta:
        ''' Meta class '''
        model = Category
        fields = '__all__'


class EmailTemplateCreateSerializer(serializers.ModelSerializer):
    '''global setting create serializer'''
    ET_BCC_EMAIL = serializers.ListField()
    ET_TO_EMAIL = serializers.ListField()

    def create(self, validated_data):
        request = self.context['request']
        template_name = self.context['request'].data.get("ET_NM")
        current_user = request.user
        product_field = self.context['request'].data.get("product_field")
        customer_field = self.context['request'].data.get("customer_field")
        order_field = self.context['request'].data.get("order_field")
        product_field_text = self.context['request'].data.get(
            "product_field_text")
        customer_field_text = self.context['request'].data.get(
            "customer_field_text")
        order_field_text = self.context['request'].data.get("order_field_text")
        ET_ACTION_TYPE = request.data.get("ET_ACTION_TYPE")
        ET_WAREHOUSE = request.data.get("ET_WAREHOUSE")
        ET_DELIVERY_CHANNEL = request.data.get("ET_DELIVERY_CHANNEL")
        department = request.data.get("DEPARTMENT")
        sending_option = request.data.get("SENDING_OPTION")
        IS_RECURRING = request.data.get("IS_RECURRING")
        action_type = request.data.get("APPLICABLE_FOR")
        description = template_name
        validated_data['ET_DS'] = description
        validated_data['ET_USR_CRT'] = current_user
        if validated_data.get('ET_Type') is not None and validated_data.get('ET_Type') != "":
            validated_data['ET_Type'] = validated_data.get('ET_Type')
        else:
            validated_data['ET_Type'] = "H"
        if request.data.get('ET_TM_DF') is not None and request.data.get('ET_TM_DF') != "":
            validated_data['ET_TM_DF'] = request.data.get('ET_TM_DF')
        else:
            validated_data['ET_TM_DF'] = "Minute"
        validated_data = self.recurring_data(IS_RECURRING, validated_data)
        save_template = EmailTemplate.objects.create(**validated_data)
        self.mapping_data(save_template, action_type, ET_ACTION_TYPE, ET_WAREHOUSE,
                          ET_DELIVERY_CHANNEL, sending_option, department)

        EmailAction.objects.create(scheduled_time=timezone.now(), last_scheduled_time=timezone.now(),
                                   template=save_template, is_active=True)
        product_field_obj = EmailFieldType.objects.filter(
            ETY_VALUE=product_field).first()
        customer_field_obj = EmailFieldType.objects.filter(
            ETY_VALUE=customer_field).first()
        order_field_obj = EmailFieldType.objects.filter(
            ETY_VALUE=order_field).first()
        self.field_type_mapping(
            product_field_obj, customer_field_obj, order_field_obj, save_template)
        product_field_text_obj = EmailFieldType.objects.filter(
            ETY_VALUE=product_field_text).first()
        customer_field_text_obj = EmailFieldType.objects.filter(
            ETY_VALUE=customer_field_text).first()
        order_field_text_obj = EmailFieldType.objects.filter(
            ETY_VALUE=order_field_text).first()
        self.field_type_text_mapping(
            product_field_text_obj, customer_field_text_obj, order_field_text_obj, save_template)
        return save_template

    def recurring_data(self, IS_RECURRING, validated_data):
        if IS_RECURRING == "Recurring":
            validated_data["is_recurring"] = True
        else:
            validated_data["is_recurring"] = False

        return validated_data

    def mapping_data(self, save_template, action_type, ET_ACTION_TYPE, ET_WAREHOUSE,
                     ET_DELIVERY_CHANNEL, sending_option, department):
        if ET_ACTION_TYPE is not None and ET_ACTION_TYPE != "":
            action_obj = TemplateAction.objects.filter(
                TA_ID=ET_ACTION_TYPE, TA_TYPE=action_type).first()
            valid_action_data = {"ET_TMP": save_template, "TM_AC": action_obj}
            TemplateActionMapping.objects.create(**valid_action_data)

        if sending_option is not None and sending_option != "":
            EmailSendingOptionMapping.objects.create(
                ET_TMP=save_template, ESO_TYPE=sending_option)

        self.multi_data_create(
            ET_WAREHOUSE, ET_DELIVERY_CHANNEL, save_template, department)

    def multi_data_create(self, ET_WAREHOUSE, ET_DELIVERY_CHANNEL, save_template, department):
        if ET_WAREHOUSE is not None and ET_WAREHOUSE != "" and len(ET_WAREHOUSE) > 0:
            for action_data in ET_WAREHOUSE:
                location_obj = Location.objects.filter(id=action_data).first()
                valid_action_data = {
                    "ET_TMP": save_template, "ET_STR": location_obj}
                TemplateWarehouseMapping.objects.create(**valid_action_data)

        if ET_DELIVERY_CHANNEL is not None and ET_DELIVERY_CHANNEL != "" and len(ET_DELIVERY_CHANNEL) > 0:
            for action_data in ET_DELIVERY_CHANNEL:
                delivery_obj = DeliveryChannel.objects.filter(
                    DC_ID=action_data).first()
                valid_action_data = {
                    "ET_TMP": save_template, "DCM_DC": delivery_obj}
                DeliveryChannelMapping.objects.create(**valid_action_data)

        if department is not None and department != "" and len(department) > 0:
            for department_data in department:
                department_obj = Department.objects.filter(
                    department_id=department_data).first()
                valid_action_data = {
                    "ET_TMP": save_template, "ET_DP": department_obj}
                EmailDepartmentMapping.objects.create(**valid_action_data)

    def field_type_mapping(self, product_field_obj, customer_field_obj, order_field_obj, save_template):
        if product_field_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=save_template, EF_TY=product_field_obj)

        if customer_field_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=save_template, EF_TY=customer_field_obj)
        if order_field_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=save_template, EF_TY=order_field_obj)

    def field_type_text_mapping(self, product_field_text_obj, customer_field_text_obj, order_field_text_obj, save_template):
        if product_field_text_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=save_template, EF_TY=product_field_text_obj)

        if customer_field_text_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=save_template, EF_TY=customer_field_text_obj)
        if order_field_text_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=save_template, EF_TY=order_field_text_obj)

    class Meta:
        model = EmailTemplate
        fields = ["ET_ID", "ET_NM", "ET_CN",  "ET_SB", "ET_OD_STS", "ET_HTML_TXT", "ET_INTERVAL", "ET_TM_DF",
                  "ET_Type", "ET_FRM_EMAIL", "ET_RPLY_TO_EMAIL", "ET_BCC_EMAIL", "ET_TO_EMAIL", "ET_AU_RSP_FR",
                  "SC_ET", "is_deleted", "is_blocked", "ET_USR_CRT", "CRT_DT", "ET_USR_UPDT", "UPDT_DT", "ET_INTERVAL",
                  "ET_TM_DF"
                  ]


class EmailFieldTypeCreateSerializer(serializers.ModelSerializer):
    '''Email field Type create serializer'''

    def create(self, validated_data):
        request = self.context['request']
        save_field = EmailFieldType.objects.create(**validated_data)

        return save_field

    class Meta:
        model = EmailTemplate
        fields = ["ETY_ID", "ETY_NM_LABEL", "ETY_VALUE",  "ETY_CAT"
                  ]


class CategoryCreateSerializer(serializers.ModelSerializer):
    '''Category create serializer'''

    def create(self, validated_data):
        request = self.context['request']

        save_category = Category.objects.create(**validated_data)

        return save_category

    class Meta:
        model = Category
        fields = ["CT_ID", "CT_NM"
                  ]


class EmailTempRetrieveSerializer(serializers.ModelSerializer):
    '''email template retrieve serializer'''
    ET_BCC_EMAIL = serializers.SerializerMethodField(read_only=True)
    ET_TO_EMAIL = serializers.SerializerMethodField(read_only=True)
    field_type = serializers.SerializerMethodField(read_only=True)
    ET_USR_CRT = serializers.SerializerMethodField(read_only=True)
    ET_USR_UPDT = serializers.SerializerMethodField(read_only=True)
    ET_ACTION_TYPE = serializers.SerializerMethodField(read_only=True)
    ET_WAREHOUSE = serializers.SerializerMethodField(read_only=True)
    ET_DELIVERY_CHANNEL = serializers.SerializerMethodField(read_only=True)
    IS_RECURRING = serializers.SerializerMethodField(read_only=True)
    APPLICABLE_FOR = serializers.SerializerMethodField(read_only=True)
    DEPARTMENT = serializers.SerializerMethodField(read_only=True)
    SENDING_OPTION = serializers.SerializerMethodField(read_only=True)

    def get_ET_BCC_EMAIL(self, obj):
        if obj.ET_BCC_EMAIL:
            try:
                bcc_list = eval(obj.ET_BCC_EMAIL)
            except Exception as e:
                bcc_list = obj.ET_BCC_EMAIL

        else:
            bcc_list = ""

        return bcc_list

    def get_ET_TO_EMAIL(self, obj):
        if obj.ET_TO_EMAIL:

            try:
                to_email_list = eval(obj.ET_TO_EMAIL)
            except Exception as e:
                to_email_list = obj.ET_TO_EMAIL

        else:
            to_email_list = ""

        return to_email_list

    def get_field_type(self, obj):
        ''' Get Created User Name '''

        if obj.template_filed_type:

            filed_list = obj.template_filed_type.all()
            list_data = []
            for data in filed_list:
                data_dict = {
                    "ID": data.EF_TY.ETY_ID,
                    "ETY_NM_LABEL": data.EF_TY.ETY_NM_LABEL,
                    "ETY_VALUE": data.EF_TY.ETY_VALUE,
                    "ETY_CAT": data.EF_TY.ETY_CAT.CT_ID
                }
                list_data.append(data_dict)

        else:
            list_data = ""

        return list_data

    def get_ET_USR_CRT(self, obj):
        '''get created user name'''
        try:
            if obj.ET_USR_CRT:
                user_id = User.objects.get(
                    id=obj.ET_USR_CRT.id).get_full_name()
            else:
                user_id = ''
        except User.DoesNotExist:
            user_id = ''
        return user_id

    def get_ET_USR_UPDT(self, obj):
        '''get updated user name'''
        try:
            if obj.ET_USR_UPDT:
                user_id = User.objects.get(
                    id=obj.ET_USR_UPDT.id).get_full_name()
            else:
                user_id = ''
        except User.DoesNotExist:
            user_id = ''
        return user_id

    def get_ET_ACTION_TYPE(self, obj):
        if obj.template_action_mapping.all():
            list_data = obj.template_action_mapping.all().first().TM_AC.TA_ID

        else:
            list_data = ''

        return list_data

    def get_ET_WAREHOUSE(self, obj):
        if obj.storage_template_mapping.all():
            warehouse_list_data = [
                data.ET_STR.id for data in obj.storage_template_mapping.all()]

        else:
            warehouse_list_data = ''

        return warehouse_list_data

    def get_ET_DELIVERY_CHANNEL(self, obj):
        if obj.channel_template_mapping.all():
            channel_list_data = [
                data.DCM_DC.DC_ID for data in obj.channel_template_mapping.all()]

        else:
            channel_list_data = ''

        return channel_list_data

    def get_IS_RECURRING(self, obj):
        ''' Recurring Data '''

        if obj.is_recurring:

            is_recurring = "Recurring"

        else:
            is_recurring = "Instant"

        return is_recurring

    def get_APPLICABLE_FOR(self, obj):
        if obj.template_action_mapping.first():
            applicable_type_data = obj.template_action_mapping.first().TM_AC.TA_TYPE
        else:
            applicable_type_data = ""

        return applicable_type_data

    def get_DEPARTMENT(self, obj):
        if obj.email_department_mapping_template.all():
            list_data = [
                data.ET_DP.department_id for data in obj.email_department_mapping_template.all()]

        else:
            list_data = ''

        return list_data

    def get_SENDING_OPTION(self, obj):
        if obj.template_sending_option_mapping.first():
            sending_type_data = obj.template_sending_option_mapping.first().ESO_TYPE
        else:
            sending_type_data = ""

        return sending_type_data

    class Meta:
        model = EmailTemplate
        fields = ["ET_ID", "ET_NM",  "ET_CN",  "ET_SB", "ET_OD_STS", "ET_HTML_TXT", "ET_INTERVAL", "ET_TM_DF",
                  "ET_Type", "ET_FRM_EMAIL", "ET_RPLY_TO_EMAIL", "ET_BCC_EMAIL", "ET_TO_EMAIL", "ET_AU_RSP_FR",
                  "SC_ET", "is_deleted", "is_blocked", "is_default", "ET_USR_CRT", "CRT_DT", "ET_USR_UPDT", "UPDT_DT", "ET_TM_DF",
                  "ET_INTERVAL", "field_type", "ET_ACTION_TYPE", "ET_WAREHOUSE", "ET_DELIVERY_CHANNEL", "IS_RECURRING",
                  "APPLICABLE_FOR", "DEPARTMENT", "SENDING_OPTION"]
        depth = 1


class CategorySerializer(serializers.ModelSerializer):
    '''email Template  retrieve serializer'''

    class Meta:
        model = Category
        fields = ["CT_ID", "CT_NM"]
        depth = 1


class EmailTempUpdateSerializer(serializers.ModelSerializer):
    '''email template fetch update serializer'''

    def update(self, instance, validated_data):
        request = self.context['request']
        current_user = request.user
        instance.ET_NM = validated_data.get('ET_NM', instance.ET_NM)
        instance.ET_DS = validated_data.get(
            'ET_NM')
        instance.ET_CN = validated_data.get(
            'ET_CN', instance.ET_CN)
        instance.ET_HTML_TXT = validated_data.get(
            'ET_HTML_TXT', instance.ET_HTML_TXT)
        instance.ET_Type = validated_data.get(
            'ET_Type', instance.ET_Type)
        instance.ET_SB = validated_data.get(
            'ET_SB', instance.ET_SB)
        instance.ET_INTERVAL = validated_data.get(
            'ET_INTERVAL', instance.ET_INTERVAL)
        instance.ET_TM_DF = validated_data.get(
            'ET_TM_DF', instance.ET_TM_DF)
        instance.ET_FRM_EMAIL = validated_data.get(
            'ET_FRM_EMAIL', instance.ET_FRM_EMAIL)
        instance.ET_RPLY_TO_EMAIL = validated_data.get(
            'ET_RPLY_TO_EMAIL', instance.ET_RPLY_TO_EMAIL)
        ET_BCC_EMAIL = request.data.get("ET_BCC_EMAIL", instance.ET_BCC_EMAIL)
        instance.ET_BCC_EMAIL = json.dumps(ET_BCC_EMAIL)
        ET_TO_EMAIL = request.data.get("ET_TO_EMAIL", instance.ET_TO_EMAIL)
        instance.ET_TO_EMAIL = json.dumps(ET_TO_EMAIL)
        instance.ET_AU_RSP_FR = validated_data.get(
            'ET_AU_RSP_FR', instance.ET_AU_RSP_FR)
        instance.ET_OD_STS = validated_data.get(
            'ET_OD_STS', instance.ET_OD_STS)
        instance.SC_ET = validated_data.get(
            'SC_ET', instance.SC_ET)
        instance.is_default = validated_data.get(
            'is_default', instance.is_default)
        instance.ET_USR_UPDT = current_user
        product_field = self.context['request'].data.get("product_field")
        customer_field = self.context['request'].data.get("customer_field")
        order_field = self.context['request'].data.get("order_field")
        product_field_text = self.context['request'].data.get(
            "product_field_text")
        customer_field_text = self.context['request'].data.get(
            "customer_field_text")
        order_field_text = self.context['request'].data.get("order_field_text")
        instance.save()
        ET_ACTION_TYPE = request.data.get("ET_ACTION_TYPE")
        ET_WAREHOUSE = request.data.get("ET_WAREHOUSE")
        ET_DELIVERY_CHANNEL = request.data.get("ET_DELIVERY_CHANNEL")
        department = request.data.get("DEPARTMENT")
        sending_option = request.data.get("SENDING_OPTION")
        IS_RECURRING = request.data.get("IS_RECURRING")
        self.recurring_update_data(IS_RECURRING, validated_data, instance)
        action_type = request.data.get("APPLICABLE_FOR")
        self.mapping_update_data(instance, action_type, ET_ACTION_TYPE, ET_WAREHOUSE,
                                 ET_DELIVERY_CHANNEL, sending_option, department)
        product_field_obj = EmailFieldType.objects.filter(
            ETY_VALUE=product_field).first()
        customer_field_obj = EmailFieldType.objects.filter(
            ETY_VALUE=customer_field).first()
        order_field_obj = EmailFieldType.objects.filter(
            ETY_VALUE=order_field).first()
        self.field_type_update_mapping(
            product_field_obj, customer_field_obj, order_field_obj, instance)
        product_field_text_obj = EmailFieldType.objects.filter(
            ETY_VALUE=product_field_text).first()
        customer_field_text_obj = EmailFieldType.objects.filter(
            ETY_VALUE=customer_field_text).first()
        order_field_text_obj = EmailFieldType.objects.filter(
            ETY_VALUE=order_field_text).first()

        self.field_type_text_update_mapping(
            product_field_text_obj, customer_field_text_obj, order_field_text_obj, instance)
        return instance

    ET_BCC_EMAIL = serializers.SerializerMethodField(read_only=True)
    ET_TO_EMAIL = serializers.SerializerMethodField(read_only=True)

    def get_ET_BCC_EMAIL(self, obj):
        if obj.ET_BCC_EMAIL:
            try:
                bcc_list = eval(obj.ET_BCC_EMAIL)
                bcc_email = ", ".join(bcc_list)
            except Exception as e:
                logger.exception("error", e)
                bcc_email = obj.ET_BCC_EMAIL

        else:
            bcc_email = ""

        return bcc_email

    def get_ET_TO_EMAIL(self, obj):
        if obj.ET_TO_EMAIL:
            try:
                to_email_list = eval(obj.ET_TO_EMAIL)
                to_email = ", ".join(to_email_list)
            except Exception as e:
                logger.exception("error", e)
                to_email = obj.ET_TO_EMAIL

        else:
            to_email = ""

        return to_email

    def recurring_update_data(self, IS_RECURRING, validated_data, instance):
        if IS_RECURRING == "Recurring":
            validated_data["is_recurring"] = True
        else:
            validated_data["is_recurring"] = False
        instance.is_recurring = validated_data.get(
            "is_recurring", instance.is_recurring)
        instance.save()

        return instance

    def mapping_update_data(self, instance, action_type, ET_ACTION_TYPE, ET_WAREHOUSE,
                            ET_DELIVERY_CHANNEL, sending_option, department):

        if not ET_ACTION_TYPE:
            TemplateActionMapping.objects.filter(ET_TMP=instance).delete()
        else:
            TemplateActionMapping.objects.filter(ET_TMP=instance).delete()
            action_obj = TemplateAction.objects.filter(
                TA_ID=ET_ACTION_TYPE, TA_TYPE=action_type).first()
            valid_action_data = {"ET_TMP": instance, "TM_AC": action_obj}
            TemplateActionMapping.objects.create(**valid_action_data)

        if not sending_option:
            EmailSendingOptionMapping.objects.filter(ET_TMP=instance).delete()
        else:
            EmailSendingOptionMapping.objects.filter(ET_TMP=instance).delete()
            EmailSendingOptionMapping.objects.create(
                ET_TMP=instance, ESO_TYPE=sending_option)

        instance = self.multi_data_update(
            ET_WAREHOUSE, ET_DELIVERY_CHANNEL, instance, department)

        instance.save()
        return instance

    def multi_data_update(self, ET_WAREHOUSE,
                          ET_DELIVERY_CHANNEL, instance, department):

        if len(ET_WAREHOUSE) == 0:
            TemplateWarehouseMapping.objects.filter(ET_TMP=instance).delete()

        else:
            TemplateWarehouseMapping.objects.filter(ET_TMP=instance).delete()
            for action_data in ET_WAREHOUSE:
                location_obj = Location.objects.filter(id=action_data).first()
                valid_action_data = {
                    "ET_TMP": instance, "ET_STR": location_obj}
                TemplateWarehouseMapping.objects.create(**valid_action_data)

        if len(ET_DELIVERY_CHANNEL) == 0:
            DeliveryChannelMapping.objects.filter(ET_TMP=instance).delete()

        else:
            DeliveryChannelMapping.objects.filter(ET_TMP=instance).delete()
            for action_data in ET_DELIVERY_CHANNEL:
                delivery_obj = DeliveryChannel.objects.filter(
                    DC_ID=action_data).first()
                valid_action_data = {
                    "ET_TMP": instance, "DCM_DC": delivery_obj}
                DeliveryChannelMapping.objects.create(**valid_action_data)

        if len(department) == 0:
            EmailDepartmentMapping.objects.filter(ET_TMP=instance).delete()
        else:
            EmailDepartmentMapping.objects.filter(ET_TMP=instance).delete()
            for department_data in department:
                department_obj = Department.objects.filter(
                    department_id=department_data).first()
                valid_action_data = {
                    "ET_TMP": instance, "ET_DP": department_obj}
                EmailDepartmentMapping.objects.create(**valid_action_data)

        return instance

    def field_type_update_mapping(self, product_field_obj, customer_field_obj, order_field_obj, instance):
        EmailFieldTemplateMapping.objects.filter(ET_TMP=instance).delete()

        if product_field_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=instance, EF_TY=product_field_obj)

        if customer_field_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=instance, EF_TY=customer_field_obj)
        if order_field_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=instance, EF_TY=order_field_obj)

        instance.save()

        return instance

    def field_type_text_update_mapping(self, product_field_text_obj, customer_field_text_obj, order_field_text_obj, instance):
        EmailFieldTemplateMapping.objects.filter(ET_TMP=instance).delete()

        if product_field_text_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=instance, EF_TY=product_field_text_obj)

        if customer_field_text_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=instance, EF_TY=customer_field_text_obj)
        if order_field_text_obj:
            EmailFieldTemplateMapping.objects.create(
                ET_TMP=instance, EF_TY=order_field_text_obj)

        instance.save()

        return instance

    class Meta:
        model = EmailTemplate
        fields = ["ET_ID", "ET_NM",  "ET_CN",  "ET_SB", "ET_OD_STS", "ET_HTML_TXT", "ET_INTERVAL", "ET_TM_DF",
                  "ET_Type", "ET_FRM_EMAIL", "ET_RPLY_TO_EMAIL", "ET_BCC_EMAIL", "ET_TO_EMAIL", "ET_AU_RSP_FR",
                  "SC_ET", "is_deleted", "is_blocked", "ET_USR_CRT", "CRT_DT", "ET_USR_UPDT", "UPDT_DT", ]


class EmailFieldTypeUpdateSerializer(serializers.ModelSerializer):
    '''email template fetch update serializer'''

    def update(self, instance, validated_data):
        request = self.context['request']
        instance.ETY_NM_LABEL = validated_data.get(
            'ETY_NM_LABEL', instance.ETY_NM_LABEL)
        instance.ETY_VALUE = validated_data.get(
            'ETY_VALUE', instance.ETY_VALUE)
        instance.ETY_CAT = validated_data.get(
            'ETY_CAT', instance.ETY_CAT)
        instance.save()
        return instance

    class Meta:
        model = EmailFieldType
        fields = ["ETY_ID", "ETY_NM_LABEL",  "ETY_VALUE",  "ETY_CAT", ]


class CategoryUpdateSerializer(serializers.ModelSerializer):
    '''email template fetch update serializer'''

    def update(self, instance, validated_data):
        request = self.context['request']
        instance.CT_NM = validated_data.get(
            'CT_NM')

        instance.save()
        return instance

    class Meta:
        model = Category
        fields = ["CT_ID", "CT_NM", ]


class EmailTemplateStatusSerializer(serializers.ModelSerializer):
    '''email template status serializer'''

    def update(self, instance, validated_data):
        request = self.context['request']
        current_user = request.user
        instance.SC_ET = validated_data.get('SC_ET', instance.SC_ET)
        instance.ET_USR_UPDT = current_user.id
        instance.save()
        logger.info('Global setting stat update serializer')
        return instance

    class Meta:
        model = EmailTemplate
        fields = ["ET_ID", "ET_NM", "SC_ET"]
        read_only_fields = ["ET_ID", "ET_NM"]


class LocationListSerializer(serializers.ModelSerializer):
    '''Location List'''

    class Meta:
        ''' Meta class '''
        model = Location
        fields = ['id', 'NM_LCN']


class DeliveryChannelListSerializer(serializers.ModelSerializer):
    '''Location List'''

    class Meta:
        ''' Meta class '''
        model = DeliveryChannel
        fields = '__all__'


class OrderDetailsSerializer(serializers.ModelSerializer):
    '''OrderDetails List'''
    product_name = serializers.SerializerMethodField(read_only=True)
    sku = serializers.SerializerMethodField(read_only=True)
    price = serializers.SerializerMethodField(read_only=True)
    qty = serializers.SerializerMethodField(read_only=True)
    
    def get_product_name(self, obj):
        if obj:
             return obj.OD_ITM.NM_ITM
        return ''
    def get_sku(self, obj):
        if obj:
             return obj.OD_ITM.AS_ITM_SKU
        return ''

    def get_price(self, obj):
        if obj:
             return obj.OD_ITM_TOTL_AMT
        return ''

    def get_qty(self, obj):
        if obj:
            return int(obj.OD_ITM_QTY_PKD)
        return ''
    
    class Meta:
        ''' Meta class '''
        model = OrderItemDetails
        fields = ['product_name','sku','price','qty']
