from django.core.files import File
from django.core.files.storage import storages
from django.core.management.base import BaseCommand

from account.media_utils import resolve_local_media_path
from account.models import Customer, Product


class Command(BaseCommand):
    help = "Upload existing local media files to the active remote storage and update model fields."

    def handle(self, *args, **options):
        active_storage = storages["default"]

        if active_storage.__class__.__module__.startswith("django.core.files.storage"):
            self.stdout.write(
                self.style.WARNING(
                    "Default storage is still local. Skipping Cloudinary sync."
                )
            )
            return

        specs = (
            (Customer, "profile_image", "Customer", "profile"),
            (Product, "pic", "Product", "product_image"),
        )

        total_synced = 0
        total_skipped = 0
        total_missing = 0

        for model, field_name, label, upload_dir in specs:
            synced, skipped, missing = self.sync_model_files(model, field_name, label, upload_dir)
            total_synced += synced
            total_skipped += skipped
            total_missing += missing

        self.stdout.write(
            self.style.SUCCESS(
                f"Cloudinary sync complete. synced={total_synced}, skipped={total_skipped}, missing={total_missing}"
            )
        )

    def sync_model_files(self, model, field_name, label, upload_dir):
        synced = 0
        skipped = 0
        missing = 0

        for obj in model.objects.exclude(**{field_name: ""}).iterator():
            field_file = getattr(obj, field_name)
            stored_name = str(field_file)

            if not stored_name:
                continue

            local_path = resolve_local_media_path(stored_name, upload_dir=upload_dir)

            if not local_path:
                missing += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Missing local file for {label}#{obj.pk}: {stored_name}"
                    )
                )
                continue

            if field_file.storage.exists(stored_name):
                skipped += 1
                self.stdout.write(
                    f"Already present in Cloudinary for {label}#{obj.pk}: {stored_name}"
                )
                continue

            with local_path.open("rb") as source:
                field_file.save(local_path.name, File(source), save=False)

            obj.save(update_fields=[field_name])
            synced += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Synced {label}#{obj.pk}: {stored_name} -> {getattr(obj, field_name).name}"
                )
            )

        return synced, skipped, missing
