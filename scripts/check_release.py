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

def generate_post_preview(version):
    """בניית תצוגה מקדימה של הפוסט לפי התבנית"""
    return f"""**עדכון:**
{version}

**עדכון נתונים באמצעות יבוא קובץ חיצוני**
ניתן ליבוא בשני דרכים - 

* ממסך ההגדרות 
* פתיחה ישירה של קובץ הZIP ישירות מסייר הקבצים של המכשיר [פתח באמצעות...].

ניתן להוריד מהאתר בכל גרסה שלושה קבצים - 
1. גרסה מלאה הכולל את מסד הנתונים, 
2. גרסה קלה שכוללת  רק את האפליקציה ללא מסד נתונים, 
3. את מסד הנתונים לבדו. 

בכל שחרור יצוין מה עודכן - האפליקציה או מסד הנתונים. התקנה של עדכון תוכנה דרך האפליקציה יזהה זאת ויוריד במקרה הצורך רק את קובץ האפליקציה ללא מסד הנתונים.

**להורדה ישירה:**
[גרסה מלאה](https://github.com/moovitdos/moovidos/releases/download/{version}/moovidos_full_{version}.apk)
[גרסה קלה ללא נתונים](https://github.com/moovitdos/moovidos/releases/download/{version}/moovidos_lite_{version}.apk)
[מסד נתונים ליבוא ידני](https://github.com/moovitdos/moovidos/releases/download/{version}/transport_v8.db.zip)

[לאתר](https://moovitdos.github.io/moovidos/#home)
[לתגובות - ](https://mitmachim.top/post/1111350)
![image](/assets/uploads/files/1776240923823-3c087c5b-9afb-40d5-acd4-9a9c78a964ad-image.png)
"""

def create_approval_issue(version, body):
    title = f"[אישור פרסום] גרסה חדשה שוחררה: {version}"
    preview = generate_post_preview(version)
    
    issue_body = f"""
גרסה חדשה נמצאה ב-Repository: `moovitdos/moovidos`.
גרסה: **{version}**

### תצוגה מקדימה של הפוסט שפורסם:
---
{preview}
---

**האם ברצונך לפרסם את העדכון הזה בפורום "מתמחים טופ"?**
הגיב **"כן"** או **"שחרר"** כדי להתחיל בפרסום האוטומטי.

<details>
<summary>פרטי ה-Release המקוריים מ-GitHub</summary>
{body}
</details>
"""
    # שימוש ב-GitHub CLI ליצירת ה-Issue
    try:
        subprocess.run([
            "gh", "issue", "create",
            "--title", title,
            "--body", issue_body,
            "--label", "release-trigger"
        ], check=True)
        print(f"Issue created for version {version}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create issue: {e}")

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
        create_approval_issue(current_version, release_body)
        
        # עדכון הקובץ המקומי
        with open(TRACKING_FILE, "w") as f:
            f.write(current_version)
    else:
        print(f"No new version. Current version {current_version} matches last handled.")

if __name__ == "__main__":
    main()
