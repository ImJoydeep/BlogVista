
from datetime import datetime
from order.models import OrderBillingAddress, OrderItemDetails, OrderShippingAddress


def generate_invoice(order_id, invoice_id):
    '''Generate invoice'''
    billing_instance = OrderBillingAddress.objects.filter(
        OD_BA_OD_ID=order_id.OD_ID).first()
    shipping_instance = OrderShippingAddress.objects.filter(
        OD_SA_OD_ID=order_id.OD_ID).first()
    billing_country_name = billing_instance.OD_BA_CTR_CODE
    if str(billing_instance.OD_BA_CTR_CODE).lower() == 'us':
        billing_country_name = 'United States'
    shipping_country_name = shipping_instance.OD_SA_CTR_CODE
    if str(shipping_instance.OD_SA_CTR_CODE).lower() == 'us':
        shipping_country_name = 'United States'
    if order_id.PT_MD_NM == 'checkmo':
        payment_method = "Check / Money order"
    else:
        payment_method = "Credit Card (Authorize.Net CIM)"
    order_date = order_id.OD_DATE[:10]
    date_obj = datetime.strptime(order_date, "%Y-%m-%d")

    formatted_date = date_obj.strftime("%b %d, %Y")
    html_content = """<!DOCTYPE html
        PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">

    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>file_1695901448428</title>
        <style type="text/css">
            * {
                margin: 0;
                padding: 0;
                text-indent: 0;
            }

            .s1 {
                color: #FFF;
                font-family: "Times New Roman", serif;
                font-style: normal;
                font-weight: normal;
                text-decoration: none;
                font-size: 10pt;
            }

            .s2 {
                color: black;
                font-family: "Times New Roman", serif;
                font-style: normal;
                font-weight: bold;
                text-decoration: none;
                font-size: 12pt;
            }

            .s3 {
                color: black;
                font-family: "Times New Roman", serif;
                font-style: normal;
                font-weight: normal;
                text-decoration: none;
                font-size: 10pt;
            }

            .s4 {
                color: black;
                font-family: "Times New Roman", serif;
                font-style: normal;
                font-weight: bold;
                text-decoration: none;
                font-size: 10pt;
            }

            table,
            tbody {
                vertical-align: top;
                overflow: visible;
            }
        </style>
    </head>

    <body>"""
    html_content += f"""
        <table style="border-collapse:collapse;margin-left:6pt" cellspacing="0">
            <tr style="height:55pt">
                <td style="width:545pt;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F"
                    colspan="2" bgcolor="#727272">
                    <p class="s1" style="padding-top: 5pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">Invoice #
                        {str(invoice_id)}</p>
                    <p class="s1" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">Order #
                        {str(order_id.CU_OD_ID)}</p>
                    <p class="s1" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">Order Date:
                        {str(formatted_date)}</p>
                </td>
            </tr>
            <tr style="height:25pt">
                <td style="width:250pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-left-style:solid;border-left-width:1pt;border-left-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;border-right-style:solid;border-right-width:1pt;border-right-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s2" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">Sold to:
                    </p>
                </td>
                <td style="width:295pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-left-style:solid;border-left-width:1pt;border-left-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;border-right-style:solid;border-right-width:1pt;border-right-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s2" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">Ship to:
                    </p>
                </td>
            </tr>
            <tr style="height:83pt">
                <td style="border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-left-style:solid;border-left-width:1pt;border-left-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;"
                    colspan="1">
                    <p class="s3" style="padding-top: 5pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(billing_instance.OD_BA_FN)} {str(billing_instance.OD_BA_LN)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(billing_instance.OD_BA_ST)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(billing_instance.OD_BA_CT)}, {str(billing_instance.OD_BA_RGN)}, {str(billing_instance.OD_BA_PIN)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(billing_country_name)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">T:
                        {str(billing_instance.OD_BA_PH)}</p>
                </td>
                <td style="border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;border-right-style:solid;border-right-width:1pt;border-right-color:#7F7F7F"
                    colspan="1">
                    <p class="s3" style="padding-top: 5pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(shipping_instance.OD_SA_FN)} {str(shipping_instance.OD_SA_LN)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(shipping_instance.OD_SA_ST)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(shipping_instance.OD_SA_CT)}, {str(shipping_instance.OD_SA_RGN)}, {str(shipping_instance.OD_SA_PIN)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(shipping_country_name)}</p>
                    <p class="s3" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">T:
                        {str(shipping_instance.OD_SA_PH)}</p>
                </td>
            </tr>
        </table>
        <p style="text-indent: 0pt;text-align: left;"><br /></p>
        <table style="border-collapse:collapse;margin-left:6pt" cellspacing="0">
            <tr style="height:25pt">
                <td style="width:250pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-left-style:solid;border-left-width:1pt;border-left-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;border-right-style:solid;border-right-width:1pt;border-right-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s2" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">Payment
                        Method:</p>
                </td>
                <td style="width:295pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-left-style:solid;border-left-width:1pt;border-left-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;border-right-style:solid;border-right-width:1pt;border-right-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s2" style="padding-top: 3pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">Shipping
                        Method:</p>
                </td>
            </tr>
            <tr style="height:65pt">
                <td style="border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-left-style:solid;border-left-width:1pt;border-left-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;"
                    colspan="1">
                    <p class="s3" style="padding-top: 5pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(payment_method)}</p>
                    <p style="text-indent: 0pt;text-align: left;"><br /></p>
                </td>
                <td style="border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;border-right-style:solid;border-right-width:1pt;border-right-color:#7F7F7F"
                    colspan="1">
                    <p class="s3" style="padding-top: 5pt;padding-left: 10pt;text-indent: 0pt;text-align: left;">{str(order_id.OD_SHIP_DESC)}</p>
                    <p style="text-indent: 0pt;text-align: left;"><br /></p>
                    <p class="s3" style="text-indent: 0pt;text-align: left;">(Total Shipping Charges
                        ${str(order_id.OD_SHP_AMT)})</p>
                </td>
            </tr>
        </table>
        <p style="text-indent: 0pt;text-align: left;"><br /></p>
        <table style="border-collapse:collapse;margin-left:6pt;width:100%;max-width:730px;" cellspacing="0">
            <tr style="height:15pt">
                <td style="width:145pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-left-style:solid;border-left-width:1pt;border-left-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s3" style="padding-left: 10pt;text-indent: 0pt;text-align: left;padding-top: 2px;">Products</p>
                </td>
                <td style="width:145pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s3" style="text-indent: 0pt;text-align: center;padding-top: 2px;">SKU</p>
                </td>
                <td style="width:49pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s3" style="text-indent: 0pt;text-align: center;padding-top: 2px;">Price</p>
                </td>
                <!-- <td style="width:44pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p style="text-indent: 0pt;text-align: left;"><br /></p>
                </td> -->
                <td style="width:46pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s3" style="text-indent: 0pt;text-align: center;padding-top: 2px;">Qty</p>
                </td>
                <td style="width:60pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s3" style="text-indent: 0pt;text-align: center;padding-top: 2px;">Discount</p>
                </td>
                <td style="width:56pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;border-bottom-style:solid;border-bottom-width:1pt;border-bottom-color:#7F7F7F;border-right-style:solid;border-right-width:1pt;border-right-color:#7F7F7F"
                    bgcolor="#EDEAEA">
                    <p class="s3" style="padding-right:10px;text-indent: 0pt;text-align: center;padding-top: 2px;">Subtotal</p>
                </td>
            </tr>"""
    for od_id in OrderItemDetails.objects.filter(OD_ID=order_id.OD_ID):
        html_content += f"""<tr style="height:42pt">
            <td style="width:145pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;padding-top: 10px;">
               
                <p class="s3" style="padding-left: 10pt;text-indent: 0pt;text-align: left;">{od_id.OD_ITM_NM}</p>
            </td>
            <td style="width:145pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;padding-top: 10px;">
              
                <p class="s3" style="padding-left: 40pt;text-indent: 0pt;text-align: left;">{od_id.OD_ITM_SKU}</p>
            </td>
          
            <td style="width:44pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;padding-top: 10px;">
                
                <p class="s4" style="text-indent: 0pt;text-align: center;">${od_id.OD_ITM_OR_PR}</p>
            </td>
            <td style="width:46pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;padding-top: 10px;">
               
                <p class="s3" style="text-indent: 0pt;text-align: center;">{od_id.OD_ITM_QTY_PKD if od_id.OD_ITM_QTY_PKD else 0}</p>
            </td>
            <td style="width:60pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;padding-top: 10px;">
               
                <p class="s4" style="text-indent: 0pt;text-align: center;">${od_id.OD_ITM_DSC_AMT}</p>
            </td>
            <td style="width:56pt;border-top-style:solid;border-top-width:1pt;border-top-color:#7F7F7F;padding-top: 10px;">
               
                <p class="s4" style="padding-right:10px;text-indent: 0pt;text-align: center;">${od_id.OD_ITM_NET_AMT}</p>
            </td>
        </tr>"""
    html_content += f"""</table>
        <p style="text-indent: 0pt;text-align: left;"><br /></p>
        <p style="text-indent: 0pt;text-align: left;"><br /></p>
        <table style="border-collapse:collapse;margin-left:358.06pt" cellspacing="0">
            <tr style="height:13pt">
                <td style="width:129pt">
                    <p class="s4" style="padding-right: 31pt;text-indent: 0pt;line-height: 11pt;text-align: right;">
                        Subtotal:</p>
                </td>
                <td style="width:61pt">
                    <p class="s4" style="padding-right: 15px;text-indent: 0pt;line-height: 11pt;text-align: right;">${str(order_id.OD_NT_AMT)}
                    </p>
                </td>
            </tr>
            <tr style="height:15pt">
                <td style="width:129pt">
                    <p class="s4" style="padding-top: 1pt;padding-right: 31pt;text-indent: 0pt;text-align: right;">Discount (-)
:</p>
                </td>
                <td style="width:61pt">
                    <p class="s4" style="padding-top: 1pt;padding-right: 15px;text-indent: 0pt;text-align: right;">${str(order_id.OD_DIS_AMT)}</p>
                </td>
            </tr>
            <tr style="height:15pt">
                <td style="width:129pt">
                    <p class="s4" style="padding-top: 1pt;padding-right: 31pt;text-indent: 0pt;text-align: right;">Shipping
                        &amp; Handling:</p>
                </td>
                <td style="width:61pt">
                    <p class="s4" style="padding-top: 1pt;padding-right: 15px;text-indent: 0pt;text-align: right;">${str(order_id.OD_SHP_AMT)}</p>
                </td>
            </tr>
            <tr style="height:13pt">
                <td style="width:129pt">
                    <p class="s4"
                        style="padding-top: 1pt;padding-right: 31pt;text-indent: 0pt;line-height: 10pt;text-align: right;">
                        Grand Total:</p>
                </td>
                <td style="width:61pt">
                    <p class="s4"
                        style="padding-top: 1pt;padding-right: 15px;text-indent: 0pt;line-height: 10pt;text-align: right;">
                        ${str(order_id.OD_TL_AMT)}</p>
                </td>
            </tr>
        </table>
    </body>"""
    return html_content
