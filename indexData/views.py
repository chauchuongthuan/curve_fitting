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
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import io
from django.conf import settings
from coffee.helpers import gennerate_random_string
import math
from scipy.optimize import *
import pandas as pd
from scipy.optimize import minimize


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
                for sheet_index, sheet_name in enumerate(wb.sheetnames):
                    ws = wb[sheet_name]
                    
                    # Create a new sheet in output workbook with the same name
                    output_ws = output_wb.create_sheet(title=sheet_name)
                    if sheet_index == 0:
                        output_wb.active = output_ws  # Set first sheet as active
                    
                    # Get dynamic dimensions
                    max_row = ws.max_row
                    max_col = ws.max_column
                    
                    # Find the actual data range dynamically
                    start_col = 3  # C - fixed starting column
                    end_col = max_col
                    
                    # Find title row dynamically by looking for non-empty cells in row 1
                    title_row = 1
                    base_row = 2
                    
                    # Validate if sheet has enough data
                    if max_row < 2 or max_col < 3:
                        print(f"Sheet {sheet_name} doesn't have enough data. Skipping.")
                        continue
                    
                    # Get base year values dynamically
                    base_year = []
                    for col in range(2, end_col + 1):  # B to max_column
                        cell = ws.cell(row=title_row, column=col)
                        if cell.value is not None:
                            base_year.append(cell.value)
                    
                    # Remove first and last elements if base_year has enough elements
                    if len(base_year) > 2:
                        base_year = base_year[1:-1]
                    
                    # Get base values from row 2 dynamically
                    base_values = {}
                    for col in range(start_col, end_col + 1):
                        cell = ws.cell(row=base_row, column=col)
                        base_values[col] = cell.value if cell.value is not None else 0
                    
                    # Copy column A and B for all rows
                    for row in range(1, max_row + 1):
                        # Copy column A
                        cell_a = ws.cell(row=row, column=1)
                        output_ws.cell(row=row, column=1).value = cell_a.value
                        
                        # Copy column B
                        cell_b = ws.cell(row=row, column=2)
                        output_ws.cell(row=row, column=2).value = cell_b.value
                    
                    # Process data columns (C to max_column)
                    for col in range(start_col, end_col + 1):
                        # Calculate output column position (each input column becomes 2 output columns)
                        out_col_start = (col - start_col) * 2 + 3
                        
                        # Process title row
                        title_value = ws.cell(row=title_row, column=col).value
                        output_ws.cell(row=title_row, column=out_col_start).value = title_value
                        output_ws.cell(row=title_row, column=out_col_start + 1).value = f""
                        
                        # Process data rows
                        for row in range(2, max_row + 1):
                            cell = ws.cell(row=row, column=col)
                            
                            if cell.value is None or base_values.get(col, 0) == 0:
                                output_ws.cell(row=row, column=out_col_start).value = None
                                output_ws.cell(row=row, column=out_col_start + 1).value = None
                            else:
                                # Apply original formula: (current / base) * 100
                                output_value = (cell.value / base_values[col]) * 100
                                output_ws.cell(row=row, column=out_col_start).value = output_value

                                # Add new column with formula: 1 / current * 10000
                                oposite_value = 1 / output_value * 10000
                                output_ws.cell(row=row, column=out_col_start + 1).value = oposite_value
                    
                    # Calculate the maximum column after processing
                    processed_cols_count = (end_col - start_col + 1) * 2
                    max_col_all = 2 + processed_cols_count  # 2 fixed columns (A+B) + processed columns
                    
                    # Create new columns after all processed data - ĐIỀU CHỈNH THỨ TỰ CÁC CỘT
                    new_columns = [
                        "Phase Forecast", "P(x) Forecast",  # Cột forecast trước
                        "Phase Correlation", "P(x) Correlation",  # Cột correlation sau
                        "Year", "Beta", "Beta Phase", "Beta P(X) Density", 
                        "Alpha", "Alpha Phase", "Alpha P(X) Density"
                    ]
                    
                    for i, col_name in enumerate(new_columns):
                        output_ws.cell(row=title_row, column=max_col_all + i + 1).value = col_name
                    
                    # Process base_year data for Year column
                    if base_year:
                        for row in range(2, len(base_year) + 2):
                            if row <= max_row:  # Ensure we don't exceed sheet boundaries
                                output_ws.cell(row=row, column=max_col_all + 5).value = base_year[row - 2] if row - 2 < len(base_year) else None
                                output_ws.cell(row=row, column=max_col_all + 6).value = "β" + str(row - 2 + 1)
                                
                                beta = 1 / math.sqrt(len(base_year) * 2) if base_year else 0
                                output_ws.cell(row=row, column=max_col_all + 7).value = beta

                                # Beta squared formula with percentage format
                                if beta != 0:
                                    beta_cell_ref = get_column_letter(max_col_all + 7) + str(row)
                                    beta_sq_cell = output_ws.cell(row=row, column=max_col_all + 8)
                                    beta_sq_cell.value = f"={beta_cell_ref}^2"
                                    beta_sq_cell.number_format = '0.0%'

                                output_ws.cell(row=row, column=max_col_all + 9).value = "α" + str(row - 2 + 1)
                                alpha = 1 / math.sqrt(len(base_year) * 2) if base_year else 0
                                output_ws.cell(row=row, column=max_col_all + 10).value = alpha

                                # Alpha squared formula with percentage format
                                if alpha != 0:
                                    alpha_cell_ref = get_column_letter(max_col_all + 10) + str(row)
                                    alpha_sq_cell = output_ws.cell(row=row, column=max_col_all + 11)
                                    alpha_sq_cell.value = f"={alpha_cell_ref}^2"
                                    alpha_sq_cell.number_format = '0.0%'
                    
                    # Forecast formulas - dynamic based on actual data columns
                    def calculate_forecast_formula(beta_col_offset, alpha_col_offset, output_col_offset):
                        """Calculate forecast formula using dynamic column references"""
                        col_beta_letter = get_column_letter(max_col_all + beta_col_offset)
                        col_alpha_letter = get_column_letter(max_col_all + alpha_col_offset)

                        for row_idx in range(2, max_row + 1):
                            formula_part1 = []
                            formula_part2 = []
                            
                            for i in range(len(base_year)):
                                if i < (end_col - start_col + 1):  # Ensure we don't exceed available data columns
                                    data_col_letter = get_column_letter(3 + i * 2)  # Start from column C

                                    beta_cell_ref = f"${col_beta_letter}${2 + i}"
                                    formula_part1.append(f"{data_col_letter}{row_idx}*{beta_cell_ref}")

                                    alpha_cell_ref = f"${col_alpha_letter}${2 + i}"
                                    formula_part2.append(f"{data_col_letter}{row_idx}*{alpha_cell_ref}")

                            if formula_part1 and formula_part2:  # Only add formula if there are components
                                final_formula = f"=({' + '.join(formula_part1)}) + ({' + '.join(formula_part2)})"
                                output_ws.cell(row=row_idx, column=max_col_all + output_col_offset).value = final_formula

                    # Calculate forecasts only if there's base year data
                    if base_year and len(base_year) > 0:
                        # Tính forecast trước (cột 1 và 2 trong new_columns)
                        calculate_forecast_formula(7, 10, 1)  # Phase Forecast - cột thứ 1
                        calculate_forecast_formula(8, 11, 2)  # P(x) Forecast - cột thứ 2
                        
                        # Sau đó tính correlation (cột 3 và 4 trong new_columns)
                        # Tìm cột năm cuối cùng (cột dữ liệu gốc)
                        last_year_col = 3 + (len(base_year)) * 2  # Cột dữ liệu gốc của năm cuối
                        last_year_col_letter = get_column_letter(last_year_col)
                        
                        # Tính correlation formulas
                        phase_forecast_col = max_col_all + 1  # Phase Forecast column
                        p_forecast_col = max_col_all + 2      # P(x) Forecast column
                        
                        phase_forecast_col_letter = get_column_letter(phase_forecast_col)
                        p_forecast_col_letter = get_column_letter(p_forecast_col)
                        
                        # Phase Correlation formula: =CORREL(AA2:AA733,$W$2:$W$733)
                        phase_correl_formula = f"=CORREL({phase_forecast_col_letter}2:{phase_forecast_col_letter}{max_row}, ${last_year_col_letter}$2:${last_year_col_letter}${max_row})"
                        output_ws.cell(row=2, column=max_col_all + 3).value = phase_correl_formula
                        
                        # P(x) Correlation formula: =CORREL(AB2:AB733,$W$2:$W$733)
                        p_correl_formula = f"=CORREL({p_forecast_col_letter}2:{p_forecast_col_letter}{max_row}, ${last_year_col_letter}$2:${last_year_col_letter}${max_row})"
                        output_ws.cell(row=2, column=max_col_all + 4).value = p_correl_formula

                    # SUM calculations only if there's data
                    if base_year and len(base_year) > 0:
                        start_row = 2
                        end_row = min(len(base_year) + 1, max_row)
                        
                        # SUM beta^2
                        col_beta_sq = max_col_all + 8
                        if end_row >= start_row:
                            sum_range_beta = f"{get_column_letter(col_beta_sq)}{start_row}:{get_column_letter(col_beta_sq)}{end_row}"
                            total_beta_sq_cell = output_ws.cell(row=end_row + 1, column=col_beta_sq)
                            total_beta_sq_cell.value = f"=SUM({sum_range_beta})"
                            total_beta_sq_cell.number_format = '0.0%'

                        # SUM alpha^2
                        col_alpha_sq = max_col_all + 11
                        if end_row >= start_row:
                            sum_range_alpha = f"{get_column_letter(col_alpha_sq)}{start_row}:{get_column_letter(col_alpha_sq)}{end_row}"
                            total_alpha_sq_cell = output_ws.cell(row=end_row + 1, column=col_alpha_sq)
                            total_alpha_sq_cell.value = f"=SUM({sum_range_alpha})"
                            total_alpha_sq_cell.number_format = '0.0%'
                        
                        # SUM all = SUM beta^2 + alpha^2
                        col_all = max_col_all + 12
                        if end_row >= start_row:
                            # Create formula: SUM(beta^2) + SUM(alpha^2)
                            beta_sum_ref = get_column_letter(col_beta_sq) + str(end_row + 1)
                            alpha_sum_ref = get_column_letter(col_alpha_sq) + str(end_row + 1)
                            total_all_cell = output_ws.cell(row=end_row + 1, column=col_all)
                            total_all_cell.value = f"={beta_sum_ref} + {alpha_sum_ref}"
                            total_all_cell.number_format = '0.0%'

                # Remove default sheet if it exists
                if 'Sheet' in output_wb.sheetnames:
                    del output_wb['Sheet']
                    
                # Save to BytesIO
                output_io = io.BytesIO()
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
        