import pandas as pd
import ast

# Get .csv version of the spreadsheet.
# NOTE: This assumes that the data is in a Google Sheets file.

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Y6I57HlmI9wd2iwQUQGaj1vFO2scPF48XB3osrUhXAA/export?format=csv"

# Dummy database - use for testing.
# SHEET_URL = "https://docs.google.com/spreadsheets/d/1vw1LWtZ7A1_aa_WI_psgIo4Lo9X3jyC9XB4NAMbSBYg/export?format=csv"

df = pd.read_csv(SHEET_URL)

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

biblios = author_to_paper(df)
