import json
import logging
import time

from django.core.management import call_command
from django.shortcuts import render
from .models import create_and_register_dynamic_model
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from sample.middlewares import create_custom_migration
from io import StringIO
import re
from django.apps import apps
# Create your views here.


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