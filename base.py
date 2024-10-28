from django.db import models

def create_dynamic_model(name, fields=None):
    # Default to an empty dictionary if no fields are provided
    if fields is None:
        fields = {}

    # Add the __module__ attribute for Django model registration
    fields['__module__'] = __name__

    # Use type() to create a new model class with Django's ModelBase as its metaclass
    return type(name, (models.Model,), fields)

# Example usage
DynamicClient = create_dynamic_model('DynamicClient', {
    'name': models.CharField(max_length=255),
    'email': models.EmailField(unique=True),
    'phone_number': models.CharField(max_length=20)
})


#     migration_content = f"""\
# from django.db import migrations
#
# class Migration(migrations.Migration):
#
#     dependencies = [
#         ('{app_label}', 'last_migration_name'),  # Replace with the actual last migration name
#     ]
#
#     operations = [
#         migrations.RunSQL(
#             \"\"\"
#             {sql_up}
#             \"\"\",
#             reverse_sql=\"\"\"
#             {sql_down}
#             \"\"\"
#         ),
#     ]
#     """
#     breakpoint()
#     # Write the migration content to the file
#     with open(migration_path, 'w') as migration_file:
#         migration_file.write(migration_content)
