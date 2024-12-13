from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import os

@dataclass
class Business:
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    reviews_count: int = None
    reviews_average: float = None
    latitude: float = None
    longitude: float = None

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)
    save_at: str = 'output'

    def dataframe(self):
        return pd.json_normalize((asdict(business) for business in self.business_list), sep="_")

    def save_to_excel(self, filename):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"{self.save_at}/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"{self.save_at}/{filename}.csv", index=False)

def extract_coordinates_from_url(url: str) -> tuple[float, float]:
    coordinates = url.split('/@')[-1].split('/')[0]
    return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])

def sanitize_filename(filename: str) -> str:
    return "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in filename).strip()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()

    search_list = [args.search] if args.search else []
    total = args.total if args.total else 1000000

    if not search_list:
        input_file_path = os.path.join(os.getcwd(), 'input.txt')
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = file.readlines()

        if len(search_list) == 0:
            print('Error occurred: You must either pass the -s search argument, or add searches to input.txt')
            sys.exit()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)

        for search_for in search_list:
            search_for = search_for.strip()
            page.locator('//input[@id="searchboxinput"]').fill(search_for)
            page.wait_for_timeout(3000)
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
            page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

            previously_counted = 0
            max_scrolls = 100
            scrolls = 0

            while scrolls < max_scrolls:
                page.mouse.wheel(0, 10000)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(3000)

                current_count = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count()
                if current_count >= total:
                    listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
                    listings = [listing.locator("xpath=..") for listing in listings]
                    break
                elif current_count == previously_counted:
                    listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()
                    break
                else:
                    previously_counted = current_count
                    scrolls += 1

            business_list = BusinessList()

            for listing in listings:
                try:
                    listing.click()
                    page.wait_for_timeout(5000)

                    business = Business(
                        name=listing.get_attribute('aria-label') or "",
                        address=page.locator('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]').first.inner_text(timeout=10000) or "",
                        website=page.locator('//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]').first.inner_text(timeout=10000) or "",
                        phone_number=page.locator('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]').first.inner_text(timeout=10000) or "",
                        reviews_count=int(page.locator('//button[@jsaction="pane.reviewChart.moreReviews"]//span').first.inner_text(timeout=10000).split()[0].replace(',', '')) if page.locator('//button[@jsaction="pane.reviewChart.moreReviews"]//span').count() > 0 else 0,
                        reviews_average=float(page.locator('//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]').get_attribute('aria-label').split()[0].replace(',', '.')) if page.locator('//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]').count() > 0 else 0.0,
                        latitude=None,
                        longitude=None
                    )

                    business.latitude, business.longitude = extract_coordinates_from_url(page.url)
                    business_list.business_list.append(business)
                except Exception as e:
                    print(f"Error occurred: {e}")

            sanitized_search_for = sanitize_filename(search_for)
            business_list.save_to_excel(f"google_maps_data_{sanitized_search_for}")
            business_list.save_to_csv(f"google_maps_data_{sanitized_search_for}")

        browser.close()
        print(f"google_maps_data_{sanitized_search_for}.csv")

if __name__ == "__main__":
    main()
