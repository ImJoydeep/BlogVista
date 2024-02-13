'''Order Model'''
from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from product.models.models_item_stock import ItemBarcode
from worker.models import Employee

from product.models.models_item import Item
from store.models import Location
from taxonomy.models import Color
from party.models import PartyRoleAssignment, Party

MAG_STATUS_CHOICES = (
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("complete", "Complete"),
    ("canceled", "Canceled"),
    ("on hold", "On Hold"),
    ("ready", "Ready"),
)
STATUS_CHOICES = (
    ("new", "New"),
    ("ready_to_pick", "Ready to Pick"),
    ("ready_for_pickup", "Ready for Pickup"),
    ("void", "Void"),
    ("on hold", "Attention Needed"),
    ("complete", "Completed"),
)

CUST_STATUS_CHOICES = (
    ("A", "Active"),
    ("I", "Inactive")
)
order_id_help_text = "Order ID"
invoice_id_help_text = "Order Invoice ID"
order_item_help_text = "Order Item ID"
store_id_key = "Store ID"


class CommonFeatures(models.Model):
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    CRT_DT = models.DateTimeField(auto_now_add=True)
    UPDT_DT = models.DateTimeField(auto_now=True)

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

    class Meta:
        abstract = True


class Customer(CommonFeatures):
    CUST_FNM = models.CharField(
        "CustomerFirstName", max_length=100, blank=True, default=None)
    CUST_LNM = models.CharField(
        "CustomerLastName", max_length=100, blank=True, default=None)
    CUST_EMAIL = models.CharField(
        "CustomerEmail", max_length=100, blank=True, default=None)
    CUST_PH = models.CharField(
        "CustomerPhone", max_length=20, blank=True, default=None)
    IS_GUST = models.BooleanField(default=False)
    CUST_ST = models.CharField("StatusCode", max_length=2,
                               choices=CUST_STATUS_CHOICES, default="A")
    ID_PRTY_RO_ASGMT = models.ForeignKey(
        PartyRoleAssignment, on_delete=models.CASCADE, blank=True, null=True, verbose_name="PartyRoleAssignmentID", related_name="party_role_assignment_cust", db_column="ID_PRTY_RO_ASGMT")
    ID_PRTY = models.ForeignKey(
        Party, on_delete=models.CASCADE, verbose_name="PartyID", blank=True, null=True, related_name="party_customer", db_column="ID_PRTY")
    CRT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               blank=True, null=True, related_name='Cust_Createuser', db_column="CRT_BY")
    UPDT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                blank=True, null=True, related_name='Cust_Modifiyuser', db_column="UPDT_BY")

    class Meta:
        db_table = "CUST_INFO"


class OrderMaster(CommonFeatures):
    OD_ID = models.BigAutoField("OrderID", primary_key=True)
    CU_OD_ID = models.CharField(
        "CustomOrderID", default=None, unique=True, max_length=52, blank=True)
    CH_OD_ID = models.IntegerField("ChannelOrderID", null=True, blank=True)
    PT_MD_NM = models.CharField(
        "PaymentMethodName", max_length=100, blank=True, default=None)
    OD_CUS_NM = models.CharField(
        "CustomerName", max_length=100, blank=True, default=None)
    OD_CUS_EMAIL = models.CharField(
        "CustomerEmail", max_length=100, blank=True, default=None)
    OD_QTY = models.IntegerField("OderQuantity", blank=True, null=True)
    IS_GUST = models.BooleanField(default=False)
    OD_TL_AMT = models.FloatField(
        null=True, blank=True, help_text="Total Amount")
    OD_NT_AMT = models.FloatField(
        null=True, blank=True, help_text="Net Amount")
    OD_SHP_AMT = models.FloatField(
        null=True, blank=True, help_text="Shipping Amount")
    OD_DIS_AMT = models.FloatField(
        null=True, blank=True, help_text="Discount Amount")
    OD_STR_NM = models.CharField(
        max_length=150, blank=True, default=None, help_text="Store Name")
    OD_PD_AMT = models.FloatField(
        null=True, blank=True, help_text="Paid Amount")
    OD_TX_AMT = models.FloatField(
        null=True, blank=True, help_text="Tax Amount")
    OD_STS = models.CharField(max_length=10,
                              blank=True, choices=MAG_STATUS_CHOICES, default='pending', help_text="Order Status")
    OD_DATE = models.CharField(
        max_length=30, blank=True, default=None, help_text="Order Date")
    OD_CUR_COD = models.CharField(
        max_length=10, blank=True, default=None, help_text="Currency Code")
    OD_IP_ADDR = models.CharField(
        max_length=20, blank=True, default=None, help_text="IP Address")
    IS_MAIL = models.IntegerField(null=True, blank=True)
    OD_PAY_STS = models.CharField(
        max_length=100, blank=True, default=None, help_text="Payment Status")
    STR_ID = models.IntegerField(
        null=True, blank=True,  help_text=store_id_key)
    OD_PROT_ID = models.CharField(
        max_length=256, blank=True, default=None, help_text="Protect Code")
    OD_INVC_NUM = models.CharField(max_length=50,
                                   default=None,
                                   blank=True,
                                   help_text="Order Invoice Number")
    OD_SHP_NUM = models.CharField(max_length=50,
                                  default=None,
                                  blank=True,
                                  help_text="Order Shipping Number")
    OD_INST = models.CharField(max_length=250,
                               blank=True,
                               default=None,
                               help_text="Order Instruction")
    OD_CUST = models.ForeignKey(Customer,
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True,
                                help_text="Customer")
    OD_TYPE = models.CharField(max_length=20, blank=True, default=None)
    OD_SHIP_DESC = models.CharField(
        max_length=100, blank=True, default=None, help_text="Order Shipping Description")
    IS_VERIFIED = models.BooleanField(default=False)
    OMS_OD_STS = models.CharField(max_length=20,
                                  blank=True, choices=STATUS_CHOICES, default='new', help_text="OMS Order Status")

    class Meta:
        db_table = "OD_MAST"


