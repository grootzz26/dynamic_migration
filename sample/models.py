
from django.apps import apps
from django.core.management import call_command
from django.db import models
from django.db.utils import OperationalError, ProgrammingError

def get_dynamic_model(app_label, params, fields, model_name):
    fields['__module__'] = __name__
    meta_attrs = {"app_label": app_label}
    if "db_table" in params:
        meta_attrs["managed"] = True
        meta_attrs["db_table"] = params["db_table"]
    fields['Meta'] = type("Meta", (), meta_attrs)
    DynamicModel = type(model_name, (models.Model,), fields)
    return DynamicModel

def parse_field_definitions(field_definitions, app_label, model_name, model_dict=None):
    parsed_fields = {}
    mapped_models = []
    for field_name, field_def in field_definitions.items():
        # Handle special keys like "managed" and "db_table" directly
        if "ForeignKey" in field_def:
            key = field_def.split("(")[1].split(",")[0]
            field_definitions = dict(model_dict[key.lower()])
            stub_model = parse_field_definitions(field_definitions, app_label, model_name, model_dict)
            fields = {name: field for name, field in stub_model.items() if name not in ["managed", "db_table"]}
            DynamicModel = get_dynamic_model(app_label, stub_model, fields, stub_model["db_table"].split("_")[-1])
            apps.register_model(app_label, DynamicModel)
            field_def = field_def.replace(key, "DynamicModel")

        if field_name == 'managed':
            parsed_fields[field_name] = field_def == 'True'
        elif field_name == 'db_table':
            parsed_fields[field_name] = field_def.strip("'")
        else:
            # Dynamically evaluate the field definition
            parsed_fields[field_name] = eval(field_def)

    return parsed_fields

def create_and_register_dynamic_model(model_dict, app_label, model_name, fields=None):
    app_label_key = f"{app_label}{model_name}".lower()
    try:
        DynamicModel = apps.get_model(app_label, model_name)
    except:
        DynamicModel = None
    if DynamicModel:
        return DynamicModel
    if app_label_key in model_dict:
        params = parse_field_definitions(dict(model_dict[app_label_key]), app_label, model_name, model_dict)
        fields = {name: field for name, field in params.items() if name not in ["managed", "db_table"]}
    else:
        fields = {}
        params = {}
    DynamicModel = get_dynamic_model(app_label, params, fields, model_name)
    apps.register_model(app_label, DynamicModel)
    return DynamicModel

