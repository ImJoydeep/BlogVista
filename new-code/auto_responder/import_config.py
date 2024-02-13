from dotenv import load_dotenv
import os

from auto_responder.models import EmailAction, EmailTemplate, EmailDepartmentMapping, TemplateWarehouseMapping,\
TemplateActionMapping
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.html import strip_tags
from order.models import OrderMaster, OrderItemDetails
from department.models import Department
from party.models import EmailAddress, PartyContactMethod
from accesscontrol.models import Operator, WorkerOperatorAssignment
from position.models import WorkerPositionAssignment, Position
from store.models import SiteContactMethod, Location
from django.template.loader import render_to_string
from django.db.models import Value as V
from django.db.models.functions import Concat, Coalesce
import logging
import re
logger = logging.getLogger(__name__)
load_dotenv()