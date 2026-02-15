import pandas as pd

# Read CSV
df = pd.read_csv("trail_sublinks3.csv")

# Remove duplicates based on Sub-Link URL
df_unique = df.drop_duplicates(subset=["Sub-Link URL"])

# Save result
df_unique.to_csv("unique.csv", index=False)

print("Done — unique.csv created")
