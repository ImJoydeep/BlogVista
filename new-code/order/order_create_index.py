from dnbadmin.elastic_conf import es


def mapping_for_order_index(index_name):
    '''Mapping for order index'''
    request_body = {
        "mappings": {
            "properties": {
                "all_data": {
                    "properties": {
                        "CRT_DT": {
                            "type": "date"
                        },
                        "CU_OD_ID": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "IS_GUST": {
                            "type": "boolean"
                        },
                        "CH_OD_ID": {
                            "type": "long"
                        },
                        "OD_BA_CT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "IS_MAIL": {
                            "type": "long"
                        },
                        "IS_VERIFIED": {
                            "type": "boolean"
                        },
                        "OD_BA_ST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_PIN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_CUST": {
                            "type": "long"
                        },
                        "OD_CUR_COD": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_CUS_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_CUS_EMAIL": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_DATE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ID": {
                            "type": "long"
                        },
                        "OD_DIS_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OD_INVC_NUM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_INST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_AMT_REF": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OD_NT_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OD_IP_ADDR": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PAY_STS": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PD_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OD_PROT_ID": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_QTY": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OD_SA_CT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_RQD_DT": {
                            "type": "date"
                        },
                        "OD_SA_PIN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_PH": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SHIP_DESC": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_ST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SHP_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OD_STR_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SHP_NUM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_STS": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_TL_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OD_TX_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            },
                            "fielddata": True
                        },
                        "OMS_OD_STS": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_TYPE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "PT_MD_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "is_blocked": {
                            "type": "boolean"
                        },
                        "STR_ID": {
                            "type": "long"
                        },
                        "UPDT_DT": {
                            "type": "date"
                        },
                        "is_deleted": {
                            "type": "boolean"
                        },
                        "PREV_STATE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        }
                    }
                },
                "billing_address": {
                    "properties": {
                        "CRT_DT": {
                            "type": "date"
                        },
                        "OD_BA_CT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_CTR_CODE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_EMAIL": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_FN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_LN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_MN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_OD_ID": {
                            "type": "long"
                        },
                        "OD_BA_PH": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_PIN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_RGN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_RGN_CODE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_RGN_ID": {
                            "type": "long"
                        },
                        "OD_BA_ST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ENT_ID": {
                            "type": "long"
                        },
                        "OD_PRT_ID": {
                            "type": "long"
                        },
                        "UPDT_DT": {
                            "type": "date"
                        },
                        "id": {
                            "type": "long"
                        },
                        "is_blocked": {
                            "type": "boolean"
                        },
                        "is_deleted": {
                            "type": "boolean"
                        }
                    }
                },
                "item_details": {
                    "properties": {
                        "AS_ITM_SLUG": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "CRT_DT": {
                            "type": "date"
                        },
                        "ITM_MDF_PRT_NO": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "ITM_VDR_PRT_NO": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "MMS_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ID": {
                            "type": "long"
                        },
                        "OD_ITM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_AMT_REF": {
                            "type": "float"
                        },
                        "OD_ITM_BS_PR": {
                            "type": "float"
                        },
                        "OD_ITM_CL_QTY": {
                            "type": "float"
                        },
                        "OD_ITM_CRT_DT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_DSC_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_DSC_INVC": {
                            "type": "float"
                        },
                        "OD_ITM_DSC_PER": {
                            "type": "float"
                        },
                        "OD_ITM_DSC_TX_CMPSATN_AMT": {
                            "type": "float"
                        },
                        "OD_ITM_FRE_SHP": {
                            "type": "boolean"
                        },
                        "OD_ITM_ID": {
                            "type": "long"
                        },
                        "OD_ITM_ID_ITM": {
                            "type": "long"
                        },
                        "OD_ITM_INVC": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_INVC_QTY": {
                            "type": "float"
                        },
                        "OD_ITM_IS_QTY_DCML": {
                            "type": "boolean"
                        },
                        "OD_ITM_IS_VRTL": {
                            "type": "boolean"
                        },
                        "OD_ITM_NET_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_NO_DSC": {
                            "type": "float"
                        },
                        "OD_ITM_ODR_ID": {
                            "type": "long"
                        },
                        "OD_ITM_OR_PR": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_PRC": {
                            "type": "float"
                        },
                        "OD_ITM_PRC_INC_TX": {
                            "type": "float"
                        },
                        "OD_ITM_QOT_ITM_ID": {
                            "type": "long"
                        },
                        "OD_ITM_QTY": {
                            "type": "float"
                        },
                        "OD_ITM_RETN_QTY": {
                            "type": "float"
                        },
                        "OD_ITM_RFND_QTY": {
                            "type": "float"
                        },
                        "OD_ITM_ROW_INVOICED": {
                            "type": "long"
                        },
                        "OD_ITM_ROW_TOT": {
                            "type": "float"
                        },
                        "OD_ITM_ROW_TOT_INC_TX": {
                            "type": "float"
                        },
                        "OD_ITM_ROW_WGHT": {
                            "type": "float"
                        },
                        "OD_ITM_SHP_QTY": {
                            "type": "float"
                        },
                        "OD_ITM_SKU": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_TAX_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_TAX_CL_AMT": {
                            "type": "float"
                        },
                        "OD_ITM_TAX_INVC_AMT": {
                            "type": "float"
                        },
                        "OD_ITM_TAX_PER": {
                            "type": "float"
                        },
                        "OD_ITM_TOTL_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_UPDT_DT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "UPDT_DT": {
                            "type": "date"
                        },
                        "is_blocked": {
                            "type": "boolean"
                        },
                        "is_deleted": {
                            "type": "boolean"
                        }
                    }
                },
                "order_activity": {
                    "properties": {
                        "OD_ACT_CMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ACT_CRT_AT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ACT_CRT_BY": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ACT_STATUS": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        }
                    }
                },
                "order_details": {
                    "properties": {
                        "CH_OD_ID": {
                            "type": "long"
                        },
                        "CRT_DT": {
                            "type": "date"
                        },
                        "CU_OD_ID": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "IS_GUST": {
                            "type": "boolean"
                        },
                        "IS_MAIL": {
                            "type": "long"
                        },
                        "IS_VERIFIED": {
                            "type": "boolean"
                        },
                        "OD_BA_CT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_PIN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_BA_ST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_CUR_COD": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_CUST": {
                            "type": "long"
                        },
                        "OD_CUS_EMAIL": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_CUS_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_DATE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_DIS_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ID": {
                            "type": "long"
                        },
                        "OD_INST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_INVC_NUM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_IP_ADDR": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_ITM_AMT_REF": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_NT_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PAY_STS": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PD_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PROT_ID": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_QTY": {
                            "type": "long"
                        },
                        "OD_RQD_DT": {
                            "type": "date"
                        },
                        "OD_SA_CT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_PH": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_PIN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_ST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SHIP_DESC": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SHP_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SHP_NUM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_STR_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_STS": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_TL_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_TX_AMT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OMS_OD_STS": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_TYPE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "PREV_STATE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "PT_MD_NM": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "UPDT_DT": {
                            "type": "date"
                        },
                        "is_blocked": {
                            "type": "boolean"
                        },
                        "STR_ID": {
                            "type": "long"
                        },
                        "is_deleted": {
                            "type": "boolean"
                        }
                    }
                },
                "shipping_address": {
                    "properties": {
                        "CRT_DT": {
                            "type": "date"
                        },
                        "OD_ENT_ID": {
                            "type": "long"
                        },
                        "OD_PRT_ID": {
                            "type": "long"
                        },
                        "OD_SA_CT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_CTR_CODE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_CUS_ADD_ID": {
                            "type": "long"
                        },
                        "OD_SA_EMAIL": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_FN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_LN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_MN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_OD_ID": {
                            "type": "long"
                        },
                        "OD_SA_PH": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_PIN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_RGN": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_RGN_CODE": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_SA_RGN_ID": {
                            "type": "long"
                        },
                        "OD_SA_ST": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "UPDT_DT": {
                            "type": "date"
                        },
                        "id": {
                            "type": "long"
                        },
                        "is_blocked": {
                            "type": "boolean"
                        },
                        "is_deleted": {
                            "type": "boolean"
                        }
                    }
                },
                "transaction_detail": {
                    "properties": {
                        "CRT_DT": {
                            "type": "date"
                        },
                        "MAGENTO_OD_ID": {
                            "type": "long"
                        },
                        "MAGENTO_OD_PAY_ID": {
                            "type": "long"
                        },
                        "OD_PAY_ADDT_INFO": {
                            "properties": {
                                "acc_number": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "amount": {
                                    "type": "long"
                                },
                                "approval_code": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "auth_code": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "avs_result_code": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "balance_on_card": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "card_code_response_code": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "card_type": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "cavv_response_code": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "customer_id": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "description": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "invoice_number": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "is_error": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "is_fraud": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "method": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "payment_id": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "profile_id": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "reference_transaction_id": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "requested_amount": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "response_code": {
                                    "type": "long"
                                },
                                "response_reason_code": {
                                    "type": "long"
                                },
                                "response_reason_text": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "response_subcode": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "split_tender_id": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "transaction_id": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                },
                                "transaction_type": {
                                    "type": "text",
                                    "fields": {
                                        "keyword": {
                                            "type": "keyword",
                                            "ignore_above": 256
                                        }
                                    }
                                }
                            }
                        },
                        "OD_PAY_CRT_DT": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PAY_DTL_ID": {
                            "type": "long"
                        },
                        "OD_PAY_OD": {
                            "type": "long"
                        },
                        "OD_PAY_PRT_TXN_ID": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PAY_TRANS_ID": {
                            "type": "long"
                        },
                        "OD_PAY_TXN_ID": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "OD_PAY_TXN_TYP": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "UPDT_DT": {
                            "type": "date"
                        },
                        "is_blocked": {
                            "type": "boolean"
                        },
                        "is_deleted": {
                            "type": "boolean"
                        }
                    }
                }
            }
        },
        "settings": {
            "number_of_shards": "3",
            "number_of_replicas": "2",
            "index": {
                "routing": {
                    "allocation": {
                        "include": {
                                "_tier_preference": "data_content"
                        }
                    }
                }
            },
            "analysis": {
                "normalizer": {
                    "dnb_normalizer": {
                        "type": "custom",
                        "filter": ["lowercase"]
                    }
                }
            }
        }
    }
    es.indices.create(index=index_name, body=request_body)
