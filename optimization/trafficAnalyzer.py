import logging
from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
import requests  # Import requests to interact with the AI proxy
from fpdf import FPDF  # For generating PDF reports

app = Flask(__name__)

# Enable Flask logging
app.logger.setLevel(logging.DEBUG)

# Set a folder to store uploaded CSV files (you can change this path)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# AI Proxy Token and URL for sending requests
AIPROXY_TOKEN = 'eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDQ5MDRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.1C8QpqZCx1Ik1aTaMlGHq26IJpupgdDAuOd1vEW7-_o'
AI_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {AIPROXY_TOKEN}",
    "Content-Type": "application/json"
}

@app.route('/process_csv', methods=['POST'])
def process_csv():
    if 'file' not in request.files:
        app.logger.error('No file part in the request.')
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        app.logger.error('No file selected.')
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            app.logger.debug(f'File saved at {file_path}')
            
            # Try specifying a different encoding when reading the CSV file
            df = pd.read_csv(file_path, sep=',', encoding='utf-8')  # or use encoding='utf-16' if utf-8 still causes issues

            app.logger.debug('CSV file read successfully.')
            
            df.columns = df.columns.str.strip()
            app.logger.debug(f'Column names cleaned: {df.columns}')
            
            df['Vehicle Count'] = pd.to_numeric(df['Vehicle Count'], errors='coerce')
            df['Average Speed'] = pd.to_numeric(df['Average Speed'], errors='coerce')
            app.logger.debug('Converted columns to numeric values.')
            
            df['Vehicle Count'] = df['Vehicle Count'].fillna(df['Vehicle Count'].mean())
            df['Average Speed'] = df['Average Speed'].fillna(df['Average Speed'].mean())
            app.logger.debug('Filled missing values with mean.')
            
            df['Congestion Level'] = df['Average Speed'].apply(lambda x: 'High' if x >= 40 else 'Low')
            app.logger.debug('Congestion level added based on average speed.')
            
            def signal_control(row):
                return "Extend Green Light" if row['Congestion Level'] == 'High' else "Normal Green Light"
            
            df['Signal Control'] = df.apply(signal_control, axis=1)
            app.logger.debug('Signal control applied.')
            
            output_file_path = os.path.join(UPLOAD_FOLDER, 'processed_' + file.filename)
            df.to_csv(output_file_path, index=False)
            app.logger.debug(f'Processed file saved at {output_file_path}')
            
            ai_response = generate_report_from_ai(df)

            # When generating the report
            ai_response = generate_report_from_ai(df)
            
            if ai_response:
                # Pass the original filename (file.filename) to the save report functions
                pdf_file_path = save_report_as_pdf(ai_response, file.filename)
                txt_file_path = save_report_as_txt(ai_response, file.filename)
                
                return jsonify({'report_pdf': pdf_file_path, 'report_txt': txt_file_path}), 200
            else:
                return jsonify({'error': 'Failed to generate report'}), 500


        except pd.errors.ParserError as e:
            app.logger.error(f'CSV parsing error: {e}')
            return jsonify({'error': 'Error parsing CSV file: ' + str(e)}), 500
        except Exception as e:
            app.logger.error(f'Error processing file: {e}')
            return jsonify({'error': 'Error processing the file: ' + str(e)}), 500
    else:
        app.logger.error('Invalid file format. Expected a CSV file.')
        return jsonify({'error': 'Invalid file format. Please upload a CSV file.'}), 400


def generate_report_from_ai(df):
    prompt = f"Analyze the following traffic data and generate a summary report with insights only about traffic do not provide details about signals:\n\n" \
             f"The dataset includes columns like 'Vehicle Count', 'Average Speed', congestion level, signal control and other traffic-related metrics." \
             f" Please provide a summary report based on this data without including the table."
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
    }
    
    try:
        response = requests.post(AI_URL, json=payload, headers=headers)
        response.raise_for_status()

        ai_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if ai_response:
            ai_response_cleaned = ai_response.replace('*', '').replace('#', '')
            return ai_response_cleaned
        else:
            app.logger.error('No response from AI')
            return None

    except requests.exceptions.RequestException as e:
        app.logger.error(f"AI Proxy request error: {e}")
        return None


def save_report_as_pdf(report_text, input_filename):
    # Extract the base filename without extension
    base_filename = os.path.splitext(input_filename)[0]
    
    # Define the path for the PDF file
    pdf_file_path = os.path.join(UPLOAD_FOLDER, f'{base_filename}_report.pdf')
    
    # Create the PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Traffic Data Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, report_text)

    # Save the PDF to the specified path
    pdf.output(pdf_file_path)
    
    return pdf_file_path


def save_report_as_txt(report_text, input_filename):
    # Extract the base filename without extension
    base_filename = os.path.splitext(input_filename)[0]
    
    # Define the path for the TXT file
    txt_file_path = os.path.join(UPLOAD_FOLDER, f'{base_filename}_report.txt')
    
    # Save the report text to the TXT file
    with open(txt_file_path, 'w') as txt_file:
        txt_file.write(report_text)
    
    return txt_file_path


from flask import render_template

@app.route('/show_report/<filename>', methods=['GET'])
def show_report(filename):
    # Construct the path to the .txt file
    txt_file_path = os.path.join(UPLOAD_FOLDER, f'{filename}_report.txt')
    
    try:
        # Open and read the content of the txt file
        with open(txt_file_path, 'r') as file:
            report_content = file.read()
        
        # Render the content in an HTML page
        return render_template('report_page.html', report_content=report_content)
    
    except FileNotFoundError:
        return jsonify({'error': 'Report file not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
