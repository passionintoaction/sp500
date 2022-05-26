import requests
import json
import utils
import numpy as np
# import boto3


def call_api(input_dict, model, task):
    if model == 'sp500':
        res=run_sp500(input_dict)
        
        return res


def run_sp500(input_dict):
    return "abcd"