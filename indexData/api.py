from django.http import response
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
import xlwings as xw
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
class TestGrgSolver(APIView):
    def post(self, request):
        def grg_nonlinear_solver(objective_cell, variable_arrays, data_range, objective_type='max'):
            """
            GRG Nonlinear Solver that mimics Excel's behavior:
            - Tries to satisfy constraints but returns best solution even if not all constraints are met
            - Prioritizes finding a solution over perfect constraint satisfaction
            """
            
            print("Starting GRG Nonlinear Solver (Excel-like behavior)...")
            
            # Extract variable arrays
            beta_phase = np.array(variable_arrays[0])
            alpha_phase = np.array(variable_arrays[1])
            
            # Initial guess
            x0 = np.concatenate([beta_phase, alpha_phase])
            
            # Bounds for variables
            bounds = [(-5, 5) for _ in range(len(x0))]
            
            # Try different constraint combinations (like Excel does)
            constraint_combinations = [
                # Try with all constraints first
                # {
                #     'name': 'All constraints',
                #     'constraints': [
                #         {'type': 'eq', 'fun': lambda x: phase_correlation_constraint(x, data_range) - 1},
                #         {'type': 'eq', 'fun': lambda x: px_correlation_constraint(x, data_range) - 1},
                #         {'type': 'eq', 'fun': lambda x: sum_of_squares_constraint(x) - 1}
                #     ]
                # },
                {
                    'name': 'Relaxed correlation constraints',
                    'constraints': [
                        {'type': 'ineq', 'fun': lambda x: abs(phase_correlation_constraint(x, data_range) - 1)},
                        {'type': 'ineq', 'fun': lambda x: abs(px_correlation_constraint(x, data_range) - 1)},
                        {'type': 'eq', 'fun': lambda x: sum_of_squares_constraint(x) - 1}
                    ]
                }
            ]
            
            best_result = None
            best_objective = float('-inf') if objective_type == 'max' else float('inf')
            best_constraint_violation = float('inf')
            
            for constraint_set in constraint_combinations:
                print(f"\nTrying constraint set: {constraint_set['name']}")
                
                try:
                    # Objective function
                    if objective_type == 'max':
                        objective_func = lambda x: -correlation_objective(x, data_range)
                    else:
                        objective_func = lambda x: correlation_objective(x, data_range)
                    
                    result = minimize(
                        objective_func,
                        x0,
                        method='SLSQP',
                        bounds=bounds,
                        constraints=constraint_set['constraints'],
                        options={'maxiter': 5000, 'ftol': 1e-30, 'eps': 1e-30, 'disp': False}
                    )
                    
                    if result.success:
                        print(f"✓ Success with {constraint_set['name']}")
                        
                        # Calculate constraint violations
                        x_optimal = result.x
                        phase_correlation_violation = abs(phase_correlation_constraint(x_optimal, data_range) - 1)
                        px_correlation_violation = abs(px_correlation_constraint(x_optimal, data_range) - 1)
                        sum_of_squares_violation = abs(sum_of_squares_constraint(x_optimal) - 1)
                        total_violation = phase_correlation_violation + px_correlation_violation + sum_of_squares_violation
                        
                        objective_value = -result.fun if objective_type == 'max' else result.fun
                        
                        # Store the best result
                        if best_result is None or total_violation < best_constraint_violation:
                            best_result = result
                            best_objective = objective_value
                            best_constraint_violation = total_violation
                            best_constraint_set = constraint_set['name']
                            
                    else:
                        print(f"✗ Failed with {constraint_set['name']}: {result.message}")
                        
                        # Even if failed, check if this result is better than what we have
                        if result.x is not None and len(result.x) == len(x0):
                            x_optimal = result.x
                            phase_correlation_violation = abs(phase_correlation_constraint(x_optimal, data_range) - 1)
                            px_correlation_violation = abs(px_correlation_constraint(x_optimal, data_range) - 1)
                            sum_of_squares_violation = abs(sum_of_squares_constraint(x_optimal) - 1)
                            total_violation = phase_correlation_violation + px_correlation_violation + sum_of_squares_violation
                            
                            objective_value = correlation_objective(x_optimal, data_range)
                            if objective_type == 'max':
                                objective_value = -objective_func(x_optimal)
                            else:
                                objective_value = objective_func(x_optimal)
                            
                            # Accept this result if it has lower constraint violation
                            if total_violation < best_constraint_violation:
                                best_result = result
                                best_objective = objective_value
                                best_constraint_violation = total_violation
                                best_constraint_set = constraint_set['name'] + " (failed but best)"
                                
                except Exception as e:
                    print(f"Error with {constraint_set['name']}: {str(e)}")
                    continue
            
            # Final fallback: simple optimization without constraints
            if best_result is None:
                print("\nTrying unconstrained optimization as final fallback...")
                try:
                    if objective_type == 'max':
                        objective_func = lambda x: -correlation_objective(x, data_range)
                    else:
                        objective_func = lambda x: correlation_objective(x, data_range)
                    
                    result = minimize(
                        objective_func,
                        x0,
                        method='Nelder-Mead',  # Good for unconstrained problems
                        options={'maxiter': 5000, 'disp': False}
                    )
                    
                    if result.x is not None:
                        best_result = result
                        best_objective = -result.fun if objective_type == 'max' else result.fun
                        best_constraint_violation = float('inf')
                        best_constraint_set = "Unconstrained fallback"
                        print("✓ Unconstrained optimization successful")
                except Exception as e:
                    print(f"Unconstrained optimization failed: {str(e)}")
            
            # Prepare results (mimicking Excel's behavior of returning values even if constraints aren't fully satisfied)
            if best_result is not None and best_result.x is not None:
                x_optimal = best_result.x
                
                # Calculate final constraint violations
                final_phase_correlation = phase_correlation_constraint(x_optimal, data_range)
                final_px_correlation = px_correlation_constraint(x_optimal, data_range)
                final_sum_of_squares = sum_of_squares_constraint(x_optimal)
                
                # Split result back into beta and alpha phases
                n_vars = len(beta_phase)
                optimized_beta = x_optimal[:n_vars]
                optimized_alpha = x_optimal[n_vars:]
                
                print(f"\n=== FINAL RESULTS ===")
                print(f"Best solution found using: {best_constraint_set}")
                print(f"Objective value (Phase correlation): {best_objective}")
                print(f"Constraint satisfaction:")
                print(f"  Phase correlation = {final_phase_correlation:.6f} (target: 1.0, deviation: {abs(final_phase_correlation-1):.6f})")
                print(f"  PX correlation = {final_px_correlation:.6f} (target: 1.0, deviation: {abs(final_px_correlation-1):.6f})")
                print(f"  Sum of squares = {final_sum_of_squares:.6f} (target: 1.0, deviation: {abs(final_sum_of_squares-1):.6f})")
                print(f"Total constraint violation: {best_constraint_violation:.6f}")
                
                return {
                    'success': True,
                    'optimized_beta': optimized_beta.tolist(),
                    'optimized_alpha': optimized_alpha.tolist(),
                    'objective_value': best_objective,
                    'constraint_satisfaction': {
                        'Phase correlation': final_phase_correlation,
                        'PX correlation': final_px_correlation, 
                        'Sum of squares': final_sum_of_squares
                    },
                    'constraint_violation': best_constraint_violation,
                    'message': f'Optimization completed (constraints satisfied: {best_constraint_violation < 0.1})'
                }
            else:
                print("All optimization attempts failed. Returning initial values.")
                return {
                    'success': False,
                    'optimized_beta': beta_phase.tolist(),
                    'optimized_alpha': alpha_phase.tolist(),
                    'objective_value': correlation_objective(x0, data_range),
                    'message': 'Optimization failed - returning initial values'
                }

        # Keep the rest of your functions the same (calculate_phase_forecast_values, calculate_px_forecast_values, etc.)
        def calculate_phase_forecast_values(x, data_range):
            """Calculate Phase Forecast values based on the Excel formula"""
            n_vars = len(x) // 2
            beta_phase = x[:n_vars]
            alpha_phase = x[n_vars:]
            col_keys = list(data_range.keys())
            col_keys.remove('current_year_data')
            phase_forecast_values = []
            for i in range(len(data_range['c_data'])):
                phase_forecast_value = 0.0
                
                # # Beta phase part
                for j, col_key in enumerate(col_keys):
                    phase_forecast_value += data_range[col_key][i] * beta_phase[j]

                # # Alpha phase part
                for j, col_key in enumerate(col_keys):
                    phase_forecast_value += data_range[col_key][i] * alpha_phase[j]

                phase_forecast_values.append(phase_forecast_value)
            
            return np.array(phase_forecast_values)

        def calculate_px_forecast_values(x, data_range):
            """Calculate P(X) Forecast values based on the Excel formula"""
            n_vars = len(x) // 2
            beta_phase = x[:n_vars]
            alpha_phase = x[n_vars:]
            
            beta_squares = beta_phase ** 2
            alpha_squares = alpha_phase ** 2
            
            col_keys = list(data_range.keys())
            col_keys.remove('current_year_data')
            px_forecast_values = []
            for i in range(len(data_range['c_data'])):
                px_forecast_value = 0.0
                
                # # Beta squares part
                for j, col_key in enumerate(col_keys):
                    px_forecast_value += data_range[col_key][i] * beta_squares[j]
                
                # # Alpha squares part
                for j, col_key in enumerate(col_keys):
                    px_forecast_value += data_range[col_key][i] * alpha_squares[j]
                
                px_forecast_values.append(px_forecast_value)
            
            return np.array(px_forecast_values)

        def safe_correlation(x, y):
            """Calculate correlation with numerical safety"""
            if len(x) < 2 or len(y) < 2:
                return 0.0
            
            x_clean = np.array(x)[np.isfinite(x)]
            y_clean = np.array(y)[np.isfinite(y)]
            
            min_len = min(len(x_clean), len(y_clean))
            if min_len < 2:
                return 0.0
            
            x_clean = x_clean[:min_len]
            y_clean = y_clean[:min_len]
            
            if np.std(x_clean) < 1e-34 or np.std(y_clean) < 1e-34:
                return 0.0
            
            try:
                correlation = np.corrcoef(x_clean, y_clean)[0, 1]
                return correlation if not np.isnan(correlation) else 0.0
            except:
                return 0.0

        def correlation_objective(x, data_range):
            phase_forecast_values = calculate_phase_forecast_values(x, data_range)
            current_year_values = np.array(data_range['current_year_data'])
            
            return safe_correlation(phase_forecast_values, current_year_values)

        def phase_correlation_constraint(x, data_range):
            return correlation_objective(x, data_range)

        def px_correlation_constraint(x, data_range):
            z_values = calculate_px_forecast_values(x, data_range)
            current_year_values = np.array(data_range['current_year_data'])
            return safe_correlation(z_values, current_year_values)

        def sum_of_squares_constraint(x):
            n_vars = len(x) // 2
            beta_phase = x[:n_vars]
            alpha_phase = x[n_vars:]
            
            sum_beta_squares = np.sum(beta_phase ** 2)
            sum_alpha_squares = np.sum(alpha_phase ** 2)
            
            return sum_beta_squares + sum_alpha_squares

        def run_grg_solver(request):
            try:
                file = request.FILES.get('file')
                if not file:
                    return Response({'success': False, 'message': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Load the uploaded Excel file
                wb = openpyxl.load_workbook(file)
                
                # Create a new workbook for output
                output_wb = openpyxl.Workbook()
                
                for sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    
                    # Create a new sheet in output workbook with the same name
                    output_ws = output_wb.create_sheet(title=sheet_name)
                    if sheet_name == wb.sheetnames[0]:
                        output_wb.active = output_ws
                    
                    # Copy all data from original sheet to output sheet
                    for row in ws.iter_rows():
                        for cell in row:
                            output_ws[cell.coordinate].value = cell.value
                    
                    # Get values for solver
                    # find the value in Phase Correlation column
                    cell_value_phase_correlation = None
                    values_Beta_phase_list = []
                    values_Alpha_phase_list = []
                    
                    count_years = 0
                    for column in range(3, ws.max_column - 13):
                        year_cell = ws.cell(row=1, column=column)
                        if year_cell.value is not None:
                            count_years += 1
                    column_beta_phase = None
                    column_alpha_phase = None
                    column_phase_correlation = None
                    for column in range(1, ws.max_column + 1):
                        title_cell = ws.cell(row=1, column=column)
                        if title_cell.value == 'Phase Correlation':
                            column_phase_correlation = column
                            cell_value_phase_correlation = ws.cell(row=2, column=column).value
                        if title_cell.value == 'Beta Phase':
                            column_beta_phase = column
                            for row in range(2, count_years + 2):
                                cell = ws.cell(row=row, column=column_beta_phase)
                                values_Beta_phase_list.append(cell.value or 0.0)
                        if title_cell.value == 'Alpha Phase':
                            column_alpha_phase = column
                            for row in range(2, count_years + 2):
                                cell = ws.cell(row=row, column=column_alpha_phase)
                                values_Alpha_phase_list.append(cell.value or 0.0)
                    
                    print("values_Beta_phase_list:::", values_Beta_phase_list.__len__())
                    print("values_Alpha_phase_list:::", values_Alpha_phase_list.__len__())
                    
                    # Extract data ranges needed for calculations
                    data_range = extract_data_ranges(ws, count_years)
                    
                    # Run GRG solver
                    result = grg_nonlinear_solver(
                        objective_cell=cell_value_phase_correlation,
                        variable_arrays=[values_Beta_phase_list, values_Alpha_phase_list],
                        data_range=data_range,
                        objective_type='max'
                    )
                    print("result:::", result)
                    if result['success']:
                        print("Optimization successful! Updating worksheet...")
                        
                        # Update the output worksheet with optimized values
                        for i, row in enumerate(range(2, count_years + 2)):
                            output_ws.cell(row=row, column=column_beta_phase).value = result['optimized_beta'][i]
                        
                        for i, row in enumerate(range(2, count_years + 2)):
                            output_ws.cell(row=row, column=column_alpha_phase).value = result['optimized_alpha'][i]
                        
                        output_ws.cell(row=2, column=column_phase_correlation).value = result['objective_value']
                        
                        # Recalculate dependent cells
                        recalculate_dependent_cells(output_ws, result['optimized_beta'], result['optimized_alpha'], count_years)
                    else:
                        print("Optimization failed:", result['message'])
                
                # Remove default sheet created by openpyxl
                if 'Sheet' in output_wb.sheetnames:
                    output_wb.remove(output_wb['Sheet'])
                
                # Save the optimized workbook
                output_io = io.BytesIO()
                output_wb.save(output_io)
                output_io.seek(0)
                
                # Save file to local
                filename = "processed_data_with_function.xlsx"
                path = pathByDate()
                relative_path = os.path.join('uploads', path, filename)
                full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'wb') as f:
                    f.write(output_io.getvalue())
                
                # Return the optimized file
                print("relative_path:::", relative_path)
                return relative_path
                
            except Exception as e:
                print(f"Error: {str(e)}")
                return None

        def extract_data_ranges(ws, count_years):
            """
            Extract actual data ranges from the worksheet for correlation calculations
            """
            data_range = {}
            
            columns_to_extract = {}
            for column in range(3, count_years * 2 + 2):
                col_letter = get_column_letter(column).lower()
                if column % 2 == 1:
                    columns_to_extract[f"{col_letter}_data"] = column

            for key, col in columns_to_extract.items():
                data = []
                for row in range(2, ws.max_row + 1):
                    cell_value = ws.cell(row=row, column=col).value
                    data.append(cell_value if cell_value is not None else 0.0)
                data_range[key] = data
            
            current_year_data = []
            for row in range(2, ws.max_row + 1):
                cell_value = ws.cell(row=row, column=count_years * 2 + 4).value 
                current_year_data.append(cell_value if cell_value is not None else 0.0)
            data_range['current_year_data'] = current_year_data
            
            print(f"Extracted data ranges: {len(data_range['c_data'])} rows")
            return data_range

        def recalculate_dependent_cells(ws, optimized_beta, optimized_alpha, count_years):
            """
            Recalculate dependent cells after optimization
            """
            for i, row in enumerate(range(2, count_years + 2)):
                ws.cell(row=row, column=ws.max_column - 4).value = optimized_beta[i] ** 2
                ws.cell(row=row, column=ws.max_column - 1).value = optimized_alpha[i] ** 2
            
            # Recalculate sums of squares
            print("ws.max_column - 4:::", ws.max_column - 4)
            print("ws.max_column - 1:::", ws.max_column - 1)

            ws.cell(row=count_years+2, column=ws.max_column - 4).value = sum([optimized_beta[i] ** 2 for i in range(count_years)])
            ws.cell(row=count_years+2, column=ws.max_column - 1).value = sum([optimized_alpha[i] ** 2 for i in range(count_years)])
            
            # Recalculate all sum of squares
            ws.cell(row=count_years+2, column=ws.max_column).value = ws.cell(row=count_years+2, column=ws.max_column - 4).value + ws.cell(row=count_years+2, column=ws.max_column - 1).value
            
            print("Recalculated dependent cells")

        try:
            relative_path = run_grg_solver(request)
            if relative_path:
                return Response({
                    'success': True,
                    'file_path':  f"http://localhost:8000/media/{relative_path}",
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Failed to run GRG solver'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

