# Lumnus: substrate-stable identity anchor on Issue — the Plane-side end of the
# task_projection.projection_map link. Indexed for reverse lookup ("which item
# carries gid X" / "which items carry none" = the ADOPT enumeration as one filter).
# No backfill here: the projector flow stamps gids via the API (hash-recipe v2
# re-run updates all projected items); hand-created items legitimately carry NULL.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0123_singular_md_body"),
    ]

    operations = [
        migrations.AddField(
            model_name="issue",
            name="work_item_gid",
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]
