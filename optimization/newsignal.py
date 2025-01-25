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
            
            # Send the processed data to the AI Proxy for report generation
            ai_response = generate_report_from_ai(df)

            # If AI response is successful, save the report as a PDF
            if ai_response:
                pdf_file_path = save_report_as_pdf(ai_response)
                return jsonify({'report_pdf': pdf_file_path}), 200
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
    """
    Generate a report from the AI proxy service by sending a request with the data.
    """
    # Prepare a more concise description of the data (without the table itself)
    prompt = f"Analyze the following traffic data and generate a summary report with insights only about signals do not provide details about traffic:\n\n" \
             f"The dataset includes columns like 'Vehicle Count' 'Average Speed', congestion level, signal control and other traffic-related metrics." \
             f" Please provide a summary report based on this data without including the table."
    
    payload = {
        "model": "gpt-4o-mini",  # Example model, change it based on your service
        "messages": [{"role": "user", "content": prompt}],
    }
    
    # Send the request to the AI Proxy
    try:
        response = requests.post(AI_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Get the AI's response (assuming it returns the generated text in 'choices[0].message.content')
        ai_response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if ai_response:
            # Remove '*' and '#' characters from the AI response
            ai_response_cleaned = ai_response.replace('*', '').replace('#', '')
            return ai_response_cleaned
        else:
            app.logger.error('No response from AI')
            return None

    except requests.exceptions.RequestException as e:
        app.logger.error(f"AI Proxy request error: {e}")
        return None


def save_report_as_pdf(report_text):
    """
    Save the AI-generated report as a PDF file.
    """
    # Create a PDF document
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Set font
    pdf.set_font("Arial", size=12)
    
    # Add title
    pdf.cell(200, 10, txt="Traffic Data Analysis Report", ln=True, align='C')
    
    # Add report text
    pdf.ln(10)  # Add a line break
    pdf.multi_cell(0, 10, report_text)

    # Save the PDF to a file
    pdf_file_path = os.path.join(UPLOAD_FOLDER, 'ai_report.pdf')
    pdf.output(pdf_file_path)
    
    return pdf_file_path


if __name__ == '__main__':
    app.run(debug=True)