class OrderBillingAddress(CommonFeatures):
    OD_PRT_ID = models.IntegerField("OrderParentID", null=True)
    OD_ENT_ID = models.IntegerField("OrderEntityID", null=True)
    OD_BA_FN = models.CharField(
        "OrderBillingFirstName", max_length=100, blank=True, default=None)
    OD_BA_MN = models.CharField(
        "OrderBillingMiddleName", max_length=100, blank=True, default=None)
    OD_BA_LN = models.CharField(
        "OrderBillingLastName", max_length=100, blank=True, default=None)
    OD_BA_EMAIL = models.CharField(
        "OrderBillingEmail", max_length=100, blank=True, default=None)
    OD_BA_PH = models.CharField(
        "OrderBillingPhone", max_length=20, blank=True, default=None)
    OD_BA_ST = models.CharField(
        "OrderBillingStreet", max_length=256, blank=True, default=None)
    OD_BA_CT = models.CharField(
        "OrderBillingCity", max_length=20, blank=True, default=None)
    OD_BA_RGN = models.CharField(
        "OrderBillingRegion", max_length=20, blank=True, default=None)
    OD_BA_RGN_CODE = models.CharField(
        "OrderBillingRegionCode", max_length=50, blank=True, default=None)
    OD_BA_CTR_CODE = models.CharField(
        "OrderBillingCountryCode", max_length=50, blank=True, default=None)
    OD_BA_PIN = models.CharField(
        "OrderBillingPincode", max_length=100, blank=True, default=None)
    OD_BA_OD_ID = models.ForeignKey(OrderMaster,
                                    on_delete=models.CASCADE,
                                    blank=True,
                                    null=True)
    OD_CUST = models.ForeignKey(Customer,
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True,
                                help_text="Customer")
    OD_BA_RGN_ID = models.IntegerField(
        "OrderBillingRegionID", blank=True, null=True)
    OD_BA_CUS_ADD_ID = models.IntegerField(
        "OrderBillingCustomerAddressID", null=True)

    class Meta:
        db_table = "OD_BA"


class OrderShippingAddress(CommonFeatures):
    OD_PRT_ID = models.IntegerField("OrderParentID", null=True, blank=True)
    OD_ENT_ID = models.IntegerField("OrderEntityID", null=True, blank=True)
    OD_SA_FN = models.CharField(
        "OrderDeliveryFirstName", max_length=100, blank=True, default=None)
    OD_SA_MN = models.CharField(
        "OrderDeliveryMiddleName", max_length=100, blank=True, default=None)
    OD_SA_LN = models.CharField(
        "OrderDeliveryLastName", max_length=100, blank=True, default=None)
    OD_SA_EMAIL = models.CharField(
        "OrderDeliveryEmail", max_length=100, blank=True, default=None)
    OD_SA_PH = models.CharField(
        "OrderDeliveryPhone", max_length=20, blank=True, default=None)
    OD_SA_ST = models.CharField(
        "OrderDeliveryStreet", max_length=256, blank=True, default=None)
    OD_SA_CT = models.CharField(
        "OrderDeliveryCity", max_length=20, blank=True, default=None)
    OD_SA_RGN = models.CharField(
        "OrderDeliveryRegion", max_length=20, blank=True, default=None)
    OD_SA_RGN_CODE = models.CharField(
        "OrderDeliveryRegionCode", max_length=50, blank=True, default=None)
    OD_SA_CTR_CODE = models.CharField(
        "OrderDeliveryCountryCode", max_length=50, blank=True, default=None)
    OD_SA_PIN = models.CharField(
        "OrderDeliveryPincode", max_length=100, blank=True, default=None)
    OD_SA_OD_ID = models.ForeignKey(OrderMaster,
                                    on_delete=models.CASCADE,
                                    blank=True,
                                    null=True)
    OD_CUST = models.ForeignKey(Customer,
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True,
                                help_text="Customer")
    OD_SA_RGN_ID = models.IntegerField(
        "OrderShippingRegionID", null=True, blank=True)
    OD_SA_CUS_ADD_ID = models.IntegerField(
        "OrderShippingCustomerAddressID", null=True)

    class Meta:
        db_table = "OD_SA"


