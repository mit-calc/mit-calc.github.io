import pandas as pd

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Y6I57HlmI9wd2iwQUQGaj1vFO2scPF48XB3osrUhXAA/export?format=csv"
CORRECTIONS_URL = "https://docs.google.com/spreadsheets/d/1Y6I57HlmI9wd2iwQUQGaj1vFO2scPF48XB3osrUhXAA/export?format=csv&gid=13066274"

df = pd.read_csv(SHEET_URL)
df_corrections = pd.read_csv(CORRECTIONS_URL)

paper_dict = {}

for index, row in df.iterrows():
    if row["id"] not in paper_dict:
        # Save info from the ChatGPT-scraped data.
        paper_info = {"Last update": "ChatGPT", # ChatGPT if not updated, person's name if updated.
                    "GPU Number": row["GPU Number"],
                    "GPU Type": row["GPU Type"],
                    "GPU Storage": row["GPU Storage"],
                    "Inference Time": row["Inference time"],
                    "LLM(s) FineTuning": row["LLM(s) FineTuning"],
                    "LLM(s) Evaluation": row["LLM(s) Evaluation"],
                    "API Cost": row["API Cost (i.e. model testing, and iterative retraining)"],
                    "Funding Resource": row["Funding Resource"],
                    "Funding Type": row["Funding Type"],
                    }
    
    if row["id"] in df_corrections["id"].values:
        matches = df_corrections[df_corrections["id"] == row["id"]]
        print(f"CORRECTION FOUND FOR: {row['id']}")
        print(matches)
        
    paper_dict[row["id"]] = paper_info

# print(paper_dict)
