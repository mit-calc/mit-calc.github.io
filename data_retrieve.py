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
      if row["id"] in df_corrections["id"].values:
        matches = df_corrections[df_corrections["id"] == row["id"]]

        # Get only the latest entries (rows with the most recent timestamp)
        latest_timestamp = matches["Timestamp"].max()
        latest_matches = matches[matches["Timestamp"] == latest_timestamp]

        paper_info["Last update made by"] = latest_matches["User Name"].iloc[-1]
        paper_info["Timestamp"] = latest_matches["Timestamp"].iloc[-1]
        paper_info["Additional Comments"] = latest_matches["Additional Comments"].iloc[-1]

        paper_info["GPU Number"] = latest_matches["GPU Number"].tolist()
        paper_info["GPU Type"] = latest_matches["GPU Type"].tolist()
        paper_info["GPU Storage"] = latest_matches["GPU Storage"].tolist()
        paper_info["Inference Time"] = latest_matches["Inference Time"].tolist()

        paper_info["LLM(s) FineTuning"] = latest_matches["LLM(s) FineTuning"].iloc[-1]
        paper_info["LLM(s) Evaluation"] = latest_matches["LLM(s) Evaluation"].iloc[-1]
        
        paper_info["API Cost"] = latest_matches["API Cost"].iloc[-1]
        paper_info["Funding Resource"] = latest_matches["Funding Resource"].iloc[-1]
        paper_info["Funding Type"] = latest_matches["Funding Type"].iloc[-1]
        paper_info["Funding Amount"] = latest_matches["Funding Amount"].iloc[-1]

        if latest_matches["GPU CHECKED"].iloc[-1] == "Checked":
          paper_info["GPU Info Checked"] = "Checked"
        if latest_matches["LLM CHECKED"].iloc[-1] == "Checked":
          paper_info["LLM Info Checked"] = "Checked"
        if latest_matches["Funding CHECKED"].iloc[-1] == "Checked":
          paper_info["Funding Info Checked"] = "Checked"

      paper_dict[row["id"]] = paper_info

  return paper_dict

biblios = author_to_paper(df)
paper_updates = paper_tracker(df, df_corrections)