class OrderItemDetails(CommonFeatures):
    OD_ITM_ID = models.BigAutoField(
        "OrderItemID", primary_key=True, help_text=order_item_help_text)
    OD_ID = models.ForeignKey(OrderMaster,
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True, help_text=order_id_help_text)
    OD_ITM_QTY = models.FloatField(
        blank=True, null=True, help_text="Order Item Quantity")
    OD_ITM_CL_QTY = models.FloatField(
        blank=True, null=True, help_text="Order Item Cancelled Quantity")
    OD_ITM_INVC_QTY = models.FloatField(
        blank=True, null=True, help_text="Order Item Invoiced Quantity")
    OD_ITM_RETN_QTY = models.FloatField(
        blank=True, null=True, help_text="Order Item Returned Quantity")
    OD_ITM_RFND_QTY = models.FloatField(
        blank=True, null=True, help_text="Order Item Refunded Quantity")
    OD_ITM_SHP_QTY = models.FloatField(
        blank=True, null=True, help_text="Order Item Shipped Quantity")
    OD_ITM = models.ForeignKey(Item,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text="Order Item")
    OD_ITM_BS_PR = models.FloatField(
        blank=True, null=True, help_text="Order Item Base Price")
    OD_ITM_OR_PR = models.FloatField(
        blank=True, null=True, help_text="Order Item Original Price")
    OD_ITM_DSC_AMT = models.FloatField(
        blank=True, null=True, help_text="Order Item Discount Amount")
    OD_ITM_DSC_INVC = models.FloatField(
        blank=True, null=True, help_text="Order Item Discount Invoiced")
    OD_ITM_DSC_PER = models.FloatField(
        blank=True, null=True, help_text="Order Item Discount Percentage")
    OD_ITM_TOTL_AMT = models.FloatField(
        blank=True, null=True, help_text="Order Item Total Amount")
    OD_ITM_AMT_REF = models.FloatField(
        blank=True, null=True, help_text="Order Item Amount Refund")
    OD_ITM_FRE_SHP = models.BooleanField(
        default=False, blank=True, null=True, help_text="Order Item Free Shipping")
    OD_ITM_CRT_DT = models.CharField(
        max_length=100, blank=True, default=None, help_text="Order Item Created")
    OD_ITM_TAX_AMT = models.FloatField(
        null=True, blank=True, help_text="Order Item Tax Amount")
    OD_ITM_TAX_CL_AMT = models.FloatField(
        null=True, blank=True, help_text="Order Item Tax Cancel Amount")
    OD_ITM_TAX_INVC_AMT = models.FloatField(
        null=True, blank=True, help_text="Order Item Tax Invoiced Amount")
    OD_ITM_TAX_PER = models.FloatField(
        null=True, blank=True, help_text="Order Item Tax Percentage")
    OD_ITM_LCN = models.ForeignKey(Location,
                                   on_delete=models.CASCADE,
                                   null=True,
                                   blank=True,
                                   help_text="Order Item Location")
    OD_ITM_INVC = models.CharField(
        max_length=50, blank=True, default=None, help_text="Order Item Invoiced")
    OD_ITM_UPDT_DT = models.CharField(
        max_length=100, blank=True, default=None, help_text="Order Item Updated at")
    OD_ITM_DSC_TX_CMPSATN_AMT = models.FloatField(
        blank=True, null=True, help_text="Order Item Discount Tax Compensation Amount")
    OD_ITM_IS_QTY_DCML = models.BooleanField(
        blank=True, null=True, default=False, help_text="Order Item Is Decimal")
    OD_ITM_IS_VRTL = models.BooleanField(
        blank=True, null=True, default=False, help_text="Order Item Is Virtual")
    OD_ITM_ID_ITM = models.IntegerField(
        blank=True, null=True, help_text=order_item_help_text)
    OD_ITM_NM = models.CharField(
        max_length=255, blank=True, default=None, help_text="Order Item Name")
    OD_ITM_NO_DSC = models.FloatField(
        blank=True, null=True, help_text="Order Item No Discount")
    OD_ITM_ODR_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Item Order Id")
    OD_ITM_PRC = models.FloatField(
        blank=True, null=True, help_text="Order Item Price")
    OD_ITM_PRC_INC_TX = models.FloatField(
        blank=True, null=True, help_text="Order Item Price Inclusive Tax")
    OD_ITM_QOT_ITM_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Item Quote Item Id")
    OD_ITM_ROW_INVOICED = models.IntegerField(
        blank=True, null=True, help_text="Order Item Row Invoiced")
    OD_ITM_ROW_TOT = models.FloatField(
        blank=True, null=True, help_text="Order Item Row Total")
    OD_ITM_ROW_TOT_INC_TX = models.FloatField(
        blank=True, null=True, help_text="Order Item Row Total Inclusive Tax")
    OD_ITM_ROW_WGHT = models.FloatField(
        blank=True, null=True, help_text="Order Item Row Weight")
    OD_ITM_SKU = models.CharField(
        max_length=50, blank=True, default='', help_text="Order Item SKU")
    OD_ITM_NET_AMT = models.FloatField(
        blank=True, null=True, help_text="Order Item Net Amount")
    OD_ITM_QTY_PKD = models.IntegerField(
        blank=True, null=True, help_text="Order Item Quantity Picked")

    class Meta:
        db_table = "OD_ITM"


