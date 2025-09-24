from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
import os
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
import io
from coffee.upload import pathByDate, uploadFile, save_file, remove_special_characters
from django.conf import settings
import numpy as np
from scipy import stats
from scipy.optimize import minimize
import pandas as pd

class IndexDataViewSet(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            file = request.FILES.get('file')
            if not file:
                return Response({'success': False, 'message': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
            
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
                
                base_month = []
                # Copy titles from B1 to max_column
                for col in range(2, end_col + 1):  # B to max_column
                    cell = ws.cell(row=title_row, column=col)
                    output_ws.cell(row=title_row, column=col).value = cell.value
                    base_month.append(cell.value)

                
                # for row in range(2):
                #     output_ws.cell(row=row, column=end_col + 5).value = base_month[row - 2]
                      
                
                # Create 7 new columns after max_column
                output_ws.cell(row=title_row, column=end_col + 2).value = ""
                output_ws.cell(row=title_row, column=end_col + 3).value = ""
                output_ws.cell(row=title_row, column=end_col + 5).value = "Month"
                output_ws.cell(row=title_row, column=end_col + 6).value = "Beta"
                output_ws.cell(row=title_row, column=end_col + 7).value = "Phase Beta"
                output_ws.cell(row=title_row, column=end_col + 8).value = "P(x) Beta"
                output_ws.cell(row=title_row, column=end_col + 9).value = "Alpha"
                output_ws.cell(row=title_row, column=end_col + 10).value = "Phase Alpha"
                output_ws.cell(row=title_row, column=end_col + 11).value = "P(x) Alpha"
             

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
                    
                    # Process columns C to max_column
                    for col in range(start_col, end_col + 1):
                        cell = ws.cell(row=row, column=col)
                        if row == 1 or col == 2:  # Skip titles and column B
                            continue
                        elif cell.value is None or base_values[col] == 0:
                            output_ws.cell(row=row, column=col).value = None
                        else:
                            # Apply formula: (current / base) * 100
                            output_ws.cell(row=row, column=col).value = (cell.value / base_values[col]) * 100
            
            # Remove the default empty sheet if it exists
            if 'Sheet' in output_wb.sheetnames:
                del output_wb['Sheet']
            
            # Save to BytesIO
            output_io = io.BytesIO()
            output_wb.save(output_io)
            output_io.seek(0)
            
            # Save file to local
            filename = "processed_data.xlsx"
            path = pathByDate()
            relative_path = os.path.join('uploads', path, filename)
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(output_io.getvalue())
            
            response = Response({
                'success': True,
                'data': "File processed and saved successfully",
                'file_path': f"http://localhost:8000/media/{relative_path}"
            }, status=status.HTTP_200_OK)
            return response
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
class TestSuperpositionLinearRegression(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        try:
            file = request.FILES.get("file")
            if not file:
                return Response({
                    "status": False,
                    "message": "File Excel không hợp lệ"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Load Excel
            wb = openpyxl.load_workbook(file, data_only=True)
            ws = wb.active

            # === CẢI TIẾN 1: Xử lý dữ liệu đầu vào tốt hơn ===
            # Lấy dữ liệu từ cột W (2024/25)
            y_actual = []
            for row in ws.iter_rows(min_row=5, min_col=23, max_col=23):  # cột W là col 23
                val = row[0].value
                if val is not None and not np.isnan(val):
                    y_actual.append(val)
            y_actual = np.array(y_actual, dtype=float)

            # Lấy dữ liệu input từ các cột C,U (C, E, G, I, K, M, O, Q, S, U)
            input_cols = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
            X_raw = []
            for row in ws.iter_rows(min_row=5, max_row=4 + len(y_actual)):
                values = []
                for col in input_cols:
                    cell_val = row[col - 1].value
                    values.append(cell_val if cell_val is not None else 0)
                X_raw.append(values)
            X_raw = np.array(X_raw, dtype=float)

            # Loại bỏ outliers sử dụng IQR method
            def remove_outliers(data):
                Q1 = np.percentile(data, 25)
                Q3 = np.percentile(data, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                return data[(data >= lower_bound) & (data <= upper_bound)]

            # Áp dụng loại bỏ outliers cho y_actual
            y_clean = remove_outliers(y_actual)

            # Tìm indices tương ứng với dữ liệu sạch
            valid_indices = []
            for i, val in enumerate(y_actual):
                if np.isin(val, y_clean):
                    valid_indices.append(i)

            X_clean = X_raw[valid_indices]
            y_clean = y_actual[valid_indices]

            # === CẢI TIẾN 2: Biến đổi dữ liệu để tăng tính tuyến tính ===
            # Áp dụng log transformation nếu dữ liệu có range lớn
            if np.max(X_clean) / np.min(X_clean) > 100:
                X_transformed = np.log1p(X_clean)  # log(1 + x) để tránh log(0)
            else:
                X_transformed = X_clean

            # Chuẩn hóa dữ liệu
            X_mean = np.mean(X_transformed, axis=0)
            X_std = np.std(X_transformed, axis=0)
            X_normalized = (X_transformed - X_mean) / X_std

            # Sử dụng X_normalized thay vì X_clean
            X = X_normalized

            num_inputs = X.shape[1]   # = 10 cột
            num_phases = num_inputs * 2  # = 20 (10 beta + 10 alpha)

            def calc_density(phases):
                sq = np.square(phases)
                return sq / np.sum(sq)

            def forecast(phases):
                beta_phases = phases[:num_inputs]
                alpha_phases = phases[num_inputs:]

                beta_density = calc_density(beta_phases)
                alpha_density = calc_density(alpha_phases)

                forecast_vals = X.dot(beta_density) + X.dot(alpha_density)
                return forecast_vals

            # === CẢI TIẾN 3: Hàm loss cải tiến ===
            def loss(phases):
                y_pred = forecast(phases)

                # Sử dụng R-squared thay vì correlation coefficient
                ss_res = np.sum((y_clean - y_pred) ** 2)
                ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

                return -r_squared  # Minimize negative R-squared để maximize R-squared

            # === CẢI TIẾN 4: Khởi tạo tốt hơn ===
            # Khởi tạo với uniform distribution thay vì random
            init_phases = np.ones(num_phases) / np.sqrt(num_phases)

            # === CẢI TIẾN 5: Sử dụng nhiều phương pháp optimization ===
            methods = ['Nelder-Mead', 'Powell', 'L-BFGS-B']

            best_result = None
            best_r_squared = -np.inf

            for method in methods:
                try:
                    if method == 'L-BFGS-B':
                        # Thêm bounds cho L-BFGS-B
                        bounds = [(0, 1) for _ in range(num_phases)]
                        result = minimize(loss, init_phases, method=method, bounds=bounds)
                    else:
                        result = minimize(loss, init_phases, method=method)

                    current_r_squared = -result.fun
                    if current_r_squared > best_r_squared:
                        best_r_squared = current_r_squared
                        best_result = result
                except:
                    continue

            if best_result is None:
                return Response({
                    "status": False,
                    "message": "Không thể tìm được nghiệm tối ưu"
                }, status=status.HTTP_400_BAD_REQUEST)

            best_phases = best_result.x
            beta_final = calc_density(best_phases[:num_phases//2])
            alpha_final = calc_density(best_phases[num_phases//2:])
            forecast_final = forecast(best_phases)
            corr_final = np.corrcoef(y_clean, forecast_final)[0, 1]
            r_squared_final = best_r_squared

            # === CẢI TIẾN 6: Validation ===
            if r_squared_final < 0.1:  # Nếu R-squared quá thấp
                return Response({
                    "status": False,
                    "message": f"R-squared quá thấp: {r_squared_final:.4f}. Cần kiểm tra dữ liệu đầu vào."
                }, status=status.HTTP_400_BAD_REQUEST)

            # Lưu file Excel
            output_wb = Workbook()
            output_ws = output_wb.active

            # Copy dữ liệu từ sheet gốc
            for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
                for cell in row:
                    output_ws[cell.coordinate].value = cell.value

            # Thêm dữ liệu forecast vào sheet
            for row in range(5, 5 + len(y_clean)):
                output_ws.cell(row=row, column=24).value = forecast_final[row - 5]

            # Lưu file Excel
            output_io = io.BytesIO()
            output_wb.save(output_io)
            output_io.seek(0)

            # Lưu file Excel
            filename = "processed_data_regression.xlsx"
            path = pathByDate()
            relative_path = os.path.join('uploads', path, filename)
            full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, 'wb') as f:
                f.write(output_io.getvalue())

            return Response({
                "status": True,
                "file_path": f"http://localhost:8000/media/{relative_path}",
                "beta": beta_final.tolist(),
                "alpha": alpha_final.tolist(),
                "forecast": forecast_final.tolist(),
                "correlation": float(corr_final),
                "r_squared": float(r_squared_final),
                "improvements": {
                    "outliers_removed": len(y_actual) - len(y_clean),
                    "data_normalization": "applied",
                    "optimization_methods_tried": len(methods),
                    "best_method": best_result.success and best_result.message or "Nelder-Mead"
                }
            })

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

