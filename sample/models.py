from django.apps import apps
from django.db import models
from django.db.utils import OperationalError, ProgrammingError


def parse_field_definitions(field_definitions):
    parsed_fields = {}

    for field_name, field_def in field_definitions.items():
        # Handle special keys like "managed" and "db_table" directly
        if field_name == 'managed':
            parsed_fields[field_name] = field_def == 'True'
        elif field_name == 'db_table':
            parsed_fields[field_name] = field_def.strip("'")
        else:
            # Dynamically evaluate the field definition
            parsed_fields[field_name] = eval(field_def)

    return parsed_fields

def create_and_register_dynamic_model(model_dict, app_label, model_name, fields=None):
    # Use an empty dictionary if no fields are provided
    app_label_key = f"{app_label}{model_name}".lower()
    try:
        DynamicModel = apps.get_model(app_label, model_name)
    except:
        DynamicModel = None
    if DynamicModel:
        return DynamicModel
    if app_label_key in model_dict:
        params = parse_field_definitions(dict(model_dict[app_label_key]))
        fields = {name: field for name, field in params.items() if name not in ["managed", "db_table"]}
    else:
        fields = {}
        params = {}

    # Add __module__ to specify where the model is created
    fields['__module__'] = __name__
    # fields['Meta'] = type("Meta", (), {"managed": True, "db_table": f"{app_label}_{model_name}"})
    meta_attrs = {"app_label": app_label}
    if "db_table" in params:
        meta_attrs["managed"] = True
        meta_attrs["db_table"] = params["db_table"]
    fields['Meta'] = type("Meta", (), meta_attrs)

    # Create the model class
    DynamicModel = type(model_name, (models.Model,), fields)
    apps.register_model(app_label, DynamicModel)
    # globals()[f"{app_label}{model_name}"] = DynamicModel
    # globals()[f"SampleActors"] = DynamicModel
    return DynamicModel
    # Register the model with the app's model registry
    # try:
    #     app_config = apps.get_app_config(app_label)
    #     apps.register_model(app_label, DynamicModel)
    #     app_config.models[model_name.lower()] = DynamicModel
    #     apps.all_models[app_label][model_name.lower()] = DynamicModel
    # except LookupError:
    #     raise ValueError(f"App with label '{app_label}' not found.")
    #
    # return DynamicModel

