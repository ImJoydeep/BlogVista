from django.urls import path, include
from .views import EmailTemplateStatusUpdate, EmailTemplateSettingCreate, EmailTemplateSettingRetrieveUpdate, \
    EmailTemplateDeleteMultipleView, EmailFiledTypeList,CategoryListView, TemplateActionView, StoreListView, \
    DeliveryChannelListView


urlpatterns = [
    path('template/', EmailTemplateSettingCreate.as_view(), name="auto_responder_create"),
    path("template/<int:templateId>/", EmailTemplateSettingRetrieveUpdate.as_view(), name="auto_responder_status_edit"),
    path("template/status_update/", EmailTemplateStatusUpdate.as_view(), name="auto_responder_status_update"),
    path('template/delete/',
         EmailTemplateDeleteMultipleView.as_view(), name='auto_responder_multipledelete'),
    path('template/field_type', EmailFiledTypeList.as_view(), name="auto_responder_field_list"),
    path('template/category_list', CategoryListView.as_view(), name="auto_responder_category"),
    path("template/action_type", TemplateActionView.as_view(), name="action_type"),
    path('template/store_list', StoreListView.as_view(), name="auto_responder_store"),
    path('template/delivery_channel_list', DeliveryChannelListView.as_view(), name="delivery_channel"),
]