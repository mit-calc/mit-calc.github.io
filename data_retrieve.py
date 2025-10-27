import pandas as pd
import ast

# Get .csv version of the spreadsheet.
# NOTE: This assumes that the data is in a Google Sheets file.
# NOTE: This is just the first five rows of the original data.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1vw1LWtZ7A1_aa_WI_psgIo4Lo9X3jyC9XB4NAMbSBYg/export?format=csv"

df = pd.read_csv(SHEET_URL)

def author_to_paper(df):
  '''
  Creates dictionary that maps each unique author name to the papers they've authored.
  
  Args:
    df (Dataframe): Dataframe of spreadsheet data.

  Returns:
    author_to_paper (dict): Author's first and last name for the key (str) -> List of tuples with
    paper's index in the dataset (int) and paper's title (str).
  '''
  
  author_to_paper = {}

  for idx, author_list_str in enumerate(df["authors"]):
    if pd.isna(author_list_str) is False:  # Ignore nan values.
        if author_list_str[0] == "[":
          paper_authors = ast.literal_eval(author_list_str)
        else:
          paper_authors = author_list_str.split(", ")

        paper_title = df.iloc[idx]["title"]

        for paper_author in paper_authors:
          if paper_author not in author_to_paper:
            author_to_paper[paper_author] = [(idx, paper_title)]
          else:
            author_to_paper[paper_author].append((idx, paper_title))
  return author_to_paper

biblios = author_to_paper(df)