# Lumnus singular-store migration:
#   1. IssueComment.comment_md — MD+YAML canonical comment body (sibling of Issue.description_md).
#   2. Backfill: every existing Issue/IssueComment with an HTML body and no MD gets its MD
#      converted from the HTML (one-time boundary conversion). From this point the MD is the
#      single source; HTML is a save-time derived projection.
# Reverse: field drop only; backfilled MD content is left in place on rollback of data step.

from django.db import migrations, models


def backfill_markdown(apps, schema_editor):
    from plane.utils.markdown_body import convert_html_to_markdown

    Issue = apps.get_model("db", "Issue")
    IssueComment = apps.get_model("db", "IssueComment")

    # historical models don't expose .objects when the live model uses custom managers
    # without use_in_migrations — _base_manager is always present
    for issue in (
        Issue._base_manager.filter(description_md__isnull=True)
        .exclude(description_html__in=["", "<p></p>"])
        .only("id", "description_html")
        .iterator()
    ):
        md = convert_html_to_markdown(issue.description_html)
        if md:
            # historical model — plain save, no custom derivation runs
            Issue._base_manager.filter(pk=issue.pk).update(description_md=md)

    for comment in (
        IssueComment._base_manager.filter(comment_md__isnull=True)
        .exclude(comment_html__in=["", "<p></p>"])
        .only("id", "comment_html")
        .iterator()
    ):
        md = convert_html_to_markdown(comment.comment_html)
        if md:
            IssueComment._base_manager.filter(pk=comment.pk).update(comment_md=md)


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0122_issue_description_md"),
    ]

    operations = [
        migrations.AddField(
            model_name="issuecomment",
            name="comment_md",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_markdown, migrations.RunPython.noop),
    ]
