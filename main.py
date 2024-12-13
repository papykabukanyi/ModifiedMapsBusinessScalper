
# from playwright.sync_api import sync_playwright
# from dataclasses import dataclass, asdict, field
# import pandas as pd
# import argparse
# import os
# import sys

# @dataclass
# class Business:
#     """Holds business data."""
#     name: str = None
#     address: str = None
#     website: str = None
#     phone_number: str = None
#     reviews_count: int = None
#     reviews_average: float = None
#     latitude: float = None
#     longitude: float = None

# @dataclass
# class BusinessList:
#     """Holds list of Business objects, and saves to both Excel and CSV."""
#     business_list: list[Business] = field(default_factory=list)
#     save_at: str = 'output'

#     def dataframe(self):
#         """Transforms business_list to pandas dataframe."""
#         return pd.json_normalize(
#             (asdict(business) for business in self.business_list), sep="_"
#         )

#     def save_to_excel(self, filename):
#         """Saves pandas dataframe to excel (xlsx) file."""
#         if not os.path.exists(self.save_at):
#             os.makedirs(self.save_at)
#         self.dataframe().to_excel(f"{self.save_at}/{filename}.xlsx", index=False)

#     def save_to_csv(self, filename):
#         """Saves pandas dataframe to csv file."""
#         if not os.path.exists(self.save_at):
#             os.makedirs(self.save_at)
#         self.dataframe().to_csv(f"{self.save_at}/{filename}.csv", index=False)

# def extract_coordinates_from_url(url: str) -> tuple[float, float]:
#     """Helper function to extract coordinates from URL."""
#     coordinates = url.split('/@')[-1].split('/')[0]
#     # Return latitude, longitude
#     return float(coordinates.split(',')[0]), float(coordinates.split(',')[1])

# def sanitize_filename(filename: str) -> str:
#     """Sanitizes the filename by removing or replacing invalid characters."""
#     return "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in filename).strip()

# def main():
#     # Read search from arguments
#     parser = argparse.ArgumentParser()
#     parser.add_argument("-s", "--search", type=str)
#     parser.add_argument("-t", "--total", type=int)
#     args = parser.parse_args()

#     if args.search:
#         search_list = [args.search]

#     if args.total:
#         total = args.total
#     else:
#         # If no total is passed, set the value to a large number
#         total = 1_000_000

#     if not args.search:
#         search_list = []
#         # Read search from input.txt file
#         input_file_name = 'input.txt'
#         input_file_path = os.path.join(os.getcwd(), input_file_name)
#         if os.path.exists(input_file_path):
#             with open(input_file_path, 'r') as file:
#                 search_list = file.readlines()

#         if len(search_list) == 0:
#             print('Error occurred: You must either pass the -s search argument, or add searches to input.txt')
#             sys.exit()

#     # Scraping
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()

#         page.goto("https://www.google.com/maps", timeout=60000)
#         page.wait_for_timeout(5000)

#         for search_for_index, search_for in enumerate(search_list):
#             search_for = search_for.strip()
#             print(f"-----\n{search_for_index} - {search_for}")

#             page.locator('//input[@id="searchboxinput"]').fill(search_for)
#             page.wait_for_timeout(3000)

#             page.keyboard.press("Enter")
#             page.wait_for_timeout(5000)

#             # Scrolling
#             page.hover('//a[contains(@href, "https://www.google.com/maps/place")]')

#             previously_counted = 0
#             max_scrolls = 100  # Set a reasonable limit to prevent infinite scrolling
#             scrolls = 0

#             while scrolls < max_scrolls:
#                 # Scroll down and wait for the results to load
#                 page.mouse.wheel(0, 10000)
#                 page.wait_for_load_state('networkidle')
#                 page.wait_for_timeout(3000)

#                 current_count = page.locator(
#                     '//a[contains(@href, "https://www.google.com/maps/place")]'
#                 ).count()

#                 if current_count >= total:
#                     listings = page.locator(
#                         '//a[contains(@href, "https://www.google.com/maps/place")]'
#                     ).all()[:total]
#                     listings = [listing.locator("xpath=..") for listing in listings]
#                     print(f"Total Scraped: {len(listings)}")
#                     break
#                 elif current_count == previously_counted:
#                     listings = page.locator(
#                         '//a[contains(@href, "https://www.google.com/maps/place")]'
#                     ).all()
#                     print(f"Arrived at all available\nTotal Scraped: {len(listings)}")
#                     break
#                 else:
#                     previously_counted = current_count
#                     scrolls += 1
#                     print(f"Currently Scraped: {current_count}, Scrolls: {scrolls}")

#             business_list = BusinessList()

#             # Scraping
#             for listing in listings:
#                 try:
#                     listing.click()
#                     page.wait_for_timeout(5000)

#                     business = Business()

#                     try:
#                         business.name = listing.get_attribute('aria-label') or ""
#                     except:
#                         business.name = ""

#                     try:
#                         business.address = page.locator(
#                             '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
#                         ).first.inner_text(timeout=10000) or ""
#                     except:
#                         business.address = ""

#                     try:
#                         business.website = page.locator(
#                             '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
#                         ).first.inner_text(timeout=10000) or ""
#                     except:
#                         business.website = ""

