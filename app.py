from flask import Flask, render_template, request, jsonify
import pandas as pd
from data_retrieve import df, biblios, paper_updates, author_to_paper, paper_tracker, SHEET_URL, CORRECTIONS_URL
import gspread
import os, json
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import pytz
import threading

# Connect to Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# * FOR HOSTING ON RENDER *
creds_info = json.loads(os.environ["GOOGLE_API_KEY"])
creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)

# # * FOR RUNNING LOCALLY *
# creds = Credentials.from_service_account_file("money-all-you-need-demo-ea9c81c50eee.json", scopes=SCOPES)

client = gspread.authorize(creds)

# Open spreadsheet uding Google API
SHEET_NAME = "data_overview_3_9"
sheet = client.open(SHEET_NAME)
corrections_tab = sheet.worksheet("User_Corrections")

app = Flask(__name__)

# Pre-load name:paper map for case-insensitive queries
biblios_lower = {k.lower(): k for k in biblios.keys()}

from datetime import datetime, timedelta

# Cache variables
data_cache = {
    'df': None,
    'df_corrections': None,
    'paper_updates': None,
    'biblios': None,
    'last_updated': None
}
CACHE_DURATION = timedelta(minutes=5)  # Cache for 5 minutes

def get_fresh_data():
    """Get data from cache or reload if cache is stale"""
    global data_cache
    
    now = datetime.now()
    
    # Check if cache is valid
    if (data_cache['last_updated'] is None or 
        now - data_cache['last_updated'] > CACHE_DURATION):
        
        # Reload data
        print("Reloading data from Google Sheets...")
        data_cache['df'] = pd.read_csv(SHEET_URL)
        data_cache['df_corrections'] = pd.read_csv(CORRECTIONS_URL)
        data_cache['biblios'] = author_to_paper(data_cache['df'])
        data_cache['paper_updates'] = paper_tracker(data_cache['df'], data_cache['df_corrections'])
        data_cache['last_updated'] = now
        print("Data reloaded successfully")
    
    return data_cache['paper_updates']

# Initialize cache on startup
print("Initializing data cache on startup...")
get_fresh_data()
print("Cache initialized")


# Render `search.html` file. 
@app.route('/search')
def search_page():
    return render_template('search.html')


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/community')
def community_page():
    return render_template('community.html')


# Return name suggestions
@app.route('/suggest_names', methods=['POST'])
def suggest_names():
    data = request.get_json()
    query = data.get('query', '').strip().lower()
    
    if not query:
        return jsonify({'suggestions': []})
    
    # Filter names that contain the query string (case-insensitive)
    matching_names = [
        name for name in biblios.keys() 
        if query in name.lower()
    ]
    
    # Limit to top 10 suggestions, sorted alphabetically
    matching_names = sorted(matching_names)[:10]
    
    return jsonify({'suggestions': matching_names})


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

    # papers_list is list of tuples (paper_idx, paper_title, paper_id)
    papers_list = biblios[key]
    if len(papers_list) == 0:
        return jsonify({'error': 'Your name is in our database, but no papers came up.'})

    papers = [{'index': idx, 'title': title, 'id': id} for idx, title, id in papers_list]
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

    # Info about the paper that gets pulled from the spreadsheet onto the website.
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
        "API Cost (USD $)": paper_info.get("API Cost (i.e. model testing, and iterative retraining)"),
        "Funding Resource": paper_info.get("Funding Resource"),
        "Funding Type": paper_info.get("Funding Type")
    }
    return jsonify(paper_info)


@app.route('/api/updates')
def get_updates():
    try:
        # Get all corrections from Google Sheets
        corrections_data = corrections_tab.get_all_records()
        
        if not corrections_data:
            return jsonify([])
        
        # Convert to DataFrame for easier processing
        corrections_df = pd.DataFrame(corrections_data)
        
        # Sort by timestamp (most recent first)
        if 'Timestamp' in corrections_df.columns:
            corrections_df = corrections_df.sort_values('Timestamp', ascending=False)
        
        # Build updates list
        updates = []
        for _, correction in corrections_df.iterrows():
            paper_idx = correction.get('Paper Index')
            
            # Get paper info from df
            paper_info = {}
            if pd.notna(paper_idx) and 0 <= int(paper_idx) < len(df):
                paper_row = df.iloc[int(paper_idx)]
                paper_info = {
                    'title': paper_row.get('title', 'Untitled'),
                    'authors': paper_row.get('authors', 'Unknown'),
                    'year': paper_row.get('year', 'N/A'),
                    'domain': paper_row.get('Domain ARR', ''),
                    'phase': paper_row.get('Phase ARR', ''),
                    'method': paper_row.get('Method ARR', '')
                }

            # Get additional comments - try different possible column names
            comments = ''
            for possible_key in ['Share any additional comments below:', 'Additional Comments', 'Comments']:
                if possible_key in correction and pd.notna(correction[possible_key]) and str(correction[possible_key]).strip() not in ['', 'N/A']:
                    comments = str(correction[possible_key])
                    break
            
            # Build corrections dict (only non-empty fields)
            correction_fields = {}
            for key, value in correction.items():
                if key not in ['Paper ID', 'Paper Index', 'User Name', 'Timestamp'] and pd.notna(value) and str(value).strip() not in ['', 'N/A']:
                    correction_fields[key] = str(value)
            
            update = {
                'paper_title': paper_info.get('title', 'Untitled'),
                'paper_authors': paper_info.get('authors', 'Unknown'),
                'paper_year': str(paper_info.get('year', 'N/A')),
                'domain': '' if pd.isna(paper_row.get('Domain ARR')) else str(paper_row.get('Domain ARR', '')),
                'phase': '' if pd.isna(paper_row.get('Phase ARR')) else str(paper_row.get('Phase ARR', '')),
                'method': '' if pd.isna(paper_row.get('Method ARR')) else str(paper_row.get('Method ARR', '')),
                'modified_by': correction.get('User Name', 'Anonymous'),
                'modified_date': correction.get('Timestamp', ''),
                'additional_comments': comments,
                'corrections': correction_fields
            }
            updates.append(update)
        
        return jsonify(updates)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/all_papers', methods=['GET'])
