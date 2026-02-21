import os
import requests

# Folder to store flags
SAVE_DIR = "flags_iso"
os.makedirs(SAVE_DIR, exist_ok=True)

# APIs
COUNTRIES_API = "https://restcountries.com/v3.1/all"
FLAG_BASE_URL = "https://flagcdn.com/w320"

# Fetch all countries
response = requests.get(COUNTRIES_API, timeout=15)
response.raise_for_status()
countries = response.json()

downloaded = 0
skipped = 0

for country in countries:
    code = country.get("cca2")

    if not code:
        skipped += 1
        continue

    code = code.lower()
    file_path = os.path.join(SAVE_DIR, f"{code}.png")

    # Skip if already downloaded
    if os.path.exists(file_path):
        continue

    flag_url = f"{FLAG_BASE_URL}/{code}.png"

    try:
        r = requests.get(flag_url, timeout=10)
        if r.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r.content)
            print(f"⬇ Downloaded: {code}.png")
            downloaded += 1
        else:
            print(f"❌ Not available: {code}.png")
            skipped += 1

    except Exception as e:
        print(f"⚠ Error downloading {code}.png — {e}")
        skipped += 1

print("\n✅ Done")
print(f"✔ Downloaded: {downloaded}")
print(f"⏭ Skipped: {skipped}")
