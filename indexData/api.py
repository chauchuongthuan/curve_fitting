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
                
                # Copy titles from B1 to max_column
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
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)