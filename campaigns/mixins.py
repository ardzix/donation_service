from django.db import models

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, help_text="Soft delete flag.")

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    class Meta:
        abstract = True
