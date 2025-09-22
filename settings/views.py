from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse

from .models import Setting
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from coffee.upload import pathByDate, uploadFile

class SettingListView:
    @login_required(login_url="login_cms")
    def update_or_create_setting(request, pk=None):
        if not pk:
            setting, created = Setting.objects.get_or_create(
                defaults={
                    'logo': '',
                    'address': '',
                    'phone': '',
                    'email': '',
                }
            )
        else:
            # If pk is provided, get the specific setting
            setting = get_object_or_404(Setting, pk=pk)
        if request.method == 'POST':
            try:
                address = request.POST.get('address')
                phone = request.POST.get('phone')
                email = request.POST.get('email')

                for image_field in ['logo']:
                    if image_field in request.FILES and request.FILES[image_field].name != '':
                        try: 
                            image = request.FILES[image_field]
                            image_url = uploadFile({'file': image}, f'/settings/{pathByDate()}')
                            setattr(setting, image_field, image_url)
                            print(f"{image_field} đã upload: {image_url}")
                        except Exception as e:
                            print(f"Lỗi khi upload {image_field}: {str(e)}")
                            raise ValueError(f'Lỗi khi upload {image_field}.')
                setting.address = address
                setting.phone = phone
                setting.email = email
                setting.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Cập nhật thông tin thành công!',
                    'redirect': reverse('settings')
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi cập nhật thông tin: {str(e)}'
                }, status=400)
        base_image_url = 'http://localhost:8000/media/uploads/'
        if setting.logo and setting.logo != '':
            setting.logo_url = f"{base_image_url}{setting.logo}"
        return render(request, 'settings/update.html', {'setting': setting})
            