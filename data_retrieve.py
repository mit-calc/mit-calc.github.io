import pandas as pd
import ast

# Get .csv version of the spreadsheet.
# NOTE: This assumes that the data is in a Google Sheets file.

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Y6I57HlmI9wd2iwQUQGaj1vFO2scPF48XB3osrUhXAA/export?format=csv"
CORRECTIONS_URL = "https://docs.google.com/spreadsheets/d/1Y6I57HlmI9wd2iwQUQGaj1vFO2scPF48XB3osrUhXAA/export?format=csv&gid=13066274"

# Dummy database - use for testing.
# SHEET_URL = "https://docs.google.com/spreadsheets/d/1vw1LWtZ7A1_aa_WI_psgIo4Lo9X3jyC9XB4NAMbSBYg/export?format=csv"

df = pd.read_csv(SHEET_URL)
df_corrections = pd.read_csv(CORRECTIONS_URL)

def author_to_paper(df):
  '''
  Creates dictionary that maps each unique author name to the papers they've authored.
  
  Args:
    df (Dataframe): Dataframe of spreadsheet data.

  Returns:
    author_to_paper (dict): Author's first and last name for the key (str) -> List of tuples with
    paper's index in the dataset (int), paper's title (str), and paper's id (str)
  '''
  
  author_to_paper = {}

  # For each paper, turn its list of authors (which are strings) into Python lists.
  for idx, author_list_str in enumerate(df["authors"]):
    if pd.isna(author_list_str) is False:  # Ignore nan values.
        if author_list_str[0] == "[":
          paper_authors = ast.literal_eval(author_list_str)
        else:
          paper_authors = author_list_str.split(", ")

        # Retrieve the paper's title (str) and id (str).
        paper_title = df.iloc[idx]["title"]
        paper_id = df.iloc[idx]["id"]

        # Update each author's entry in author_to_paper.
        for paper_author in paper_authors:
          if paper_author not in author_to_paper:
            author_to_paper[paper_author] = [(idx, paper_title, paper_id)]
          else:
            author_to_paper[paper_author].append((idx, paper_title, paper_id))
  return author_to_paper