class OrderItemVariation(CommonFeatures):
    OD_ITM_VAR_OD = models.ForeignKey(OrderMaster,
                                      on_delete=models.CASCADE,
                                      blank=True,
                                      null=True, help_text="Order")
    OD_ITM_VAR_ITM = models.ForeignKey(Item,
                                       on_delete=models.CASCADE,
                                       blank=True,
                                       null=True, help_text="Item")
    OD_ITM_VAR_OPT_ID = models.CharField(max_length=10,
                                         default=None,
                                         blank=True,
                                         help_text="Order Item Configurable Option ID")
    OD_ITM_VAR_OPT_VAL = models.IntegerField(blank=True,
                                             null=True,
                                             help_text="Order Item Configurable Option Value")

    class Meta:
        db_table = "OD_ITM_CONF"


class OrderActivity(CommonFeatures):
    '''Order Activity Model'''
    OD_ACT_ID = models.BigAutoField(
        "OrderActivityID", primary_key=True, help_text="Order Activity ID")
    OD_ACT_OD_MA_ID = models.ForeignKey(
        OrderMaster, on_delete=models.CASCADE, blank=True, null=True, help_text="Order Activity Order Master Model Foreign Key")
    OD_ACT_CMT = models.CharField(
        max_length=255, blank=True, default=None, help_text="Order Activity Comment")
    OD_ACT_STATUS = models.CharField(
        max_length=50, blank=True, default=None, help_text="Order Activity Status")
    OD_ACT_ENT_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Activity Entity ID")
    OD_ACT_IS_CUST_NTD = models.IntegerField(
        default=0, blank=True, null=True, help_text="Order Activity Is Customer Notified")
    OD_ACT_IS_VISI_ON_FRT = models.IntegerField(
        default=0, blank=True, null=True, help_text="Order Activity Is Visible On Front")
    OD_ACT_CRT_AT = models.CharField(
        max_length=70, blank=True, default=None, help_text="Order Activity Created At In Magento")
    OD_ACT_CRT_BY = models.CharField(
        max_length=70, blank=True, default=None, help_text="Order Activity Created By")
    OD_CUST = models.ForeignKey(Customer,
                                on_delete=models.CASCADE,
                                blank=True,
                                null=True,
                                help_text="Customer")

    class Meta:
        db_table = "OD_ACT"


class OrderPaymentMethods(CommonFeatures):
    OD_PAY_ID = models.BigAutoField(
        "OrderPaymentMethodID", primary_key=True, help_text="Order Payment Method ID")
    OD_PAY_NM = models.CharField(
        max_length=255, blank=True, default=None, help_text="Order Payment Name")
    OD_PAY_DESC = models.TextField(
        blank=True, default=None, help_text="Order Payment Description")

    class Meta:
        db_table = "OD_PAY_MTHD"


