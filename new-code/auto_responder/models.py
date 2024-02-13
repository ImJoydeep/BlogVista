from django.db import models
from django.conf import settings
from order.models import OrderMaster
from department.models import Department
from store.models import Location
import json
# Create your models here.

STATUS_CHOICES = (
    ("A", "Active"),
    ("I", "Inactive")
)

APPLICABLE_CHOICES = (
    ("Others", "OTHERS"),
    ("Orders", "ORDERS")
)


TEMPLATE_TYPE = (
    ("H", "HTML"),
    ("T", "TEXT"),
    ("T/H", "TEXT/HTML")
)

TIME_DEFINITION = (
    ("Hour", "HOUR"),
    ("Minute", "MINUTE"),
)

ORDER_STATUS = (
    ("New", "New"),
    ("Ready to Pick", "Ready to Pick"),
    ("Ready for Pickup", "Ready for Pickup"),
    ("Void", "Void"),
    ("Attention Needed", "Attention Needed"),
    ("Completed", "Completed"),
)


class Category(models.Model):
    CT_ID = models.BigAutoField("Category ID", primary_key=True)
    CT_NM = models.CharField(max_length=255, default='', blank=True)

    def __str__(self):
        return str(self.CT_NM)
    class Meta:
        ''' Meta Class '''
        db_table = 'EmailCategory'


class EmailTemplate(models.Model):
    ET_ID = models.BigAutoField("Email Template ID", primary_key=True)
    ET_NM = models.CharField(
        "EmailTemplateName", unique=True, max_length=255, default='', blank=True)
    ET_DS = models.CharField("EmailTemplateDescription",
                             max_length=255, default='', blank=True)
    ET_CN = models.TextField(blank=True, default='',
                             help_text="EmailTemplateContent")
    ET_HTML_TXT = models.TextField(blank=True, default='',
                                   help_text="Email Template Html Content")
    ET_SB = models.CharField(max_length=255, default='',
                             blank=True, help_text="Subject")
    ET_Type = models.CharField(
        "Email template type", max_length=10, choices=TEMPLATE_TYPE, default="H")
    ET_FRM_EMAIL = models.CharField(
        max_length=255, default='', blank=True, help_text="From Email")
    ET_RPLY_TO_EMAIL = models.CharField(
        max_length=255, default='', blank=True, help_text="Email Template Reply to email")
    ET_BCC_EMAIL = models.CharField(
        max_length=255, default='', blank=True, help_text="Bcc Email")
    ET_TO_EMAIL = models.CharField(
        max_length=255, default='', blank=True, help_text="To Email")
    ET_AU_RSP_FR = models.CharField(
        max_length=255, default='', blank=True, help_text="Auto responder applied for")
    SC_ET = models.CharField(
        "Status", max_length=2, choices=STATUS_CHOICES, default="A")
    ET_OD_STS = models.CharField(
        "Order Status", max_length=100, choices=ORDER_STATUS, default="")
    ET_INTERVAL = models.CharField(max_length=100, blank=True, default="", help_text="Interval")
    ET_TM_DF = models.CharField(
         max_length=100, choices=TIME_DEFINITION, default="Minute", help_text="Time Definition")
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    is_default = models.BooleanField(default=True)
    ETY_OD = models.ForeignKey(OrderMaster, on_delete=models.SET_NULL,
                                blank=True, null=True, default='', related_name="email_template_order_mapping")
    ET_USR_CRT = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   blank=True, null=True, related_name="email_template_createdby_user")
    CRT_DT = models.DateTimeField(
        "Date Created", null=True, blank=True, auto_now_add=True)
    ET_USR_UPDT = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    blank=True, null=True, related_name="email_template_updatedby_user")
    UPDT_DT = models.DateTimeField(
        "Last Updated Date", null=True, blank=True, auto_now=True)

    def __str__(self):
        return str(self.ET_NM)

    def soft_delete(self):
        self.is_deleted = True
        return self.save()

    def restore_soft_delete(self):
        self.is_deleted = False
        return self.save()

    def blocked_item(self):
        self.is_blocked = True
        return self.save()

    def restore_blocked_item(self):
        self.is_blocked = False
        return self.save()

    def save_ET_BCC_EMAIL(self, ET_BCC_EMAIL):
        self.ET_BCC_EMAIL = ",".join(map(str, ET_BCC_EMAIL))
        self.save()

    def get_ET_BCC_EMAIL(self):
        return self.ET_BCC_EMAIL.split(",")

    def save_ET_TO_EMAIL(self, ET_TO_EMAIL):
        self.ET_TO_EMAIL = ",".join(map(str, ET_TO_EMAIL))
        self.save()

    def get_ET_TO_EMAIL(self):
        return self.ET_TO_EMAIL.split(",")

    class Meta:
        ''' Meta Class '''
        db_table = 'EmailTemplate'


