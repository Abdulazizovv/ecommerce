from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        indexes = [
            # Name and slug indexes for search and lookup
            models.Index(fields=['name'], name='category_name_idx'),
            models.Index(fields=['slug'], name='category_slug_idx'),
            
            # Time-based queries
            models.Index(fields=['created_at'], name='category_created_idx'),
            models.Index(fields=['updated_at'], name='category_updated_idx'),
            
            # Combined for ordering
            models.Index(fields=['name', 'created_at'], name='category_name_time_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
