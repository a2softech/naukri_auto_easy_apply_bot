import csv
import os

# 🗂 File path
file_path = "./already_applied.csv"
temp_file = "./temp_already_applied.csv"

# 🔄 Set to track unique links
unique_links = set()
duplicates = []

# 📖 Read existing file and remove duplicates
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as infile, open(temp_file, "w", encoding="utf-8", newline="") as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            if row:  # Ensure row is not empty
                link = row[0]
                if link not in unique_links:
                    unique_links.add(link)
                    writer.writerow(row)
                else:
                    duplicates.append(link)

    # 📌 Replace original file with cleaned file
    os.replace(temp_file, file_path)

    # 📊 Console output
    print(f"\n✅ Duplicate Removal Completed!")
    print(f"📌 Total Unique Links: {len(unique_links)}")
    print(f"❌ Total Duplicates Removed: {len(duplicates)}")

    if duplicates:
        print("\n🗑 Removed Links:")
        for i, link in enumerate(duplicates, start=1):
            print(f"{i}. {link}")
else:
    print("⚠️ File 'already_applied.csv' not found!")
