from dotenv import load_dotenv
load_dotenv()

import os
import requests

from playwright.sync_api import sync_playwright

from datetime import datetime


#TG msg
def tg_alert(message):
    token = os.environ["TG_TOKEN"]
    chat_id = os.environ["TG_CHAT_ID"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.get(url, params={
        "chat_id": chat_id,
        "text": message
    })

#Scraper
def scrape_meduse():
    with sync_playwright() as p:
        base_url = os.environ["BASE_URL"]
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(base_url, timeout=60000)

        # attendre que la page charge (à ajuster selon le site)
        page.wait_for_timeout(3000)

        container = page.locator("div.load-status")

        # méduses
        try:
            jellyfish_24h = container.locator(".load-badge").inner_text().strip()
        except:
            jellyfish_24h = "N/A"

        # dernier signalement
        try:
            report = page.locator("tr.report-row").first

            report_date = report.get_attribute("data-report-date")
            report_level = report.get_attribute("data-report-level-label")
            report_beach = report.get_attribute("data-report-beach-name")

        except:
            report_date = "N/A"
            report_level = "N/A"
            report_beach = "N/A"

        # température eau
        try:
            water_temp = container.locator(".weather-badge").nth(0).inner_text().strip()
        except:
            water_temp = "N/A"

        # courant marin
        try:
            current_speed = container.locator(".weather-badge").nth(1).inner_text().strip()
        except:
            current_speed = "N/A"

        browser.close()

        return jellyfish_24h, water_temp, current_speed, report_date, report_level, report_beach


def get_meduse_forecast_score():
    url = os.environ["EXPLORE_URL"]

    today = datetime.now()
    day = today.day
    month = today.month - 1  # important : janvier = 0

    selector = f'.explore-day[data-day="{day}"][data-month="{month}"]'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)

        try:
            element = page.locator(selector)
            score = element.get_attribute("data-score")

            if score is None:
                score = "0"

        except:
            score = "0"

        browser.close()

    return score

def interpret_meduse_score(score):
    try:
        s = float(score)
    except:
        return "inconnu"

    if s < 5:
        return "rare"
    elif s < 20:
        return "peu fréquent"
    elif s < 40:
        return "fréquent"
    else:
        return "très fréquent"

#Msg format
def format_forecast_message(score):
    return f"📅 Risque méduses : {score}% ({interpret_meduse_score(score)})"

def format_report(date, level, beach):
    if date == "N/A":
        return "indisponible"
    return f"{level} • {beach} • {date}"


def format_message(jellyfish, water_temp, current_speed, report):
    return (
        f"🪼 Méduses (24h) : {jellyfish}\n"
        f"🌊 Température : {water_temp}\n"
        f"🌬 Courant : {current_speed}\n\n"
        f"🕒 Dernier signalement : {report}"
    )



#Main
if __name__ == "__main__":
    try:
        # --- scraping live (ton premier bloc existant) ---
        jellyfish, water_temp, current_speed, report_date, report_level, report_beach = scrape_meduse()

        report = format_report(report_date, report_level, report_beach)

        live_message = format_message(
            jellyfish,
            water_temp,
            current_speed,
            report
        )

        # --- forecast ---
        forecast_score = get_meduse_forecast_score()
        forecast_message = format_forecast_message(forecast_score)

        # --- message final ---
        message = live_message + "\n\n" + forecast_message

        print(message)
        tg_alert(message)

    except Exception as e:
        error_msg = f"Erreur scraping méduses : {e}"
        print(error_msg)
        tg_alert(error_msg)