class EmailAction(models.Model):
    EA_ID = models.BigAutoField("Email Action ID", primary_key=True)
    is_active = models.BooleanField(default=True)
    scheduled_time = models.DateTimeField()
    last_scheduled_time = models.DateTimeField()
    template = models.ForeignKey(EmailTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="template_action")

    class Meta:
        ''' Meta Class '''
        db_table = 'EmailAction'


class EmailFieldType(models.Model):
    ETY_ID = models.BigAutoField("Email Field Type ID", primary_key=True)
    ETY_NM_LABEL = models.CharField(max_length=255, default='', blank=True)
    ETY_VALUE = models.CharField(max_length=255, default='', blank=True)
    ETY_CAT = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                   blank=True, null=True, default='', related_name="email_type_category")

    def __str__(self):
        return str(self.ETY_NM_LABEL) + " --- " + str(self.ETY_VALUE)
    class Meta:
        ''' Meta Class '''
        db_table = 'EmailFieldType'


class EmailFieldTemplateMapping(models.Model):
    EFT_ID = models.BigAutoField("Email Field Type ID", primary_key=True)
    EF_TY = models.ForeignKey(EmailFieldType, on_delete=models.SET_NULL,
                                   blank=True, null=True, default='', related_name="email_type_template_mapping")
    ET_TMP = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL,
                                blank=True, null=True, default='', related_name="template_filed_type")

    def __str__(self):
        return str(self.EF_TY.ETY_NM_LABEL) + " --- " + str(self.EF_TY.ETY_VALUE)
    class Meta:
        ''' Meta Class '''
        db_table = 'EmailFieldTemplateMapping'


class EmailDepartmentMapping(models.Model):
    EDM_ID = models.BigAutoField("Email Template Department Mapping  ID", primary_key=True)
    ET_TMP = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="email_department_mapping_template")
    ET_DP = models.ForeignKey(Department, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="email_department_mapping_department")

    class Meta:
        ''' Meta Class '''
        db_table = 'EmailDepartmentMapping'


class EmailSendingOptionMapping(models.Model):
    ES_ID = models.BigAutoField("Email Store Manager ID", primary_key=True)
    ET_TMP = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="template_sending_option_mapping")
    ESO_TYPE = models.CharField(
        max_length=255,  blank=True, help_text="Email Sending Option Type", default='')

    class Meta:
        ''' Meta Class '''
        db_table = 'EmailSendingOptionMapping'


class TemplateWarehouseMapping(models.Model):
    ST_ID = models.BigAutoField("Storage ID", primary_key=True)
    ET_TMP = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="storage_template_mapping")
    ET_STR = models.ForeignKey(Location, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="location_template_mapping")
    class Meta:
        ''' Meta Class '''
        db_table = 'TemplateWarehouseMapping'


class DeliveryChannel(models.Model):
    DC_ID = models.BigAutoField("Delivery Channel ID", primary_key=True)
    DC_NM = models.CharField(max_length=255, default='', blank=True)
    class Meta:
        ''' Meta Class '''
        db_table = 'DeliveryChannel'


class DeliveryChannelMapping(models.Model):
    DCM_ID = models.BigAutoField("Delivery Channel ID", primary_key=True)
    DCM_DC = models.ForeignKey(DeliveryChannel, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="channel_mapping")
    ET_TMP = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="channel_template_mapping")
    class Meta:
        ''' Meta Class '''
        db_table = 'DeliveryChannelMapping'


class TemplateAction(models.Model):
    TA_ID = models.BigAutoField("Email Template Action ID", primary_key=True)
    TA_NM = models.CharField(max_length=255, default='', blank=True)
    TA_TYPE = models.CharField(
        max_length=255, choices=APPLICABLE_CHOICES, help_text="Order Action Type", default='Others')

    class Meta:
        ''' Meta Class '''
        db_table = 'TemplateAction'


class TemplateActionMapping(models.Model):
    TAM_ID = models.BigAutoField("Email Template Action Mapping ID", primary_key=True)
    ET_TMP = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="template_action_mapping")
    TM_AC = models.ForeignKey(TemplateAction, on_delete=models.SET_NULL,
                               blank=True, null=True, default='', related_name="action_template_action_mapping")

    class Meta:
        ''' Meta Class '''
        db_table = 'TemplateActionMapping'
        ordering = ['TAM_ID']