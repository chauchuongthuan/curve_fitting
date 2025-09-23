from django.views.generic import ListView, DetailView
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Q
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from coffee.upload import pathByDate, uploadFile
from django.utils import timezone
from django.utils.text import slugify
import os
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import io
from django.conf import settings
from coffee.helpers import gennerate_random_string
class IndexDataCreateView(View):
    @login_required(login_url="login_cms")
    def create(request):
        if request.method == 'POST':
            try:
                file = request.FILES.get('file')
                print("file:::", file)
                if not file:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'File không hợp lệ'
                    }, status=400)
                 # Load the uploaded Excel file
                wb = openpyxl.load_workbook(file)
            
                # Create a new workbook for output
                output_wb = Workbook()
                
                # Process each sheet in the original workbook
                for sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    
                    # Create a new sheet in output workbook with the same name
                    output_ws = output_wb.create_sheet(title=sheet_name)
                    if sheet_name == wb.sheetnames[0]:
                        output_wb.active = output_ws  # Set first sheet as active
                    
                    # Get the range of columns to process (C to max_column)
                    start_col = 3  # C
                    end_col = ws.max_column
                    title_row = 1
                    base_row = 2
                    
                    # Copy titles from B1 to max_column (for original columns)
                    for col in range(2, end_col + 1):  # B to max_column
                        cell = ws.cell(row=title_row, column=col)
                        output_ws.cell(row=title_row, column=col).value = cell.value
                    
                    # Get base values from row 2, columns C to max_column
                    base_values = {}
                    for col in range(start_col, end_col + 1):
                        cell = ws.cell(row=base_row, column=col)
                        base_values[col] = cell.value if cell.value is not None else 0
                    
                    # Process each row
                    max_row = ws.max_row

                    for row in range(1, max_row + 1):
                        # Copy column B
                        cell_b = ws.cell(row=row, column=2)
                        output_ws.cell(row=row, column=2).value = cell_b.value
                        out_col = (col - start_col) * 2 + 3  # bắt đầu từ C trong output

                        cell = ws.cell(row=row, column=col)
                        # Process columns C to max_column
                        for col in range(start_col, end_col + 1):
                            # Tính toán vị trí cột mới trong output (mỗi col -> 2 col)
                            out_col = (col - start_col) * 2 + 3  # bắt đầu từ C trong output

                            cell = ws.cell(row=row, column=col)
                            if row == 1:  # tiêu đề
                                output_ws.cell(row=row, column=out_col).value = ws.cell(row=row, column=col).value
                                output_ws.cell(row=row, column=out_col + 1).value = f""
                            else:
                                if cell.value is None or base_values[col] == 0:
                                    output_ws.cell(row=row, column=out_col).value = None
                                    output_ws.cell(row=row, column=out_col + 1).value = None
                                else:
                                    # Apply original formula: (current / base) * 100
                                    output_value = (cell.value / base_values[col]) * 100
                                    output_ws.cell(row=row, column=out_col).value = output_value

                                    # Add new column with formula: 1 / current * 10000
                                    oposite_value = 1 / output_value * 10000
                                    output_ws.cell(row=row, column=out_col + 1).value = oposite_value
                
                # Save to BytesIO
                output_io = io.BytesIO()
                if 'Sheet' in output_wb.sheetnames:
                    del output_wb['Sheet']
                output_wb.save(output_io)
                output_io.seek(0)

                random_string = gennerate_random_string()

                # Save file to local
                filename = f"processed_data_{random_string}.xlsx"
                path = pathByDate()
                relative_path = os.path.join('uploads', path, filename)
                full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'wb') as f:
                    f.write(output_io.getvalue())
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Uploaded successfully!',
                    'file_path': f"http://localhost:8000/media/{relative_path}",
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error when uploading file: {str(e)}'
                }, status=400)
        return render(request, 'indexData/create.html')