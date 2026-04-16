import os
import sys
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# הגדרות פורום
FORUM_URL = "https://mitmachim.top/topic/95538/"
LOGIN_URL = "https://mitmachim.top/login"
USERNAME = os.getenv("FORUM_USERNAME")
PASSWORD = os.getenv("FORUM_PASSWORD")

def get_release_body(version):
    """משיכת תוכן הרליס מ-GitHub API לפי מספר גרסה"""
    import requests
    url = f"https://api.github.com/repos/moovitdos/moovidos/releases/tags/{version}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("body", "")
    return ""

def generate_post_content(version):
    """בניית תוכן הפוסט לפי התבנית עם התוכן הדינמי מ-GitHub"""
    release_body = get_release_body(version)
    # לוקח רק את החלק של התיאור לפני הקישורים אם יש מפריד ---
    content = release_body.split("---")[0].strip() if release_body else "אין תיאור זמין לרליס זה."
    
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

async def post_to_forum(version):
    if not USERNAME or not PASSWORD:
        print("Error: Missing forum credentials.")
        return False

    async with async_playwright() as p:
        # הרצה ב-headless עם Agent אנושי כדי למנוע חסימות
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # 1. התחברות
            print("Logging in to forum...")
            await page.goto(LOGIN_URL)
            await page.fill('input[name="username"]', USERNAME)
            await page.fill('input[name="password"]', PASSWORD)
            await page.click('#login')
            
            # המתנה לוודא שהתחברנו (בדיקת אלמנט logout או שם משתמש)
            await page.wait_for_load_state("networkidle")
            
            # 2. מעבר לשרשור
            print(f"Navigating to thread: {FORUM_URL}")
            await page.goto(FORUM_URL)
            await page.wait_for_load_state("networkidle")

            # 3. פתיחת עורך התגובה
            # כפתור ה-Reply ב-NodeBB בדרך כלל עם האטריביוט component="topic/reply"
            print("Opening reply editor...")
            await page.click('[component="topic/reply"]')
            
            # המתנה להופעת תיבת הטקסט
            await page.wait_for_selector('.composer .write')
            
            # 4. כתיבת פוסט
            print("Typing content...")
            content = generate_post_content(version)
            await page.fill('.composer .write', content)
            
            # 5. שליחה
            print("Submitting post...")
            # משתמשים בסלקטור ספציפי יותר ומחפשים את הכפתור הגלוי
            submit_button = page.locator('.composer [data-action="post"]:visible').first
            await submit_button.click()
            
            # המתנה לסגירת ה-composer
            await page.wait_for_selector('.composer', state="hidden", timeout=10000)
            print(f"Successfully posted update for {version}!")
            return True

        except Exception as e:
            print(f"Error during posting: {e}")
            # צילום מסך לדיבאג
            await page.screenshot(path="debug_error.png")
            return False
        finally:
            await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python post_to_forum.py <version>")
        sys.exit(1)
    
    ver = sys.argv[1]
    asyncio.run(post_to_forum(ver))