def get_all_papers():
    """Return all papers with their basic info and last update status"""
    paper_updates_fresh = get_fresh_data()
    
    papers_list = []
    
    for paper_id, paper_info in paper_updates_fresh.items():
        # Handle NaN values by converting to string and checking
        title = paper_info.get('Title', 'Unknown Title')
        if pd.isna(title):
            title = 'Unknown Title'
            
        authors = paper_info.get('Authors', 'Unknown Authors')
        if pd.isna(authors):
            authors = 'Unknown Authors'
            
        last_update = paper_info.get('Last update made by', 'Unknown')
        if pd.isna(last_update):
            last_update = 'Unknown'
            
        domain = paper_info.get('Domain', 'N/A')
        if pd.isna(domain):
            domain = 'N/A'
            
        phase = paper_info.get('Phase', 'N/A')
        if pd.isna(phase):
            phase = 'N/A'
            
        method = paper_info.get('Method', 'N/A')
        if pd.isna(method):
            method = 'N/A'
            
        timestamp = paper_info.get('Timestamp', 'N/A')
        if pd.isna(timestamp):
            timestamp = 'N/A'
            
        additional_comments = paper_info.get('Additional Comments', 'N/A')
        if pd.isna(additional_comments):
            additional_comments = 'N/A'
        
        papers_list.append({
            'paper_id': str(paper_id),
            'paper_title': str(title),
            'paper_authors': str(authors),
            'last_update': str(last_update),
            'domain': str(domain),
            'phase': str(phase),
            'method': str(method),
            'timestamp': str(timestamp),
            'additional_comments': str(additional_comments)
        })
    
    return jsonify(papers_list)


@app.route('/api/paper_info/<paper_id>', methods=['GET'])
def get_paper_info(paper_id):
    """Return detailed information for a specific paper"""
    paper_updates_fresh = get_fresh_data()
    
    if paper_id not in paper_updates_fresh:
        return jsonify({'error': 'Paper not found'}), 404
    
    paper_info = paper_updates_fresh[paper_id]
    
    # Convert all values to strings and handle NaN
    result = {}
    for key, value in paper_info.items():
        if isinstance(value, list):
            # Handle lists - keep as list but clean each element
            cleaned_list = []
            for item in value:
                if pd.isna(item):
                    cleaned_list.append("N/A")
                else:
                    cleaned_list.append(str(item))
            result[key] = cleaned_list  # Keep as list, not comma-separated string
        elif pd.isna(value):
            result[key] = "N/A"
        else:
            result[key] = str(value)
    
    return jsonify(result)


@app.route('/submit_corrections', methods=['POST'])
def submit_corrections():
    global data_cache
    
    data = request.get_json()
    paper_index = data.get('paper_index')
    paper_id = data.get('paper_id')
    corrections = data.get('corrections', {})
    user_name = data.get('user_name', 'Anonymous')

    # Add timestamp
    est = pytz.timezone('US/Eastern')
    timestamp = datetime.now(est).strftime('%Y-%m-%d %H:%M:%S')

    if paper_index is None:
        return jsonify({'error': 'No paper index provided'}), 400

    # Extract GPU data
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

    # Determine GPU info values based on "No GPUs Used" button
    if corrections.get("GPU Number") == "0" and corrections.get("GPU Type") == "None" and corrections.get("GPU Storage") == "0":
        gpu_rows = [{"number": "0", "type": "None", "storage": "0", "inference_time": "N/A"}]
    elif gpu_entries:
        gpu_rows = [
            {
                "number": gpu_data.get('number', 'N/A'),
                "type": gpu_data.get('type', 'N/A'),
                "storage": gpu_data.get('storage', 'N/A'),
                "inference_time": gpu_data.get('inference_time', 'N/A')
            }
            for _, gpu_data in gpu_entries.items()
        ]
    else:
        gpu_rows = [{"number": "N/A", "type": "N/A", "storage": "N/A", "inference_time": "N/A"}]

    # Submit row(s) to corrections log. (One row for each GPU type used)
    for gpu_row in gpu_rows:
        row = [
            paper_id,
            paper_index,
            user_name,
            gpu_row["number"],
            gpu_row["type"],
            gpu_row["storage"],
            gpu_row["inference_time"],
            corrections.get("GPU CHECKED", "N/A"),
            corrections.get("LLM(s) FineTuning", "N/A"),
            corrections.get("LLM(s) Evaluation", "N/A"),
            corrections.get("LLM CHECKED", "N/A"),
            corrections.get("API Cost (USD $)", "N/A"),
            corrections.get("Funding Resource", "N/A"),
            corrections.get("Funding Type", "N/A"),
            corrections.get("Funding CHECKED", "N/A"),
            corrections.get("Share any additional comments below:", "N/A"),
            timestamp
        ]
        corrections_tab.append_row(row)

    data_cache['last_updated'] = None

    return jsonify({'success': True, 'message': 'Correction submitted successfully'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)