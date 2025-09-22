from django.views.generic import ListView, DetailView
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from .models import Recipe, recipe_collection
from django.http import JsonResponse
from coffee.helpers import non_accent_vietnamese
from coffee.upload import pathByDate, uploadFile
from cms.middlewares import PermissionRequired
from django.utils import timezone
from django.utils.text import slugify

