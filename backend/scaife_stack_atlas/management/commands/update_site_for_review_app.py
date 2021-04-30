import os

from django.conf import settings
from django.core.management.base import BaseCommand

from django.contrib.sites.models import Site


class Command(BaseCommand):
    """
    Updates the site in the database with the review app domain
    """

    help = "Updates the site in the database with the review app domain"

    def handle(self, *args, **options):
        if settings.SITE_ID != 1:
            return
        heroku_app_name = os.environ.get("HEROKU_APP_NAME")
        if not heroku_app_name:
            return
        site = Site.objects.get_current()
        site.name = f"ATLAS {heroku_app_name} [review-app]"
        site.domain = f"{heroku_app_name}.herokuapp.com"
        site.save()
        self.stdout.write(f"Updated site: {site}")
