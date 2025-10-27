import pandas as pd

SHEET_URL = "https://docs.google.com/spreadsheets/d/1vw1LWtZ7A1_aa_WI_psgIo4Lo9X3jyC9XB4NAMbSBYg/export?format=csv&gid=0"
CORRECTIONS_URL = "https://docs.google.com/spreadsheets/d/1vw1LWtZ7A1_aa_WI_psgIo4Lo9X3jyC9XB4NAMbSBYg/export?format=csv&gid=1095922093"

df = pd.read_csv(CORRECTIONS_URL)
print(df)