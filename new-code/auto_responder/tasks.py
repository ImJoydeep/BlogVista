from celery import shared_task
from django.core import management
from auto_responder.models import EmailAction, EmailTemplate
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.utils.html import strip_tags
from order.models import OrderMaster
from django.template.loader import render_to_string
from django.template import Template, Context
import logging
logger = logging.getLogger(__name__)

@shared_task
def send_scheduled_email():
    management.call_command("send_reminder_email")