class OrderPaymentDetails(CommonFeatures):
    OD_PAY_DTL_ID = models.BigAutoField(
        "OrderPaymentDetailID", primary_key=True, help_text="Order Payment Detail ID")
    OD_PAY_TRANS_ID = models.IntegerField(
        null=True, blank=True, help_text="Transaction Id")
    OD_PAY_OD = models.ForeignKey(OrderMaster, on_delete=models.CASCADE,
                                  null=True, blank=True, help_text="Order Payment Order ID")
    MAGENTO_OD_PAY_ID = models.IntegerField(
        null=True, blank=True, help_text="Magento Order Payment ID")
    MAGENTO_OD_ID = models.IntegerField(
        null=True, blank=True, help_text="Magento Order ID")
    OD_PAY_TXN_ID = models.CharField(
        max_length=50, blank=True, default=None, help_text="Order Payment TXN ID")
    OD_PAY_PRT_TXN_ID = models.CharField(
        max_length=50, blank=True, default=None, help_text="Order Payment Parent TXN ID")
    OD_PAY_TXN_TYP = models.CharField(
        max_length=50, blank=True, default=None, help_text="Order Payment TXN Type")
    OD_PAY_ADDT_INFO = models.TextField(
        blank=True, default=None, help_text="Order Payment Additional Information")
    OD_PAY_CRT_DT = models.CharField(
        max_length=50, blank=True, default=None, help_text="Order Payment Created Date")
    OD_PAY_MTHD = models.ForeignKey(
        OrderPaymentMethods, on_delete=models.CASCADE,
        blank=True, null=True, help_text="Order Payment Method ID")
    IS_CAPTURED = models.BooleanField(
        blank=True, null=True, default=False, help_text="Check Capture Status")
    ERROR = models.TextField(blank=True, default="",
                             help_text="Captured Error")

    class Meta:
        db_table = "OD_PAY_DTL"


class OrderHoldUnholdPreviousStatus(CommonFeatures):
    '''Order Hold Unhold Status'''
    OD_HD_UD_PRVST_ID = models.BigAutoField(
        "OrderHoldUnholdPreviousStatusId", primary_key=True, help_text="Order Hold Unhold Previous Status ID")
    OD_HD_UH_OD_ID = models.CharField(
        max_length=50, blank=True, default='', help_text=order_id_help_text)
    OD_HD_UH_CRNT_STAT = models.CharField(
        max_length=50, blank=True, default='', help_text="Order Current Status")
    OD_HD_UH_PREV_STAT = models.CharField(
        max_length=50, blank=True, default='', help_text="Order Previous Status")
    OD_OMS_STATUS_PREV = models.CharField(
        max_length=50, blank=True, default='', help_text="Order Oms Status Previous Status")
    OD_OMS_STATUS_CRNT = models.CharField(
        max_length=50, blank=True, default='', help_text="Order Oms Status Current Status")

    class Meta:
        db_table = "OD_HD_UD_STAT"


class ShipmentMaster(CommonFeatures):
    '''Shipment Status'''
    SHP_STS = (
        ("Picking-In Progress", "Picking-In Progress"),
        ("Picking-Completed", "Picking-Completed"),
        ("Shipping- In Progress", "Shipping- In Progress"),
        ("Shipping-Completed", "Shipping-Completed")
    )
    OD_SHP_ID = models.BigAutoField(
        "Order Shipment ID", primary_key=True, help_text="Order Shipment ID")
    OD_SHIP_CODE = models.CharField(
        max_length=50, blank=True, default='', help_text="Shipment Code")
    LOC_ID = models.ForeignKey(Location,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text="Pick up location")
    OD_SHP_TRK_NO = models.IntegerField(
        null=True, blank=True, help_text="Order Shipping Tracking Number")
    OD_SHP_TRK_CMP = models.CharField(
        max_length=100, default='', blank=True, help_text="Order Shipping Tracking Company")
    OD_SHP_ROUT_CODE = models.CharField(
        max_length=100, default='', blank=True, help_text="Order Shipping Routing Code")
    OD_SHP_ACT_QTY = models.CharField(
        max_length=100, default='', blank=True, help_text="Order Shipping Actual Quantity")
    OD_SHP_STS = models.CharField(
        choices=SHP_STS, max_length=100, default='', blank=True, help_text="Order Shipping Status")
    OD_ID = models.ForeignKey(OrderMaster,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              help_text=order_id_help_text)
    OD_CRATE_COUNT = models.IntegerField(null=True,
                                         blank=True,
                                         help_text="Crate Number Count")
    IS_GENERATED = models.BooleanField(default=False)
    TOT_PICK_QTY = models.IntegerField(
        blank=True, null=True, help_text="Total Pick Amount")
    TOT_AMT = models.FloatField(
        blank=True, null=True, help_text="Total Amount")
    TOT_NET_AMT = models.FloatField(
        blank=True, null=True, help_text="Total Net Amount")
    TOT_TAX_AMT = models.FloatField(
        blank=True, null=True, help_text="Total Tax Amount")
    TOT_DIS_AMT = models.FloatField(
        blank=True, null=True, help_text="Total Discount Amount")
    MUL_OD_ID = models.CharField(
        max_length=50, default='', blank=True, help_text="Multiple Order ID")
    MUL_OD_STR_NM = models.CharField(
        max_length=50, default='', blank=True, help_text="Multiple Order store name")

    class Meta:
        db_table = "OD_SHP_MASTER"


