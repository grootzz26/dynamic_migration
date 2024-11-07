import json
import logging
import time
import gzip

from django.core.management import call_command
from django.shortcuts import render
from rest_framework.response import Response

from .models import create_and_register_dynamic_model
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from sample.middlewares import create_custom_migration
from io import StringIO
import re
import base64
from rest_framework import status
from Crypto.Cipher import AES
from rest_framework.decorators import api_view
from security import aes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os
from django.apps import apps
# Create your views here.
IV = AES.block_size * '\x00'
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[:-ord(s[len(s)-1:])]


@csrf_exempt
def generate_migrations(request):
    migrations = request.migrations_list
    app_label = request.app_label
    if not migrations:
        call_command("makemigrations", f"{app_label}", "--empty")
    else:
        dependencies = migrations.last().name if migrations else ""
        call_command("makemigrations", f"{app_label}", "--empty")
    return JsonResponse({"data": "migration file created!", "code": 201})

@csrf_exempt
def create_model(request):
    data = request.payload
    app_label = data["app_label"]
    model = data["model"]
    columns = data["fields"]
    try:
        create_custom_migration(app_label, model, columns)
    except Exception as e:
        logging.error(e)
        logging.info("Error in generating migration file")
    call_command("migrate", f"{app_label}")
    return JsonResponse({"data": "table created!", "code": 201})


@csrf_exempt
def fetch_data_from_dynamic_table(request):
    app_label = request.GET["app_label"]
    model = request.GET["model"]
    output = StringIO()
    call_command('inspectdb', stdout=output)
    models = output.getvalue()
    model_dict = {}

    # Regular expression to capture model names and their fields
    model_pattern = re.compile(r'class (\w+)\(models\.Model\):')
    fields_pattern = re.compile(r'^\s+(\w+) = (.+)$')

    # Split the output into lines for processing
    lines = models.splitlines()
    current_model = None

    for line in lines:
        # Check for model declaration
        model_match = model_pattern.search(line)
        if model_match:
            current_model = model_match.group(1)
            model_dict[current_model.lower()] = []
        # Check for field declarations if we are in a model
        elif current_model:
            field_match = fields_pattern.match(line)
            if field_match:
                field_name = field_match.group(1)
                field_definition = field_match.group(2)
                model_dict[current_model.lower()].append((field_name, field_definition))
    DynamicModel = create_and_register_dynamic_model(model_dict, app_label, model)
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        value = DynamicModel(**body)
        value.save()
        return JsonResponse({"data": "inserted successfully"})
    else:
        if DynamicModel:
            m = DynamicModel.objects.all()
            value = []
            for i in m:
                dic = {}
                dic["model"] = i.model
                dic["brand"] = i.brand
                dic["id"] = i.id
                value.append(dic)
            return JsonResponse({"data": value})
        else:
            value = []
            return JsonResponse({"data":value})


# def encrypted_response(request):
#     path = "/home/sargunaraj/Desktop/json_from_s3_excel.json"
#     with open(path, "r") as j:
#         data = json.load(j)
#     data = json.dumps(data).encode("utf-8")
#     key = os.urandom(32)
#     iv = os.urandom(16)
#     cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
#     encryptor = cipher.encryptor()
#     padder = padding.PKCS7(128).padder()
#     padded_data = padder.update(data) + padder.finalize()
#     encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
#     encrypted_data_base64 = base64.b64encode(encrypted_data).decode('utf-8')
#     iv_base64 = base64.b64encode(iv).decode('utf-8')
#     breakpoint()
#     pass

@api_view(["GET"])
def encrypted_response(request):
    path = "/home/sargunaraj/Desktop/json_from_s3_excel.json"
    with open(path, "r") as j:
        data = json.load(j)
    # data = json.dumps(data).encode("utf-8")
    breakpoint()
    if not data or data is None:
        return "FAIL"
    print('data going to give client is %s', str(data))
    # fn = {}
    # for _d in range(len(data["data"])):
    #     fn[str(_d)] = aes.compressed_data(json.dumps(data["data"][_d]))
        # result = aes.compressed_data(json.dumps(data))
    result = aes.compressed_data(json.dumps(data))
    # key = 'DImfVmeSe34DFGHH'.encode("utf-8")
    # enc = aes.encrypt(key, data.decode("utf-8"))
    # result = dict(data=enc)
    return Response(data={"data": result}, status=status.HTTP_200_OK)
    # try:
    #     cipher = AES.new(key, AES.MODE_CBC, IV)
    #     breakpoint()
    #     encrypted = base64.b64encode(cipher.encrypt(pad(data)))
    #     result = json.loads(encrypted)
    #     print(encrypted)
    #     return Response(data=result, status=status.HTTP_200_OK)
    # except Exception as e:
    #     breakpoint()
    #     print("key should not be None %s", e)
    # print("key data is : %s", key)
    # breakpoint()
    # return Response(data={"error": True}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
def decrpyt(request):
    body = json.loads(request.body.decode("utf-8"))
    encoded_data = body.get("data")
    compressed_data = base64.b64decode(encoded_data)
    decompressed_data = gzip.decompress(compressed_data)
    original_data = json.loads(decompressed_data.decode("utf-8"))
    return Response(data={"data": original_data}, status=status.HTTP_200_OK)
