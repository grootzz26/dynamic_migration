# Generated by Django 5.1.2 on 2024-10-28 09:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sample', '0002_auto_20241028_0939'),
    ]

    operations = [
        migrations.RunSQL(
            """
CREATE TABLE sample_address (
    id INT PRIMARY KEY,
    city VARCHAR(50),
    state VARCHAR(50)
);
            """,
            reverse_sql="""
DROP TABLE IF EXISTS sample_address;
            """
        ),
    ]