class PicklistMaster(CommonFeatures):
    '''Master Picklist Table'''
    OD_PICK_ID = models.BigAutoField(
        "PickList ID", primary_key=True, help_text="PickList ID")
    OD_PICK_NO = models.CharField(
        max_length=50, blank=True, default='', help_text="PickList Number")
    OD_PICK_BY = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   blank=True,
                                   null=True,
                                   help_text="Order Picked By")
    OD_ID = models.ForeignKey(OrderMaster,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              help_text=order_id_help_text)
    OD_SHP_ID = models.ForeignKey(ShipmentMaster,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  null=True,
                                  help_text="Order Shipping")
    OD_PICK_CONFRM = models.BooleanField(
        max_length=15, blank=True, default=False, help_text="Order Picking Status")
    OD_PICK_SUB = models.BooleanField(
        blank=True, null=True, default=False, help_text="Order Sub Picking")
    OD_PICK_TOTAL_AMT = models.FloatField(
        blank=True, null=True, help_text="Total Picking Amount")

    class Meta:
        db_table = "OD_PICK_MASTER"


class ItemPicklist(CommonFeatures):
    '''Item Pick List table'''
    ITM_PICK_ID = models.BigAutoField(
        "Item Picklist ID", primary_key=True, help_text="Item Picklist ID")
    ITM_ID = models.ForeignKey(Item,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text="Item")
    OD_PICK_ID = models.ForeignKey(PicklistMaster,
                                   on_delete=models.SET_NULL,
                                   blank=True,
                                   null=True,
                                   help_text="Order Picklist")
    ID_CD_BR_ITM = models.ForeignKey(ItemBarcode,
                                     on_delete=models.SET_NULL,
                                     blank=True,
                                     null=True,
                                     help_text="Item Barcode")
    ITM_QTY_REQST = models.IntegerField(
        blank=True, null=True, help_text="Item Quantity Request")
    ITM_QTY_PCKD = models.IntegerField(
        blank=True, null=True, help_text="Item Quantity Picked")
    ITM_QTY_SORT = models.IntegerField(
        blank=True, null=True, help_text="Item Quantity Shortage")
    ITM_STK_AVAIL = models.FloatField(
        blank=True, null=True, help_text="Item stock Available")
    ITM_PICK_MRP = models.FloatField(
        blank=True, null=True, help_text="Item MRP when pickup")
    ITM_OR_MRP = models.FloatField(
        blank=True, null=True, help_text="Item MRP when pickup")

    class Meta:
        db_table = "OD_ITM_PICK"


class ItemShipmentList(CommonFeatures):
    ITM_SHP_ID = models.BigAutoField(
        "Item Shipment ID", primary_key=True, help_text="Item Shipment ID")
    ITM_SHP_QTY = models.IntegerField(
        blank=True, null=True, help_text="Shipped Item Quantity")
    ITM_SHP_SORT = models.IntegerField(
        blank=True, null=True, help_text="Shipped Item Quantity Shortage")
    ITM_SHP_RTN_QTY = models.IntegerField(
        blank=True, null=True, help_text="Shipped Item Return Quantity")
    ITM_SHP_GRN_QTY = models.IntegerField(
        blank=True, null=True, help_text="Shipped Item Goods Recieved Note Quantity")
    ITM_SHP_GRN_RTN = models.IntegerField(
        blank=True, null=True, help_text="Shipped Item Goods Recieved Note Return Quantity")
    OD_ID = models.ForeignKey(OrderMaster,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              help_text="Order id")
    OD_ITM_ID = models.ForeignKey(OrderItemDetails,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  null=True,
                                  help_text=order_item_help_text)
    ITM_ID = models.ForeignKey(Item,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text="Item ID")
    OD_PICK_ID = models.ForeignKey(PicklistMaster,
                                   on_delete=models.SET_NULL,
                                   blank=True,
                                   null=True,
                                   help_text="Order Picking ID")
    OD_SHP_ID = models.ForeignKey(ShipmentMaster,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  null=True,
                                  help_text="Order Shipping ID")
    ID_CD_BR_ITM = models.ForeignKey(ItemBarcode,
                                     on_delete=models.SET_NULL,
                                     blank=True,
                                     null=True,
                                     help_text="Item Barcode")

    class Meta:
        db_table = "ITM_SHP_LIST"


