import json
import logging
import ast
import requests
from django.conf import settings
from order.models import OrderMaster, OrderPaymentDetails

logger = logging.getLogger(__name__)

def capture_payment(order_id):
    ''' Capture Customer Payment '''
    try:
        res = {}
        authorize_uri = settings.AUTHORIZE_ENDPOINT
        order_details = OrderMaster.objects.filter(CU_OD_ID__iexact=order_id).first()
        order_payment_info = OrderPaymentDetails.objects.filter(
            OD_PAY_OD__CU_OD_ID=order_id).first()
        if order_payment_info:
            data_list = ast.literal_eval(order_payment_info.OD_PAY_ADDT_INFO)
            order_payment_json = json.loads(data_list[0])
            headers = {
                'Content-Type': 'application/json'
                }
            payment_capture_json = {
                "createTransactionRequest": {
                    "merchantAuthentication": {
                        "name": settings.APILOGINID,
                        "transactionKey": settings.TRANSACTIONKEY
                    },
                    "refId": order_payment_json.get('transaction_id'),
                    "transactionRequest": {
                        "transactionType": "priorAuthCaptureTransaction",
                        "amount": str(order_payment_json.get('amount')),
                        "refTransId": order_payment_json.get('transaction_id')
                    }
                }
            }
            payload = json.dumps(payment_capture_json)
            response = requests.post(authorize_uri, headers=headers, data=payload)

            if response.status_code == 200:
                data = response.text.encode('utf-8').decode('utf-8-sig')
                data = json.loads(data)
                if data.get('messages').get('resultCode') == 'Ok':
                    order_payment_info.IS_CAPTURED = True
                    order_payment_info.ERROR = data
                    order_payment_info.save()
                    order_details.OD_PD_AMT = float(int(order_payment_json.get('amount')))
                    order_details.save()
                    res["message"] = "Payment Captured Successfully."
                    res["status"] = True
                else:
                    order_payment_info.ERROR = response.text
                    order_payment_info.save()
                    res["message"] = "Payment failure, Complete Picking cannot be Done."
                    res["status"] = False 
        else:
            res["message"] = "Its a Offline Transaction."
            res["status"] = False
        return res
    except Exception:
        logger.info(f"payment-failed due to -{Exception}")


def refund_payment(order_id):
    authorize_uri = settings.AUTHORIZE_ENDPOINT
    order_payment_info = OrderPaymentDetails.objects.filter(
        OD_PAY_OD__CU_OD_ID=order_id).first()
    if order_payment_info:
        data_list = ast.literal_eval(order_payment_info.OD_PAY_ADDT_INFO)
        order_payment_json = json.loads(data_list[0])
        headers = {
            'Content-Type': 'application/json'
            }
        refund_payment = {
            "createTransactionRequest": {
                "merchantAuthentication": {
                    "name": settings.APILOGINID,
                    "transactionKey": settings.TRANSACTIONKEY
                    },
                "refId": order_payment_json.get('transaction_id'),
                "transactionRequest": {
                    "transactionType": "refundTransaction",
                    "amount": str(order_payment_json.get('amount')),
                    "payment": {
                        "creditCard": {
                            "cardNumber": order_payment_json.get("acc_number")[4:],
                            "expirationDate": "XXXX"
                            }
                        },
                        "refTransId": order_payment_json.get('transaction_id')
                    }
                }
            }
        payload = json.dumps(refund_payment)
        response = requests.post(authorize_uri, headers=headers, data=payload)
        if response.status_code == 200:
            data = response.text.encode('utf-8').decode('utf-8-sig')
            data = json.loads(data)
            if data.get('messages').get('resultCode') == 'Ok':
                order_payment_info.ERROR = data
                order_payment_info.save()
                logger.info(f"Refund: {response.text}")
            else:
                logger.info(f"Error in Refund: {response.text}")