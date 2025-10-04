import pandas as pd
csv_file_name = input("Enter File Name : ")
# CSV file load karo
df = pd.read_csv(csv_file_name)

# Total rows
total_urls = len(df)

# Unique rows
unique_urls = df['URL'].nunique()

# Duplicate rows
duplicate_count = total_urls - unique_urls

# Duplicate list
duplicates = df[df.duplicated(subset=['URL'], keep=False)]

# ===== SUMMARY =====
print("===== SUMMARY =====")
print(f"Total URLs       : {total_urls}")
print(f"Unique URLs      : {unique_urls}")
print(f"Duplicate Count  : {duplicate_count}")

if duplicate_count > 0:
    print("\nDuplicate URLs:")
    print(duplicates['URL'].to_string(index=False))
else:
    print("\nNo duplicates found ✅")

# ===== REMOVE DUPLICATES & UPDATE SAME FILE =====
df = df.drop_duplicates(subset=['URL'])
df.to_csv(csv_file_name, index=False)

print("\n✅ Duplicates removed. File '{csv_file_name}' updated successfully.")