def paper_tracker(df, df_corrections):
  '''
  Given a Dataframe of the original ChatGPT-scraped data, and a Dataframe of 
  the user-submitted corrections log, track each paper by ID (NOT dataset index!) and
  their relevant information in a dictionary.

  Key (string): Paper ID
  Value (dict): (All the columns in the corrections log spreadsheet)
  '''
  paper_dict = {}

  # Pre-build a set of paper IDs that have corrections (MUCH faster lookup)
  papers_with_corrections = set(df_corrections["id"].unique())

  # Iterate through all rows in original data.
  for index, row in df.iterrows():
    if row["id"] not in paper_dict:
      # Save info from the ChatGPT-scraped data.
      paper_info = {
          "Title": row["title"] if pd.notna(row["title"]) else "Unknown Title",
          "Authors": row["authors"] if pd.notna(row["authors"]) else "Unknown Authors",
          "Last update made by": "ChatGPT",
          "GPU Number": row["GPU Number"] if pd.notna(row["GPU Number"]) else "N/A",
          "GPU Type": row["GPU Type"] if pd.notna(row["GPU Type"]) else "N/A",
          "GPU Storage": row["GPU Storage"] if pd.notna(row["GPU Storage"]) else "N/A",
          "Inference Time": row["Inference time"] if pd.notna(row["Inference time"]) else "N/A",
          "LLM(s) FineTuning": row["LLM(s) FineTuning"] if pd.notna(row["LLM(s) FineTuning"]) else "N/A",
          "LLM(s) Evaluation": row["LLM(s) Evaluation"] if pd.notna(row["LLM(s) Evaluation"]) else "N/A",
          "API Cost": row["API Cost (i.e. model testing, and iterative retraining)"] if pd.notna(row["API Cost (i.e. model testing, and iterative retraining)"]) else "N/A",
          "Funding Resource": row["Funding Resource"] if pd.notna(row["Funding Resource"]) else "N/A",
          "Funding Type": row["Funding Type"] if pd.notna(row["Funding Type"]) else "N/A",
          "Funding Amount": "N/A",
          "GPU Info Checked": "Not Checked",
          "LLM Info Checked": "Not Checked",
          "Funding Info Checked": "Not Checked",
          "Domain": row["Domain ARR"],
          "Phase": row["Phase ARR"],
          "Method": row["Method ARR"],
          "Timestamp": "",
          "Additional Comments": ""
      }
      
      # Go through user-submitted corrections and update paper_info.
      if row["id"] in papers_with_corrections:
        matches = df_corrections[df_corrections["id"] == row["id"]]
        
        # Sort by timestamp to process in chronological order (oldest to newest)
        matches = matches.sort_values('Timestamp')
        
        # Find the latest timestamp that has GPU data
        latest_gpu_timestamp = None
        for _, submission in matches.iterrows():
          gpu_num = submission["GPU Number"]
          if pd.notna(gpu_num) and str(gpu_num).strip() not in ['', 'N/A']:
            latest_gpu_timestamp = submission["Timestamp"]
        
        # Collect GPU data from all rows with the latest GPU timestamp
        gpu_rows = []
        if latest_gpu_timestamp:
          gpu_submissions = matches[matches["Timestamp"] == latest_gpu_timestamp]
          for _, submission in gpu_submissions.iterrows():
            gpu_num = submission["GPU Number"]
            if pd.notna(gpu_num) and str(gpu_num).strip() not in ['', 'N/A']:
              gpu_rows.append({
                "number": gpu_num,
                "type": submission["GPU Type"] if pd.notna(submission["GPU Type"]) else "N/A",
                "storage": submission["GPU Storage"] if pd.notna(submission["GPU Storage"]) else "N/A",
                "time": submission["Inference Time"] if pd.notna(submission["Inference Time"]) else "N/A"
              })
        
        # Process each submission for non-GPU fields, keeping the latest non-N/A value
        for _, submission in matches.iterrows():
          # Update metadata (always use latest)
          paper_info["Last update made by"] = submission["User Name"]
          paper_info["Timestamp"] = submission["Timestamp"]
          
          # Update Additional Comments if not N/A
          if pd.notna(submission["Additional Comments"]) and str(submission["Additional Comments"]).strip() not in ['', 'N/A']:
            paper_info["Additional Comments"] = submission["Additional Comments"]
          
          # Update LLM fields if not N/A
          if pd.notna(submission["LLM(s) FineTuning"]) and str(submission["LLM(s) FineTuning"]).strip() not in ['', 'N/A']:
            paper_info["LLM(s) FineTuning"] = submission["LLM(s) FineTuning"]
          
          if pd.notna(submission["LLM(s) Evaluation"]) and str(submission["LLM(s) Evaluation"]).strip() not in ['', 'N/A']:
            paper_info["LLM(s) Evaluation"] = submission["LLM(s) Evaluation"]
          
          # Update API Cost if not N/A
          if pd.notna(submission["API Cost"]) and str(submission["API Cost"]).strip() not in ['', 'N/A']:
            paper_info["API Cost"] = submission["API Cost"]
          
          # Update Funding fields if not N/A
          if pd.notna(submission["Funding Resource"]) and str(submission["Funding Resource"]).strip() not in ['', 'N/A']:
            paper_info["Funding Resource"] = submission["Funding Resource"]
          
          if pd.notna(submission["Funding Type"]) and str(submission["Funding Type"]).strip() not in ['', 'N/A']:
            paper_info["Funding Type"] = submission["Funding Type"]
          
          if pd.notna(submission["Funding Amount"]) and str(submission["Funding Amount"]).strip() not in ['', 'N/A']:
            paper_info["Funding Amount"] = submission["Funding Amount"]
          
          # Update check flags if marked as Checked
          if submission["GPU CHECKED"] == "Checked":
            paper_info["GPU Info Checked"] = "Checked"
          if submission["LLM CHECKED"] == "Checked":
            paper_info["LLM Info Checked"] = "Checked"
          if submission["Funding CHECKED"] == "Checked":
            paper_info["Funding Info Checked"] = "Checked"
        
        # If GPU data was found, convert to lists
        if len(gpu_rows) > 0:
          paper_info["GPU Number"] = [str(row["number"]) for row in gpu_rows]
          paper_info["GPU Type"] = [str(row["type"]) for row in gpu_rows]
          paper_info["GPU Storage"] = [str(row["storage"]) for row in gpu_rows]
          paper_info["Inference Time"] = [str(row["time"]) for row in gpu_rows]

      paper_dict[row["id"]] = paper_info

  return paper_dict

biblios = author_to_paper(df)
paper_updates = paper_tracker(df, df_corrections)

