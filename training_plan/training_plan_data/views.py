from django.contrib import messages
from django.shortcuts import redirect, render
from .models import SheetData
import sys
import os
import pandas as pd
from datetime import datetime
import traceback
import re 
from django.http import JsonResponse

def training_data_api(request):
    """API endpoint for React to fetch training data"""
    data = list(SheetData.objects.all().order_by('date').values(
        'id', 'day', 'date', 'time_session_1', 'session_1', 'time_session_2', 'session_2'
    ))
    
    # Convert date objects to strings for JSON serialization
    for item in data:
        if 'date' in item:
            item['date'] = item['date'].isoformat()
    
    return JsonResponse(data, safe=False)

def home(request):
    return render(request, 'home.html')

def training_plan(request):
    # Handle form submission for manual import
    if request.method == 'POST' and 'import_data' in request.POST:
        try:
            # Import data using the import script
            rows_imported = import_training_data(clear_existing=True)
            messages.success(request, f"Training data imported successfully! {rows_imported} rows imported.")
        except Exception as e:
            messages.error(request, f"Error importing data: {str(e)}")
            print(f"Error during manual import: {e}")
            traceback.print_exc()
        return redirect('training_plan_data:home')
    
    # Auto-refresh data on every page load
    try:
        print("Automatically refreshing data from Google Sheet...")
        rows_imported = import_training_data(clear_existing=True)
        if rows_imported > 0:
            print(f"Auto-imported {rows_imported} rows")
        else:
            print("No data imported during auto-refresh")
    except Exception as e:
        print(f"Error during auto-refresh: {e}")
        traceback.print_exc()
    
    # Get the latest data
    training_data = SheetData.objects.all().order_by('date')
    
    # Simple count print - keeping this one for basic diagnostics
    print(f"Found {training_data.count()} training data records")
    
    # Pass current date to the template to highlight today's record
    context = {
        'training_data': training_data,
        'current_date': datetime.now().date(),
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return render(request, 'training_plan.html', context)

def import_training_data(clear_existing=True):
    """
    Import rowing training data from Google Sheet
    
    Args:
        clear_existing: Whether to delete existing data before import
    
    Returns:
        int: Number of rows imported
    """
    html_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vT9uvJ4kDJLBTZ_9jzQDZyiLGnoiykRH5Elgn9MJaDWNoSaiLaOiHPsctOxhuWNyQ5eyUbH6vM-RqoM/pubhtml'
    
    print(f"Fetching data from: {html_url}")
    
    try:
        # Clear existing data if requested
        if clear_existing:
            deleted_count = SheetData.objects.all().delete()
            print(f"Cleared {deleted_count[0]} existing records")
        
        # Fetch the HTML tables from the URL
        dfs = pd.read_html(html_url)
        if not dfs:
            print("No tables found in the published sheet")
            return 0
            
        print(f"Found {len(dfs)} tables in the HTML")
        
        # Take the first table and inspect it
        df = dfs[0]
        print(f"Original DataFrame shape: {df.shape}")
        
        # Find the actual header row (the row with 'Day', 'Date', etc.)
        header_row_idx = None
        for idx, row in df.iterrows():
            row_values = [str(val).strip() for val in row.values]
            if 'Day' in row_values and 'Date' in row_values:
                header_row_idx = idx
                print(f"Found header row at index {idx}")
                break
        
        if header_row_idx is None:
            print("Could not find a header row with 'Day' and 'Date'")
            return 0
        
        # Extract the column names from the header row
        header = df.iloc[header_row_idx].values
        
        # Get the data rows (everything after the header)
        data_df = df.iloc[header_row_idx+1:].reset_index(drop=True)
        
        # Assign the column names
        data_df.columns = header
        
        # Clean up column names
        data_df.columns = [str(col).strip() for col in data_df.columns]
        
        # Print the processed data
        print(f"Processed DataFrame shape: {data_df.shape}")
        print("Column names:", data_df.columns.tolist())
        
        def clean_value(val):
            """Basic cleaning of values to handle None, NaN and pandas Series metadata"""
            if val is None:
                return ''
            
            val_str = str(val).strip()
            if val_str.lower() in ('nan', 'none', 'null'):
                return ''
            
            # Strip out pandas Series metadata (Name: X, dtype: object)
            metadata_pattern = r'\s*Name:\s*\d+,\s*dtype:\s*\w+\s*$'
            cleaned_val = re.sub(metadata_pattern, '', val_str)
            
            # Log the change if any
            if cleaned_val != val_str:
                print(f"Cleaned metadata: '{val_str}' → '{cleaned_val}'")
            
            return cleaned_val
        
        # Function to analyze column structure and find the most likely columns
        def identify_columns(df):
            """ 
            Analyze dataframe to identify day, date, time and session columns
            even if column names change
            
            Returns:
                dict: Dictionary of identified columns
            """
            columns = {
                'day_col': None,
                'date_col': None,
                'time_cols': [],
                'session_cols': []
            }
            
            # First try to identify by column name
            for col in df.columns: 
                col_str = str(col).lower()
                
                if col_str == 'day':
                    columns['day_col'] = col
                elif col_str == 'date':
                    columns['date_col'] = col
                elif 'time' in col_str:
                    columns['time_cols'].append(col)
                elif 'session' in col_str:
                    columns['session_cols'].append(col)
            
            # If we couldn't find by name, try to identify by content pattern
            if not columns['day_col'] or not columns['date_col']:
                print("Couldn't find day/date columns by name, trying content pattern...")
                
                # Sample first few rows to identify column types
                for col in df.columns:
                    sample = [str(val).strip().lower() for val in df[col].head(5) if str(val).strip()]
                    
                    # Check for day of week pattern
                    if not columns['day_col'] and any(day in ' '.join(sample) 
                                                      for day in ['monday', 'tuesday', 'wednesday', 'thursday', 
                                                                 'friday', 'saturday', 'sunday']):
                        columns['day_col'] = col
                    
                    # Check for date pattern
                    if not columns['date_col'] and any(re.search(r'\d{1,2}[/-]\d{1,2}', str(val)) for val in sample):
                        columns['date_col'] = col
            
            # If we still couldn't find time/session columns, try content pattern
            if not columns['time_cols'] or not columns['session_cols']:
                print("Analyzing column content to identify time and session columns...")
                
                for col in df.columns:
                    if col not in [columns['day_col'], columns['date_col']]:
                        # Sample values
                        sample = [str(val).strip().lower() for val in df[col].head(5) if str(val).strip()]
                        sample_text = ' '.join(sample)
                        
                        # Check for time patterns
                        time_patterns = [':', 'off', 'own time', 'scp']
                        session_patterns = ['mins', 'paddle', 'ut2', 'rest', 'weight']
                        
                        if any(pattern in sample_text for pattern in time_patterns) and col not in columns['time_cols']:
                            columns['time_cols'].append(col)
                        
                        if any(pattern in sample_text for pattern in session_patterns) and col not in columns['session_cols']:
                            columns['session_cols'].append(col)
            
            # Sort time and session columns to ensure consistent order
            columns['time_cols'].sort()
            columns['session_cols'].sort()
            
            print(f"Identified columns: {columns}")
            return columns
        
        # Identify the key columns
        columns = identify_columns(data_df)
        
        if not columns['day_col'] or not columns['date_col']:
            print("Could not identify essential Day and Date columns")
            return 0
        
        # Import the data
        rows_imported = 0
        for idx, row in data_df.iterrows():
            try:
                # Skip rows without a day value
                day_val = clean_value(row.get(columns['day_col'], ''))
                if not day_val:
                    continue
                
                # Parse the date
                date_str = clean_value(row.get(columns['date_col'], ''))
                if not date_str:
                    print(f"Skipping row {idx}: No date value")
                    continue
                
                try:
                    # Try different date formats with dayfirst=True for UK format
                    date_obj = pd.to_datetime(date_str, dayfirst=True, errors='raise')
                except Exception as e:
                    print(f"Error parsing date '{date_str}' in row {idx}: {e}")
                    continue
                
                # Get morning time - just take raw value without processing
                # Get time session(s) from a single time column (split if needed)
                time_session_1 = ''
                time_session_2 = ''

                if columns['time_cols']:
                    raw_time = row.get(columns['time_cols'][0], '')
                    cleaned_time = clean_value(raw_time)
                    
                    # Try to split the time string if multiple times are present
                    time_parts = re.split(r'\s*[\/,&]| to |\s+-\s+|\s*\n\s*', cleaned_time)
                    time_parts = [part.strip() for part in time_parts if part.strip()]
                    
                    if time_parts:
                        time_session_1 = time_parts[0]
                        if len(time_parts) > 1:
                            time_session_2 = time_parts[1]
                    
                    print(f"Raw time: '{raw_time}' → Split: {time_parts}")
                    print(f"  Morning time: {time_session_1}")
                    print(f"  Afternoon time: {time_session_2}")
                    
                time_session_1 = time_session_1.replace('Time ', '')
                time_session_2 = time_session_2.replace('Time ', '')
                
                time_session_1 = time_session_1.replace('NaN', '')
                time_session_2 = time_session_2.replace('NaN', '')
                
                # Get morning session - just take raw value without processing
                session_1 = ''
                if columns['session_cols'] and len(columns['session_cols']) > 0:
                    raw_session_1 = row.get(columns['session_cols'][0], '')
                    session_1 = clean_value(raw_session_1)
                    print(f"Morning session: raw='{raw_session_1}', cleaned='{session_1}'")

                # Get afternoon session - just take raw value without processing
                session_2 = ''
                if columns['session_cols'] and len(columns['session_cols']) > 1:
                    raw_session_2 = row.get(columns['session_cols'][1], '')
                    session_2 = clean_value(raw_session_2)
                    print(f"Afternoon session: raw='{raw_session_2}', cleaned='{session_2}'")
                
                # Create the database record with raw values
                SheetData.objects.create(
                    day=day_val,
                    date=date_obj.date(),
                    time_session_1=time_session_1,
                    session_1=session_1,
                    time_session_2=time_session_2,
                    session_2=session_2
                )
                rows_imported += 1
                
            except Exception as e:
                print(f"Error importing row {idx}: {e}")
                print(f"Row data: {row}")
                traceback.print_exc()
        
        print(f"\nImport complete. Total rows imported: {rows_imported}")
        return rows_imported
        
    except Exception as e:
        print(f"Error during import: {e}")
        traceback.print_exc()
        return 0