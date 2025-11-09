from flask import Flask, render_template, request, jsonify
import pandas as pd
from data_retrieve import df, biblios
import gspread
import os, json
from google.oauth2.service_account import Credentials

# Connect to Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# # * This is for hosting on Render. Ignore this if running locally. *
# creds_info = json.loads(os.environ["GOOGLE_API_KEY"])
# creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

creds = Credentials.from_service_account_file("money-all-you-need-demo-ea9c81c50eee.json", scopes=SCOPES)

client = gspread.authorize(creds)

# Open spreadsheet uding Google API
SHEET_NAME = "data_overview_3_9"
sheet = client.open(SHEET_NAME)
corrections_tab = sheet.worksheet("User_Corrections")

app = Flask(__name__)

# Pre-load name:paper map for case-insensitive queries
biblios_lower = {k.lower(): k for k in biblios.keys()}

# Render `search.html` file when 
@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/')
def index_page():
    return render_template('index.html')

# Return a list of the user's papers when they search their name.
@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': 'No name provided'}), 400

    key = biblios_lower.get(name.lower())
    if key is None:
        return jsonify({'error': 'Name not in database'})

    papers_list = biblios[key]
    if len(papers_list) == 0:
        return jsonify({'error': 'Your name is in our database, but no papers came up.'})

    papers = [{'index': idx, 'title': title} for idx, title in papers_list]
    return jsonify({'papers': papers, 'name': key})

# Retrieve the selected paper's information.
@app.route('/paper_details', methods=['POST'])
def paper_details():
    data = request.get_json()
    idx = data.get('index')

    if idx is None:
        return jsonify({'error': 'No paper index provided'}), 400
    if idx < 0 or idx >= len(df):
        return jsonify({'error': 'Invalid paper index'}), 404

    row = df.iloc[idx]

    fields = [
        "title", "authors", "year", "GPU Number", "GPU Type", "GPU Storage",
        "Inference time", "LLM(s) FineTuning", "LLM(s) Evaluation",
        "API Cost (i.e. model testing, and iterative retraining)",
        "Funding Resource", "Funding Type"
    ]

    paper_info = {}
    for f in fields:
        v = row.get(f)
        if pd.isna(v) or v is None or v == " ":
            paper_info[f] = "N/A"
        else:
            paper_info[f] = str(v)

    paper_info = {
        "Title": paper_info.get("title"),
        "Authors": paper_info.get("authors"),
        "Year": paper_info.get("year"),
        "GPU Number": paper_info.get("GPU Number"),
        "GPU Type": paper_info.get("GPU Type"),
        "GPU Storage": paper_info.get("GPU Storage"),
        "Inference Time": paper_info.get("Inference time"),
        "LLM(s) FineTuning": paper_info.get("LLM(s) FineTuning"),
        "LLM(s) Evaluation": paper_info.get("LLM(s) Evaluation"),
        "API Cost": paper_info.get("API Cost (i.e. model testing, and iterative retraining)"),
        "Funding Resource": paper_info.get("Funding Resource"),
        "Funding Type": paper_info.get("Funding Type")
    }
    return jsonify(paper_info)

# Receive user's corrections
@app.route('/submit_corrections', methods=['POST'])
def submit_corrections():
    data = request.get_json()
    paper_index = data.get('paper_index')
    corrections = data.get('corrections', {})
    user_name = data.get('user_name', 'Anonymous')

    if paper_index is None:
        return jsonify({'error': 'No paper index provided'}), 400

    # Check if "No GPUs Used" was submitted
    if corrections.get("GPU Number") == "0" and corrections.get("GPU Type") == "None" and corrections.get("GPU Storage") == "0":
        row = [
            paper_index,
            user_name,
            "0",  # GPU Number
            "None",  # GPU Type
            "0",  # GPU Storage
            "N/A",  # Inference Time
            corrections.get("GPU CHECKED", "N/A"),
            corrections.get("LLM(s) FineTuning", "N/A"),
            corrections.get("LLM(s) Evaluation", "N/A"),
            corrections.get("LLM CHECKED", "N/A"),
            corrections.get("API Cost", "N/A"),
            corrections.get("Funding Resource", "N/A"),
            corrections.get("Funding Type", "N/A"),
            corrections.get("Funding CHECKED", "N/A"),
            corrections.get("Share any additional comments below:", "N/A")
        ]
        corrections_tab.append_row(row)
        return jsonify({'success': True, 'message': 'Correction submitted successfully'})

    # Extract GPU data - find all indexed GPU entries
    gpu_entries = {}
    for key, value in corrections.items():
        if key.startswith('GPU Type '):
            index = key.split(' ')[-1]
            if index not in gpu_entries:
                gpu_entries[index] = {}
            gpu_entries[index]['type'] = value
        elif key.startswith('GPU Number '):
            index = key.split(' ')[-1]
            if index not in gpu_entries:
                gpu_entries[index] = {}
            gpu_entries[index]['number'] = value
        elif key.startswith('GPU Storage '):
            index = key.split(' ')[-1]
            if index not in gpu_entries:
                gpu_entries[index] = {}
            gpu_entries[index]['storage'] = value
        elif key.startswith('Inference Time '):
            index = key.split(' ')[-1]
            if index not in gpu_entries:
                gpu_entries[index] = {}
            gpu_entries[index]['inference_time'] = value

    # If no GPU entries found, add one row with N/A
    if not gpu_entries:
        row = [
            paper_index,
            user_name,
            "N/A",  # GPU Number
            "N/A",  # GPU Type
            "N/A",  # GPU Storage
            "N/A",  # Inference Time
            corrections.get("GPU CHECKED", "N/A"),
            corrections.get("LLM(s) FineTuning", "N/A"),
            corrections.get("LLM(s) Evaluation", "N/A"),
            corrections.get("LLM CHECKED", "N/A"),
            corrections.get("API Cost", "N/A"),
            corrections.get("Funding Resource", "N/A"),
            corrections.get("Funding Type", "N/A"),
            corrections.get("Funding CHECKED", "N/A"),
            corrections.get("Share any additional comments below:", "N/A")
        ]
        corrections_tab.append_row(row)
    else:
        # Add one row per GPU type
        for _, gpu_data in gpu_entries.items():
            row = [
                paper_index,
                user_name,
                gpu_data.get('number', 'N/A'),
                gpu_data.get('type', 'N/A'),
                gpu_data.get('storage', 'N/A'),
                gpu_data.get('inference_time', 'N/A'),
                corrections.get("GPU CHECKED", "N/A"),  # Add this
                corrections.get("LLM(s) FineTuning", "N/A"),
                corrections.get("LLM(s) Evaluation", "N/A"),
                corrections.get("LLM CHECKED", "N/A"),  # Add this
                corrections.get("API Cost", "N/A"),
                corrections.get("Funding Resource", "N/A"),
                corrections.get("Funding Type", "N/A"),
                corrections.get("Funding CHECKED", "N/A"),  # Add this
                corrections.get("Share any additional comments below:", "N/A")
            ]
            corrections_tab.append_row(row)

    return jsonify({'success': True, 'message': 'Correction submitted successfully'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)