class OrderInvoice(CommonFeatures):
    '''Order Activity Model'''
    OD_INVOE_ID = models.BigAutoField(
        "OrderInvoiceID", primary_key=True, help_text=invoice_id_help_text)
    OD_INVOE_OD_ID = models.ForeignKey(
        OrderMaster, on_delete=models.CASCADE, blank=True, null=True, help_text="Order Invoice Order ID")
    OD_INVOE_INCR_ID = models.CharField(
        max_length=50, blank=True, default=None, help_text="Order Invoice Increment ID")
    OD_INVOE_ENT_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice Entity ID")
    OD_INVOE_GRND_TOT = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice Grand Total")
    OD_INVOE_SHIP_AMT = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice Shipment_Amount")
    OD_INVOE_SHIP_INCL_TAX = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice Shipment Incl Tax")
    OD_INVOE_CRT_AT = models.CharField(
        max_length=70, blank=True, default=None, help_text="Order Invoice Created At In Magento")
    OD_INVOE_UPDT_AT = models.CharField(
        max_length=70, blank=True, default=None, help_text="Order Invoice Updated At In Magento")
    OD_INVOE_STATE_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice State ID")
    OD_INVOE_STR_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice Store ID")
    OD_INVOE_BILL_ADD_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice Billing Address ID")
    OD_INVOE_SHIP_ADD_ID = models.IntegerField(
        blank=True, null=True, help_text="Order Invoice Shipping ADDRESS ID")
    OD_SHP_ID = models.ForeignKey(
        ShipmentMaster, on_delete=models.CASCADE, blank=True, null=True, help_text="Order Shipping ID")
    ITM_PICK_ID = models.ForeignKey(
        PicklistMaster, on_delete=models.CASCADE, blank=True, null=True, help_text="Order Picking ID")

    class Meta:
        db_table = "OD_INVOE"


class OrderInvoicePicklistType(CommonFeatures):
    '''Order Invoice and Picklist Type'''
    OD_INV_PICK_ID = models.BigAutoField(
        "OrderInvoicePicklistID", primary_key=True, help_text="Order Invoice Picklist ID")
    OD_INV_PICK_NM = models.CharField(
        max_length=15, blank=True, default='', help_text="Order Invoice Picklist Type Name")

    class Meta:
        db_table = "OD_INV_PK TP"


class OrderInvoiceTemplate(CommonFeatures):
    '''Order Invoice Template'''
    OD_INVOE_TEMP_ID = models.BigAutoField(
        "OrderInvoiceTemplateID", primary_key=True, help_text="Order Invoice Template ID")
    OD_INVOE_TEMP_FILE = models.TextField(
        blank=True, default=None, help_text="Order Invoice Created At In Magento")
    OD_INVOE_ID = models.ForeignKey(
        OrderInvoice, on_delete=models.CASCADE, blank=True, null=True, help_text=invoice_id_help_text)
    OD_INV_PICK_ID = models.ForeignKey(
        OrderInvoicePicklistType, on_delete=models.CASCADE, blank=True, null=True, help_text="Order Invoice Picklist Type ID")

    class Meta:
        db_table = "OD_INVOE_TEMP"


class Crates(CommonFeatures):
    '''
    create management fields -
    crate code (unique) - mandatory
    barcode (unique) - mandatory
    store assigned - mandatory
    material type - (plastic,fibre,steel,wooden)
    colour - ForeignKey(Color)
    Status - Enable or Disable
    Description - Optional
    '''
    CRT_ID = models.BigAutoField(
        "CRATES ID", primary_key=True, help_text="Crates ID")
    CRT_CD = models.CharField(max_length=100,
                              default="", unique=True, help_text="Crate Code")
    BR_CD = models.CharField(max_length=100,
                             default="", unique=True, help_text="Crate Barcode")
    DES = models.CharField(max_length=255,
                           default="", blank=True, help_text="Crate Description")
    MATERIAL_TYPE_CHOICES = [
        ('plastic', 'Plastic'),
        ('fibre', 'Fibre'),
        ('steel', 'Steel'),
        ('wooden', 'Wooden'),
    ]
    STATUS_TYPE_CHOICES = (
        ("A", "Active"),
        ("I", "Inactive")
    )
    MTRL_TYPE = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES,
                                 blank=True, help_text="Material Type")

    CLRS = models.ForeignKey(Color,
                             on_delete=models.SET_NULL,
                             blank=True,
                             null=True,
                             help_text="Crate Color ID")
    CRT_STS = models.CharField(max_length=20, default="Active", choices=STATUS_TYPE_CHOICES,
                               blank=True, help_text="Status")
    CRT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               blank=True, null=True, related_name='Crate_Createuser', db_column="CRT_BY")
    UPDT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                blank=True, null=True, related_name='Crate_Modifiyuser', db_column="UPDT_BY")

    class Meta:
        db_table = "CRT_TBL"


class AssociateCrate(CommonFeatures):

    AC_ID = models.BigAutoField(
        "AssociateCrate ID", primary_key=True, help_text="AssociateCrate ID")
    CRT_ID = models.ForeignKey(Crates,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text="Crate ID")
    STR_ID = models.ForeignKey(Location,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text=store_id_key)

    class Meta:
        db_table = "AS_CRATE_TBL"


