import uuid
from django.db import models
from django.utils.text import slugify
from db_connection import db

# recipe_collection = db['recipe']

# class Recipe(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=255)
#     name_non = models.CharField(max_length=255, blank=True, null=True)
#     slug = models.SlugField(max_length=255, unique=True)
#     content = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     is_trash = models.BooleanField(default=False)

#     class Meta:
#         db_table = 'recipe'
#         verbose_name = 'Recipe'
#         verbose_name_plural = 'Recipes'


#     def __str__(self):
#         return self.name

#     def save(self, *args, **kwargs):
#         if not self.slug:
#             self.slug = slugify(self.name_non)
#         super().save(*args, **kwargs)