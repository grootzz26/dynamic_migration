# Generated by Django 5.1.2 on 2024-10-28 09:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sample', '0003_auto_20241028_0947'),
    ]

    operations = [
        migrations.RunSQL(
            """
CREATE TABLE sample_hobby (
    id INT PRIMARY KEY,
    name VARCHAR(50),
    type VARCHAR(50)
);
            """,
            reverse_sql="""
DROP TABLE IF EXISTS sample_hobby;
            """
        ),
    ]