class OrderCrates(CommonFeatures):
    CRATE_ID = models.BigAutoField(
        "CRATES ID", primary_key=True, help_text="Crates ID")
    OD_ID = models.ForeignKey(OrderMaster,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              help_text="Crate Order id")
    OD_SHP_ID = models.ForeignKey(ShipmentMaster,
                                  on_delete=models.SET_NULL,
                                  blank=True,
                                  null=True,
                                  help_text="Crate Order Shipping ID")
    OD_PICK_ID = models.ForeignKey(PicklistMaster,
                                   on_delete=models.SET_NULL,
                                   blank=True,
                                   null=True,
                                   help_text="Crate Order Picking ID")
    AC_ID = models.ForeignKey(AssociateCrate, on_delete=models.SET_NULL,
                              blank=True, null=True, help_text="Associate crate module")

    class Meta:
        db_table = "CRATE_TBL"


class Reason(CommonFeatures):
    STATUS_TYPE_CHOICES = (
        ("A", "Active"),
        ("I", "Inactive")
    )
    RN_ID = models.BigAutoField(
        "REASON ID", primary_key=True, help_text="REASON ID")
    RN_CD = models.CharField(max_length=100,
                             default="", unique=True, help_text="Reason Code")
    RN_STD = models.CharField(
        max_length=500, blank=True, help_text="Reason Statement")
    IS_VISIBLE = models.BooleanField(default=True)
    RN_STS = models.CharField(max_length=20, choices=STATUS_TYPE_CHOICES,
                              blank=True, help_text="Reason Status")
    CRT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               blank=True, null=True, related_name='Reason_Createuser', db_column="CRT_BY")
    UPDT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                blank=True, null=True, related_name='Reason_Modifiyuser', db_column="UPDT_BY")

    class Meta:
        db_table = "RSN_TBL"


class OrderItemInvoince(CommonFeatures):
    OD_INVC_ITM_ID = models.BigAutoField(
        "ORDER INVOICE ITEM ID", primary_key=True, help_text="Order Invoice Item ID")
    OD_INVC_ID = models.ForeignKey(OrderInvoice,
                                   on_delete=models.CASCADE,
                                   blank=True,
                                   null=True,
                                   help_text=invoice_id_help_text)
    OD_ID = models.ForeignKey(
        OrderMaster, on_delete=models.CASCADE, blank=True, null=True, help_text="Order ID")
    AS_ITM = models.ForeignKey(
        Item, on_delete=models.CASCADE, blank=True, null=True, help_text="Item ID")
    OD_ITM_ID = models.ForeignKey(
        OrderItemDetails, on_delete=models.CASCADE, blank=True, null=True, help_text=order_item_help_text)
    OD_ITM_INVC_PR = models.FloatField(
        blank=True, null=True, help_text="Order Item Invoice Price")

    class Meta:
        db_table = 'OD_ITM_INVC_TBL'


class PicksheetNote(CommonFeatures):
    STATUS_TYPE_CHOICES = (
        ("A", "Active"),
        ("I", "Inactive")
    )
    PSN_ID = models.BigAutoField(
        "PICKSHEET ID", primary_key=True, help_text="Picksheet Note ID")
    PSN_NM = models.CharField(max_length=100,
                              default="", unique=True, help_text="Picksheet Note Name")

    PSN_STS = models.CharField(max_length=20, choices=STATUS_TYPE_CHOICES,
                               blank=True, help_text="Picksheet Note Status")
    ST_DT = models.DateField("StartDate", blank=True, null=True)
    EN_DT = models.DateField("EndDate", blank=True, null=True)

    PSN_VIS = models.CharField(max_length=100,
                               default="", help_text="Picksheet Note Visibility")
    NT_DETAILS = models.TextField(
        blank=True, default=None, help_text="Note Details")
    CRT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               blank=True, null=True, related_name='Picksheet_Createuser', db_column="CRT_BY")
    UPDT_BY = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                blank=True, null=True, related_name='Picksheet_Modifiyuser', db_column="UPDT_BY")

    class Meta:
        db_table = 'PSN_TBL'


class PicksheetNoteStores(CommonFeatures):
    AC_PSN_ID = models.BigAutoField(
        "ASSOCIATE PICKSHEET ID", primary_key=True, help_text="Associate PicksheetNote ID")
    PSN_ID = models.ForeignKey(PicksheetNote,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text="PickSheetNote id")
    STR_ID = models.ForeignKey(Location,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text=store_id_key)

    class Meta:
        db_table = 'PSN_STR_TBL'


class PicksheetNoteItemSKU(CommonFeatures):
    AC_PSN_ID = models.BigAutoField(
        "ASSOCIATEPICKSHEET ID", primary_key=True, help_text="PickSheetNote ID")
    PSN_ID = models.ForeignKey(PicksheetNote,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True,
                               help_text="Picksheet Note ID")
    ITM_SKU_ID = models.ForeignKey(Item,
                                   on_delete=models.SET_NULL,
                                   blank=True,
                                   null=True,
                                   help_text="Product Item SKU ID"
                                   )

    class Meta:
        db_table = 'PSN_SKU_TBL'
