import os
import time
from playwright.sync_api import sync_playwright

DOCS_DIR = "docs/screenshots"
os.makedirs(DOCS_DIR, exist_ok=True)

URL = "http://localhost:3000"

def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1536, 'height': 864})
        page = context.new_page()

        print("Capturing 01_dashboard.png")
        page.goto(f"{URL}/")
        time.sleep(2)
        page.screenshot(path=f"{DOCS_DIR}/01_dashboard.png")

        print("Capturing 02_interactive_map.png")
        page.goto(f"{URL}/map")
        time.sleep(2)
        page.screenshot(path=f"{DOCS_DIR}/02_interactive_map.png")

        print("Capturing 03_hazard_layers.png")
        page.goto(f"{URL}/methodology")
        time.sleep(1)
        # Scroll down to hazard data section if needed
        page.screenshot(path=f"{DOCS_DIR}/03_hazard_layers.png")

        print("Capturing 04_village_explorer.png")
        page.goto(f"{URL}/villages")
        time.sleep(2)
        page.screenshot(path=f"{DOCS_DIR}/04_village_explorer.png")

        print("Capturing 05_high_priority_village_profile.png")
        page.goto(f"{URL}/villages/645167") # Assuming this ID exists or use a known Tier 1
        time.sleep(2)
        page.screenshot(path=f"{DOCS_DIR}/05_high_priority_village_profile.png")

        print("Capturing 06_vulnerability_analysis.png")
        page.goto(f"{URL}/authority") # High vuln tab or sections
        time.sleep(1)
        page.click("text=High Vulnerability Only (≥2 flags)")
        time.sleep(1)
        page.screenshot(path=f"{DOCS_DIR}/06_vulnerability_analysis.png")

        print("Capturing 07_candidate_area_explorer.png")
        page.goto(f"{URL}/candidates")
        time.sleep(2)
        page.screenshot(path=f"{DOCS_DIR}/07_candidate_area_explorer.png")

        print("Capturing 08_candidate_area_profile.png")
        page.goto(f"{URL}/candidates/CA-5980") # Example CA
        time.sleep(2)
        page.screenshot(path=f"{DOCS_DIR}/08_candidate_area_profile.png")

        print("Capturing 09_capacity_or_dwelling_scenario.png")
        page.goto(f"{URL}/candidates") # Showing the capacity status
        time.sleep(1)
        page.screenshot(path=f"{DOCS_DIR}/09_capacity_or_dwelling_scenario.png")

        print("Capturing 10_relocation_planning_horizons.png")
        page.goto(f"{URL}/authority")
        time.sleep(1)
        page.screenshot(path=f"{DOCS_DIR}/10_relocation_planning_horizons.png")

        print("Capturing 11_authority_action_center.png")
        page.goto(f"{URL}/authority")
        time.sleep(1)
        page.click("text=Sub-District Summary")
        time.sleep(1)
        page.screenshot(path=f"{DOCS_DIR}/11_authority_action_center.png")

        print("Capturing 12_dynamic_recompute.png")
        page.goto(f"{URL}/pipeline")
        time.sleep(1)
        page.screenshot(path=f"{DOCS_DIR}/12_dynamic_recompute.png")

        print("Capturing 13_methodology_explainability.png")
        page.goto(f"{URL}/methodology")
        time.sleep(1)
        page.screenshot(path=f"{DOCS_DIR}/13_methodology_explainability.png")

        print("Capturing 14_data_status_limitations.png")
        page.goto(f"{URL}/pipeline") # or another page showing limitations
        time.sleep(1)
        page.screenshot(path=f"{DOCS_DIR}/14_data_status_limitations.png")

        browser.close()

if __name__ == '__main__':
    capture_all()
    print("All screenshots captured.")
