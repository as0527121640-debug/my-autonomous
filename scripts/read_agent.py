import os
import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
from dotenv import load_dotenv

# טעינת משתני סביבה (לשימוש מקומי)
load_dotenv()

# הגדרת Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("שגיאה: לא נמצא מפתח GEMINI_API_KEY")

async def scrape_thread(url):
    """סריקה של השרשור וחילוץ ההודעות"""
    print(f"מתחיל לסרוק את השרשור: {url}")
    async with async_playwright() as p:
        # הרצה ב-headless כי זה רץ על השרתים של GitHub
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle")
            
            # איתור הודעות (NodeBB)
            # ב-NodeBB כל פוסט נמצא בתוך אלמנט עם אטריביוט component="post"
            post_elements = await page.query_selector_all('[component="post"]')
            
            thread_content = []
            for element in post_elements:
                author = await element.get_attribute("data-username") or "אנונימי"
                # התוכן נמצא בדרך כלל בתוך דיב עם קלאס content
                content_node = await element.query_selector(".content")
                if content_node:
                    text = await content_node.inner_text()
                    thread_content.append(f"{author}: {text.strip()}")
            
            return thread_content
        except Exception as e:
            print(f"שגיאה בסריקה: {e}")
            return []
        finally:
            await browser.close()

def analyze_thread(posts):
    """שימוש ב-Gemini כדי להבין את תוכן השרשור"""
    import time
    if not posts:
        return "לא נמצאו הודעות לסריקה."

    full_text = "\n".join(posts)
    prompt = f"""
    נתח את שרשור הפורום הבא:
    {full_text}
    
    סכם עבורי:
    1. מהן השאלות או הבעיות העיקריות שעלו?
    2. האם יש משתמשים שמחכים לעדכון טכני (למשל על ה-GTFS)?
    3. מהי השורה התחתונה שצריך להכיר?
    
    כתוב את הסיכום בעברית, בצורה תמציתית למפתחים.
    """

    model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
    
    # ניסיון עד 3 פעמים במקרה של Timeout או עומס
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt < 2:
                print(f"ניסיון {attempt + 1} נכשל, מנסה שוב בעוד 5 שניות... ({e})")
                time.sleep(5)
                continue
            return f"שגיאה בניתוח ה-AI אחרי 3 ניסיונות: {e}"

async def main():
    target_url = os.getenv("TARGET_THREAD_URL")
    if not target_url:
        print("שגיאה: לא הוגדרה כתובת שרשור (TARGET_THREAD_URL)")
        return

    # 1. קריאה
    posts = await scrape_thread(target_url)
    
    # 2. ניתוח
    summary = analyze_thread(posts)
    
    # 3. הדפסה (GitHub Actions יתפוס את זה בלוגים)
    print("\n--- סיכום הסוכן ---")
    print(summary)
    
    # שמירת הסיכום לקובץ זמני
    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)

if __name__ == "__main__":
    asyncio.run(main())
