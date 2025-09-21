import uuid

from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """Base model with common fields."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class BaseRepository:
    """Base repository pattern implementation."""

    def __init__(self, model_class):
        self.model = model_class

    def get_by_id(self, obj_id):
        """Get object by ID."""
        try:
            return self.model.objects.get(id=obj_id, is_active=True)
        except self.model.DoesNotExist:
            return None

    def get_all_active(self):
        """Get all active objects."""
        return self.model.objects.filter(is_active=True)

    def create(self, **kwargs):
        """Create new object."""
        return self.model.objects.create(**kwargs)

    def update(self, obj_id, **kwargs):
        """Update object."""
        obj = self.get_by_id(obj_id)
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            obj.save()
        return obj

    def soft_delete(self, obj_id):
        """Soft delete object."""
        obj = self.get_by_id(obj_id)
        if obj:
            obj.is_active = False
            obj.save()
        return obj

    def filter_by(self, **kwargs):
        """Filter objects by given criteria."""
        return self.model.objects.filter(is_active=True, **kwargs)

    def count(self):
        """Count active objects."""
        return self.model.objects.filter(is_active=True).count()

    def exists(self, obj_id):
        """Check if object exists."""
        return self.model.objects.filter(id=obj_id, is_active=True).exists()
