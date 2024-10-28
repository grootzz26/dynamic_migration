import json
import time

from django.db.migrations.recorder import MigrationRecorder
from django.core.management import call_command
from root.settings import INSTALLED_APPS
import os
from django.conf import settings
from django.utils import timezone
from filelock import FileLock


def create_custom_migration(app_label, model, columns):
    # Define the migrations directory and filename
    app_migrations_dir = os.path.join(settings.BASE_DIR, app_label, 'migrations')
    if not os.path.exists(app_migrations_dir):
        os.makedirs(app_migrations_dir)

    # Generate a timestamp for a unique migration name
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = [i for i in sorted(os.listdir(app_migrations_dir)) if i not in ["__pycache__", "__init__.py"]][-1]
    migration_path = os.path.join(app_migrations_dir, filename)

    columns_sql = ",\n    ".join([f"{name} {data_type}" for name, data_type in columns.items()])
    sql_up = f"CREATE TABLE {app_label}_{model} (\n    {columns_sql}\n);"
    sql_down = f"DROP TABLE IF EXISTS {app_label}_{model};"
    lock_path = migration_path + '.lock'
    lock = FileLock(lock_path)

    with lock:
        with open(migration_path, 'r') as file:
            lines = file.readlines()
        # Define the content of the migration file
        with open(migration_path, 'w') as file:
            for line in lines:
                if "operations = [" in line:
                    file.write(line)
                    file.write("        migrations.RunSQL(\n")
                    file.write(f'            """\n{sql_up}\n            """,\n')
                    file.write(f'            reverse_sql="""\n{sql_down}\n            """\n')
                    file.write("        ),\n")
                    continue
                file.write(line)
    os.remove(lock_path)
    print(f"Migration file '{filename}' created at: {migration_path}")


class CustomMigrationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def process_request(self, request):
        path = request.path.strip()
        if not any( x in path for x in ["create_table", "generate_migrations"]):
            return request
        if request.method.lower() != "post":
            return request
        body = request.body.decode("utf-8")
        if body and isinstance(body, str):
            body = json.loads(body)
        app_label = body.get("app_label",None)
        if not app_label or app_label not in INSTALLED_APPS:
            return request
        # migrations = MigrationRecorder.Migration.objects.filter(app__in=INSTALLED_APPS)
        migrations = MigrationRecorder.Migration.objects.filter(app=app_label)
        # if not migrations:
        #     call_command("makemigrations", f"{app_label}", "--empty")
        # else:
        #     dependencies = migrations.last().name if migrations else ""
        #     call_command("makemigrations", f"{app_label}", "--empty")
        # app_migration = migrations.filter(app=app_label)
        # if len(app_migration) > 1:
        #     dependencies = migrations.get(id=app_migration.last().id - 1).name
        # else:
        #     dependencies = migrations.get(id=migrations.last().id - 1).name
        request.migrations_list = migrations
        request.app_label = app_label
        request.payload = body
        return request

    def __call__(self, request):

        request = self.process_request(request)

        response = self.get_response(request)

        return response