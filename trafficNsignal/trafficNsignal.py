import logging
from flask import Flask, request, jsonify, send_file
import pandas as pd
import os

app = Flask(__name__)

# Enable Flask logging
app.logger.setLevel(logging.DEBUG)

# Set a folder to store uploaded CSV files (you can change this path)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/process_csv', methods=['POST'])
def process_csv():
    # Ensure the file is part of the request
    if 'file' not in request.files:
        app.logger.error('No file part in the request.')
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        app.logger.error('No file selected.')
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            # Get the original file path (this will be saved temporarily)
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            
            # Save the uploaded file temporarily in the UPLOAD_FOLDER
            file.save(file_path)
            app.logger.debug(f'File saved at {file_path}')
            
            # Read the CSV into a DataFrame
            df = pd.read_csv(file_path, sep=',')
            app.logger.debug('CSV file read successfully.')
            
            # Clean the column names
            df.columns = df.columns.str.strip()
            app.logger.debug(f'Column names cleaned: {df.columns}')
            
            # Convert 'Vehicle Count' and 'Average Speed' to numeric, handling errors
            df['Vehicle Count'] = pd.to_numeric(df['Vehicle Count'], errors='coerce')
            df['Average Speed'] = pd.to_numeric(df['Average Speed'], errors='coerce')
            app.logger.debug('Converted columns to numeric values.')
            
            # Fill missing values with the column's mean
            df['Vehicle Count'] = df['Vehicle Count'].fillna(df['Vehicle Count'].mean())
            df['Average Speed'] = df['Average Speed'].fillna(df['Average Speed'].mean())
            app.logger.debug('Filled missing values with mean.')
            
            # Feature Engineering: Create a congestion level
            df['Congestion Level'] = df['Average Speed'].apply(lambda x: 'High' if x >= 40 else 'Low')
            app.logger.debug('Congestion level added based on average speed.')
            
            # Apply signal control logic
            def signal_control(row):
                return "Extend Green Light" if row['Congestion Level'] == 'High' else "Normal Green Light"
            
            df['Signal Control'] = df.apply(signal_control, axis=1)
            app.logger.debug('Signal control applied.')
            
            # Save the result in the same folder with a new name (e.g., prefix 'processed_')
            output_file_path = os.path.join(UPLOAD_FOLDER, 'processed_' + file.filename)
            df.to_csv(output_file_path, index=False)
            app.logger.debug(f'Processed file saved at {output_file_path}')
            
            # Return the updated file as a download link
            return send_file(output_file_path, as_attachment=True)
        
        except pd.errors.ParserError as e:
            app.logger.error(f'CSV parsing error: {e}')
            return jsonify({'error': 'Error parsing CSV file: ' + str(e)}), 500
        except Exception as e:
            app.logger.error(f'Error processing file: {e}')
            return jsonify({'error': 'Error processing the file: ' + str(e)}), 500
    else:
        app.logger.error('Invalid file format. Expected a CSV file.')
        return jsonify({'error': 'Invalid file format. Please upload a CSV file.'}), 400


if __name__ == '__main__':
    app.run(debug=True)
