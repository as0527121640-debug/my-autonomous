import os
import requests
import subprocess
from dotenv import load_dotenv

load_dotenv()

REPO_OWNER = "moovitdos"
REPO_NAME = "moovidos"
TRACKING_FILE = "last_release.txt"

def get_latest_release():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching release: {response.status_code}")
        return None

def generate_post_preview(version, release_body):
    """בניית תצוגה מקדימה של הפוסט עם תוכן ה-Release האמיתי"""
    # הסרת קישורים כפולים אם קיימים בתיאור המקורי (אופציונלי)
    content = release_body.split("---")[0].strip() # לוקח רק את החלק של התיאור לפני הקישורים אם יש מפריד
    
    return f"""**עדכון:**
{version}

{content}

**להורדה ישירה:**
[גרסה מלאה](https://github.com/moovitdos/moovidos/releases/download/{version}/moovidos_full_{version}.apk)
[גרסה קלה ללא נתונים](https://github.com/moovitdos/moovidos/releases/download/{version}/moovidos_lite_{version}.apk)
[מסד נתונים ליבוא ידני](https://github.com/moovitdos/moovidos/releases/download/{version}/transport_v8.db.zip)

[לאתר](https://moovitdos.github.io/moovidos/#home)
[לתגובות - ](https://mitmachim.top/post/1111350)
"""

def create_approval_issue(version, body):
    title = f"[אישור פרסום] גרסה חדשה שוחררה: {version}"
    preview = generate_post_preview(version, body)
    
    issue_body = f"""
גרסה חדשה נמצאה ב-Repository: `moovitdos/moovidos`.
גרסה: **{version}**

### תצוגה מקדימה של הפוסט המתוכנן:
---
{preview}
---

**האם ברצונך לפרסם את העדכון הזה בפורום "מתמחים טופ"?**
הגיב **"כן"** או **"שחרר"** כדי להתחיל בפרסום האוטומטי.
"""
    # שימוש ב-GitHub CLI ליצירת ה-Issue
    try:
        subprocess.run([
            "gh", "issue", "create",
            "--title", title,
            "--body", issue_body
        ], check=True)
        print(f"Issue created for version {version}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create issue: {e}")
        return False

def main():
    # קריאת הגרסה האחרונה שטיפלנו בה
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r") as f:
            last_version = f.read().strip()
    else:
        last_version = ""

    release = get_latest_release()
    if not release:
        return

    current_version = release["tag_name"]
    release_body = release.get("body", "אין תיאור לרליס.")

    if current_version != last_version:
        print(f"New version found: {current_version}")
        if create_approval_issue(current_version, release_body):
            # עדכון הקובץ המקומי רק אם האישיו נוצר בהצלחה
            with open(TRACKING_FILE, "w") as f:
                f.write(current_version)
        else:
            print("Skipping version update due to issue creation failure.")
    else:
        print(f"No new version. Current version {current_version} matches last handled.")

if __name__ == "__main__":
    main()
