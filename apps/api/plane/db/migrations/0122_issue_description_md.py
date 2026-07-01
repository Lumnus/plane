# Lumnus: MD+YAML-frontmatter canonical body field (AI-native task substrate)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0121_alter_estimate_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='description_md',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='issuedescriptionversion',
            name='description_md',
            field=models.TextField(blank=True, null=True),
        ),
    ]
