from flask import Flask, render_template, request, jsonify
import pandas as pd
from data_retrieve import df, biblios
import gspread
from google.oauth2.service_account import Credentials

# Connect to Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file("../money-all-you-need-demo-ea9c81c50eee.json", scopes=SCOPES)
client = gspread.authorize(creds)

# Open spreadsheet uding Google API
SHEET_NAME = "dummy_data"
sheet = client.open(SHEET_NAME)
corrections_tab = sheet.worksheet("User_Corrections")

app = Flask(__name__)

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
    elif name not in biblios:
        return jsonify({'error': 'Name not in database'})
    else:
        if len(biblios[name]) == 0:
            return jsonify({'error': 'Your name is in our database, but no papers came up.'})

    papers = [{'index': idx, 'title': title} for idx, title in biblios[name]]
    return jsonify({'papers': papers})

# Retrieve the selected paper's details.
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

    # Optional: rename keys to match what your JS expects
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

    row = [
        paper_index,
        user_name,
        corrections.get("GPU Number", "N/A"),
        corrections.get("GPU Type", "N/A"),
        corrections.get("GPU Storage", "N/A"),
        corrections.get("Inference Time", "N/A"),
        corrections.get("LLM(s) FineTuning", "N/A"),
        corrections.get("LLM(s) Evaluation", "N/A"),
        corrections.get("API Cost", "N/A"),
        corrections.get("Funding Resource", "N/A"),
        corrections.get("Funding Type", "N/A")
    ]

    # Append to the corrections tab
    corrections_tab.append_row(row)

    print("Added correction:", row)
    return jsonify({'success': True, 'message': 'Correction submitted successfully'})

if __name__ == '__main__':
    app.run(debug=True)