#                     try:
#                         business.phone_number = page.locator(
#                             '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
#                         ).first.inner_text(timeout=10000) or ""
#                     except:
#                         business.phone_number = ""

#                     try:
#                         business.reviews_count = int(
#                             page.locator(
#                                 '//button[@jsaction="pane.reviewChart.moreReviews"]//span'
#                             ).first.inner_text(timeout=10000).split()[0].replace(',', '')
#                         )
#                     except:
#                         business.reviews_count = 0

#                     try:
#                         business.reviews_average = float(
#                             page.locator(
#                                 '//div[@jsaction="pane.reviewChart.moreReviews"]//div[@role="img"]'
#                             ).get_attribute('aria-label').split()[0].replace(',', '.')
#                         )
#                     except:
#                         business.reviews_average = 0.0

#                     business.latitude, business.longitude = extract_coordinates_from_url(page.url)
#                     business_list.business_list.append(business)
#                 except Exception as e:
#                     print(f"Error occurred: {e}")

#             # Output
#             sanitized_search_for = sanitize_filename(search_for)
#             business_list.save_to_excel(f"google_maps_data_{sanitized_search_for}")
#             business_list.save_to_csv(f"google_maps_data_{sanitized_search_for}")

#         browser.close()

# if __name__ == "__main__":
#     main()
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dataclasses import dataclass, asdict, field
import pandas as pd
import argparse
import os
import sys

@dataclass
class Business:
    """Holds business data."""
    name: str = None
    website: str = None
    phone_number: str = None

@dataclass
class BusinessList:
    """Holds list of Business objects, and saves to both Excel and CSV."""
    business_list: list[Business] = field(default_factory=list)
    save_at: str = 'output'

    def dataframe(self):
        """Transforms business_list to pandas dataframe."""
        return pd.json_normalize(
            (asdict(business) for business in self.business_list), sep="_"
        )

    def save_to_excel(self, filename):
        """Saves pandas dataframe to excel (xlsx) file."""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_excel(f"{self.save_at}/{filename}.xlsx", index=False)

    def save_to_csv(self, filename):
        """Saves pandas dataframe to csv file."""
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"{self.save_at}/{filename}.csv", index=False)

def sanitize_filename(filename: str) -> str:
    """Sanitizes the filename by removing or replacing invalid characters."""
    return "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in filename).strip()

def main():
    # Read search from arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--search", type=str)
    parser.add_argument("-t", "--total", type=int)
    args = parser.parse_args()

    if args.search:
        search_list = [args.search]

    if args.total:
        total = args.total
    else:
        total = 1_000_000

    if not args.search:
        search_list = []
        input_file_name = 'input.txt'
        input_file_path = os.path.join(os.getcwd(), input_file_name)
        if os.path.exists(input_file_path):
            with open(input_file_path, 'r') as file:
                search_list = file.readlines()

        if len(search_list) == 0:
            print('Error occurred: You must either pass the -s search argument, or add searches to input.txt')
            sys.exit()

    # Scraping
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)

        for search_for_index, search_for in enumerate(search_list):
            search_for = search_for.strip()
            print(f"-----\n{search_for_index} - {search_for}")

            page.locator('//input[@id="searchboxinput"]').fill(search_for)
            page.wait_for_timeout(3000)

            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            # Retrieve all the listings matching the locator
            listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()

            if not listings:
                print(f"No listings found for '{search_for}'. Moving to next search.")
                continue

            print(f"Total Scraped: {len(listings)}")

            business_list = BusinessList()

            # Scraping individual listings
            for listing_index, listing in enumerate(listings):
                retry_attempts = 3
                wait_times = [5000, 10000, 15000]  # Increased wait times for retries
                for attempt in range(retry_attempts):
                    try:
                        # Scroll to the element to ensure it's in the viewport
                        listing.scroll_into_view_if_needed(timeout=10000)

                        # Check if the element is visible before interacting
                        if not listing.is_visible():
                            print(f"Listing {listing_index} is not visible. Skipping.")
                            break

                        # Attempt to click the listing with an increased timeout
                        listing.click(timeout=60000)  # Increased timeout to 60 seconds
                        page.wait_for_timeout(5000)  # Wait for the page to load

                        business = Business()

                        business.name = listing.get_attribute('aria-label') or ""
                        business.website = page.locator(
                            '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
                        ).first.inner_text(timeout=10000) or ""
                        business.phone_number = page.locator(
                            '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
                        ).first.inner_text(timeout=10000) or ""

                        business_list.business_list.append(business)
                        break  # Exit retry loop if successful
                    except PlaywrightTimeoutError:
                        print(f"Timeout occurred on attempt {attempt + 1} for listing {listing_index}. Retrying after waiting for {wait_times[attempt]} ms...")
                        page.wait_for_timeout(wait_times[attempt])  # Progressively longer waits
                        if attempt == retry_attempts - 1:
                            print(f"Failed after multiple attempts for listing {listing_index}. Moving to next listing.")
                            continue
                    except Exception as e:
                        print(f"Error occurred: {e}")
                        continue

            sanitized_search_for = sanitize_filename(search_for)
            business_list.save_to_excel(f"google_maps_data_{sanitized_search_for}")
            business_list.save_to_csv(f"google_maps_data_{sanitized_search_for}")

        browser.close()

if __name__ == "__main__":
    main()
