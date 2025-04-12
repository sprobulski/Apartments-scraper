# src/scraper.py
import os
import re
import time
from typing import List
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from .utils import get_element_text, extract_review_count
from .extractors import (is_preferred, is_preferred_plus, get_reviews, get_size,
                        get_nearest_attraction, get_nearest_restaurant, get_nearest_transport,
                        allows_pets, get_check_in, get_check_out, get_price_per_person)

class BookingScraper(webdriver.Chrome):
    def __init__(self, driver_path: str = r"C:\SeleniumDriver", stay_open: bool = False):
        """Initialize the BookingScraper with Chrome WebDriver.

        Args:
            driver_path (str): Path to the ChromeDriver executable.
            stay_open (bool): Whether to keep the browser open after scraping.
        """
        print("Initializing BookingScraper...")
        self.driver_path = driver_path
        self.stay_open = stay_open
        os.environ["PATH"] += os.pathsep + self.driver_path
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        try:
            super().__init__(options=options)
            print("WebDriver initialized successfully")
        except Exception as e:
            print(f"Failed to initialize WebDriver: {e}")
            raise
        self.implicitly_wait(5)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.stay_open:
            self.quit()

    def land_first_page(self) -> None:
        """Load the Booking.com homepage and handle cookie consent."""
        print("Attempting to load Booking.com...")
        try:
            self.get("https://www.booking.com")
            print(f"Page loaded. Current URL: {self.current_url}")
            WebDriverWait(self, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
            ).click()
            print("Cookie consent rejected")
        except TimeoutException:
            print("Timeout waiting for cookie consent button")
            print(f"Current URL: {self.current_url}")
            print(f"Page source snippet: {self.page_source[:500]}")
        except Exception as e:
            print(f"Failed to load first page: {e}")

    def change_currency(self, currency: str = "PLN") -> None:
        """Change the currency on Booking.com.

        Args:
            currency (str): The currency code to select (default: "PLN").
        """
        print("Changing currency...")
        try:
            WebDriverWait(self, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="header-currency-picker-trigger"]'))
            ).click()
            currencies = self.find_elements(By.CSS_SELECTOR, ".cf67405157")
            for element in currencies:
                if currency in element.text:
                    element.click()
                    print(f"Currency set to {currency}")
                    break
        except Exception as e:
            print(f"Currency change failed: {e}")

    def select_place_to_go(self, place_to_go: str) -> None:
        """Enter destination in search field and select the correct option.

        Args:
            place_to_go (str): The destination to search for.
        """
        print(f"Selecting place: {place_to_go}")
        try:
            search_field = WebDriverWait(self, 10).until(
                EC.element_to_be_clickable((By.ID, ":rh:"))
            )
            print("Search field found")
            search_field.clear()
            search_field.send_keys(place_to_go)
            print(f"Typed '{place_to_go}' into search field")

            time.sleep(2)
            WebDriverWait(self, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[id^="autocomplete-result-"]'))
            )
            WebDriverWait(self, 10).until(
                lambda driver: any(place_to_go.lower() in s.text.lower() for s in driver.find_elements(By.CSS_SELECTOR, '[id^="autocomplete-result-"]'))
            )
            suggestions = self.find_elements(By.CSS_SELECTOR, '[id^="autocomplete-result-"]')
            print(f"Found {len(suggestions)} suggestions")

            for i, suggestion in enumerate(suggestions):
                text = suggestion.text.strip()
                print(f"Suggestion {i}: '{text}'")

            for suggestion in suggestions:
                suggestion_text = suggestion.text.strip().lower()
                if place_to_go.lower() in suggestion_text:
                    suggestion.click()
                    print(f"Selected matching suggestion: '{suggestion.text.strip()}'")
                    return

            print(f"Warning: No exact match for '{place_to_go}', selecting first suggestion")
            if suggestions:
                suggestions[0].click()
                print(f"Selected first suggestion: '{suggestions[0].text.strip()}'")
            else:
                print("No suggestions available to select")
        except TimeoutException as e:
            print(f"Timeout waiting for elements or matching suggestion: {e}")
            print(f"Current URL: {self.current_url}")
            print(f"Page source snippet: {self.page_source[:500]}")
        except Exception as e:
            print(f"Destination selection failed: {e}")

    def select_dates(self, check_in_date: str, check_out_date: str) -> None:
        """Select check-in and check-out dates.

        Args:
            check_in_date (str): Check-in date in YYYY-MM-DD format.
            check_out_date (str): Check-out date in YYYY-MM-DD format.
        """
        print(f"Selecting dates: {check_in_date} to {check_out_date}")
        try:
            WebDriverWait(self, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f'span[data-date="{check_in_date}"]'))
            ).click()
            self.find_element(By.CSS_SELECTOR, f'span[data-date="{check_out_date}"]').click()
            print("Dates selected")
        except Exception as e:
            print(f"Date selection failed: {e}")

    def select_adults(self, count: int) -> None:
        """Select the number of adults for the search.

        Args:
            count (int): Number of adults.
        """
        print(f"Selecting {count} adults")
        try:
            WebDriverWait(self, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="occupancy-config"]'))
            ).click()
            decrease_btn = self.find_element(By.CSS_SELECTOR, 'button[class*="e91c91fa93"]')
            increase_btn = self.find_element(By.CSS_SELECTOR, 'button[class*="f4d78af12a"]')
            decrease_btn.click()
            for _ in range(count - 1):
                increase_btn.click()
            print(f"Set to {count} adults")
        except Exception as e:
            print(f"Adult selection failed: {e}")

    def search(self) -> None:
        """Perform the search with the selected parameters."""
        print("Performing search...")
        try:
            WebDriverWait(self, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class*="cceeb8986b"]'))
            ).click()
            self.close_popup()
            print("Search completed")
        except Exception as e:
            print(f"Search failed: {e}")

    def close_popup(self) -> None:
        """Close any popups that might interfere with scraping."""
        print("Attempting to close popup...")
        try:
            WebDriverWait(self, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            ActionChains(self).move_by_offset(100, 100).click().perform()
            print("Popup closed")
        except Exception as e:
            print(f"Popup closing failed: {e}")

    def apply_filters(self) -> None:
        """Apply filters to the search results (e.g., hotels only)."""
        print("Applying filters...")
        try:
            WebDriverWait(self, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-filters-item="ht_id:ht_id=201"]'))
            ).click()
            print("Filters applied")
        except Exception as e:
            print(f"Filter application failed: {e}")

    def collect_results(self) -> pd.DataFrame:
        """Collect hotel data from search results and return as a DataFrame."""
        print("Collecting results...")
        data = []
        processed_urls = set()
        observation_count = 0
        start_time = time.time()

        try:
            print("Waiting for initial results to load...")
            deal_boxes = WebDriverWait(self, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="property-card-container"]'))
            )
            print(f"Found {len(deal_boxes)} initial deal boxes")
        except TimeoutException:
            print("Timeout waiting for deal boxes. Current URL:", self.current_url)
            print("Page source snippet:", self.page_source[:500])
            return pd.DataFrame(columns=[
                'Name', 'District', 'Distance', 'Preferred', 'PreferredPlus', 'Rating', 'ReviewCount',
                'StaffRating', 'FacilitiesRating', 'CleanlinessRating', 'ComfortRating', 'ValueRating',
                'LocationRating', 'WifiRating', 'TV', 'Wifi', 'Kitchen', 'Balcony', 'AC', 'SharedBathroom',
                'PrivateBathroom', 'NoSmoking', 'Heating', 'Elevator', 'FreeParking', 'Refrigerator',
                'Terrace', 'Hairdryer', 'DailyHousekeeping', 'Polish', 'English', 'German', 'Russian',
                'Ukrainian', 'French', 'Spanish', 'Italian', 'Size', 'Transport', 'Attraction',
                'Restaurant', 'CheckIn', 'CheckOut', 'Pets', 'PricePerPerson'
            ])

        last_processed_count = 0

        while True:
            for _ in range(3):
                self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            deal_boxes = self.find_elements(By.CSS_SELECTOR, 'div[data-testid="property-card-container"]')
            print(f"Found {len(deal_boxes)} deal boxes after scroll")

            new_deal_boxes = deal_boxes[last_processed_count:]
            print(f"Processing {len(new_deal_boxes)} new deal boxes (skipping {last_processed_count} already processed)")

            for box in new_deal_boxes:
                try:
                    url = box.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    base_url = url.split('?')[0]
                    if base_url in processed_urls:
                        print(f"Skipping duplicate URL: {base_url}")
                        continue
                    processed_urls.add(base_url)
                    print(f"Processing new URL: {base_url}")

                    self._extract_attributes(box, data)
                    observation_count += 1
                    print(f"Completed observation {observation_count}")
                except Exception as e:
                    print(f"Error processing deal box: {e}")
                    continue

            last_processed_count = len(deal_boxes)
            print(f"Updated last_processed_count to {last_processed_count}")

            try:
                load_more_buttons = self.find_elements(By.XPATH, '//button[.//span[contains(text(), "Załaduj więcej wyników")]]')
                if not load_more_buttons:
                    print("No 'Load more' button found, ending scrape")
                    break

                load_more = load_more_buttons[0]
                print("Found 'Load more' button")

                WebDriverWait(self, 15).until(
                    EC.element_to_be_clickable(load_more)
                )

                self.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more)
                time.sleep(1)

                if load_more.is_displayed() and load_more.is_enabled():
                    for attempt in range(3):
                        try:
                            print(f"Attempting to click 'Load more' button (attempt {attempt + 1})...")
                            load_more.click()
                            WebDriverWait(self, 15).until(
                                lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="property-card-container"]')) > last_processed_count
                            )
                            print("Clicked 'Load more' button successfully, new results loaded")
                            time.sleep(2)
                            break
                        except Exception as e:
                            print(f"Failed to click 'Load more' button (attempt {attempt + 1}): {e}")
                            self.close_popup()
                            time.sleep(2)
                            if attempt == 2:
                                print("Max retries reached for 'Load more' button, ending scrape")
                                break
                else:
                    print("Load more button is not clickable (not displayed or not enabled), ending scrape")
                    break
            except TimeoutException:
                print("Timeout waiting for 'Load more' button to be clickable or new results to load, ending scrape")
                break
            except (NoSuchElementException, ElementClickInterceptedException):
                print("No more 'Load more' button found or click intercepted, ending scrape")
                break
            except Exception as e:
                print(f"Load more error: {e}")
                break

        end_time = time.time()
        total_time = end_time - start_time
        minutes, seconds = divmod(total_time, 60)
        print(f"Scraping completed: {observation_count} observations collected in {int(minutes)} minutes and {int(seconds)} seconds")

        df = pd.DataFrame(data, columns=[
            'Name', 'District', 'Distance', 'Preferred', 'PreferredPlus', 'Rating', 'ReviewCount',
            'StaffRating', 'FacilitiesRating', 'CleanlinessRating', 'ComfortRating', 'ValueRating',
            'LocationRating', 'WifiRating', 'TV', 'Wifi', 'Kitchen', 'Balcony', 'AC', 'SharedBathroom',
            'PrivateBathroom', 'NoSmoking', 'Heating', 'Elevator', 'FreeParking', 'Refrigerator',
            'Terrace', 'Hairdryer', 'DailyHousekeeping', 'Polish', 'English', 'German', 'Russian',
            'Ukrainian', 'French', 'Spanish', 'Italian', 'Size', 'Transport', 'Attraction',
            'Restaurant', 'CheckIn', 'CheckOut', 'Pets', 'PricePerPerson'
        ])
        df.to_csv('output/booking_results.csv', index=False, encoding='utf-8')
        return df

    def _extract_attributes(self, deal_box, data: List) -> None:
        """Extract attributes from a deal box and append to data list."""
        result = []
        wait = WebDriverWait(self, 10)

        try:
            result.append(get_element_text(deal_box, '[data-testid="title"]', ""))
            result.append(get_element_text(deal_box, '[data-testid="address"]', ""))
            result.append(get_element_text(deal_box, '[data-testid="distance"]', ""))
            result.append(1 if is_preferred(deal_box) else 0)
            result.append(1 if is_preferred_plus(deal_box) else 0)

            overall_rating = "-1"
            try:
                rating_box = deal_box.find_element(By.CSS_SELECTOR, 'div[class="a3b8729ab1 d86cee9b25"]')
                rating_text = rating_box.text.strip()
                match = re.search(r'\d+,\d+', rating_text)
                if match:
                    overall_rating = match.group(0).replace(',', '.')
            except Exception:
                pass
            result.append(overall_rating)

            review_text = get_element_text(deal_box, 'div[class="abf093bdfe f45d8e4c32 d935416c47"]', "-1")
            result.append(extract_review_count(review_text))

            title = deal_box.find_element(By.CSS_SELECTOR, '[data-testid="title"]')
            self.execute_script("arguments[0].scrollIntoView({block: 'center'});", title)
            time.sleep(1)
            original_window = self.current_window_handle
            clicked = False
            for attempt in range(5):
                try:
                    self.execute_script("arguments[0].click();", title)
                    WebDriverWait(self, 10).until(EC.number_of_windows_to_be(2))
                    clicked = True
                    break
                except Exception as e:
                    print(f"Click failed: {e}")
                    self.close_popup()
                    time.sleep(2)

            if not clicked:
                result.extend(["-1"] * (45 - len(result)))
                data.append(result)
                return

            for window_handle in self.window_handles:
                if window_handle != original_window:
                    self.switch_to.window(window_handle)
                    break

            wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'div')))
            time.sleep(2)

            result.extend(get_reviews(self))
            facilities = self.find_elements(By.CSS_SELECTOR, 'span[class="a5a5a75131"]')
            facility_texts = [facility.text.strip().lower() for facility in facilities]

            utilities = [
                "1" if any("telewizor" in text or "tv" in text for text in facility_texts) else "0",
                "1" if any("wi-fi" in text or "bezpłatne wi-fi" in text for text in facility_texts) else "0",
                "1" if any("kuchnia" in text or "płyta kuchenna" in text or "aneks kuchenny" in text for text in facility_texts) else "0",
                "1" if "balkon" in facility_texts else "0",
                "1" if "klimatyzacja" in facility_texts else "0",
                "1" if "wspólna łazienka" in facility_texts else "0",
                "1" if "prywatna łazienka" in facility_texts else "0",
                "1" if "zakaz palenia" in facility_texts else "0",
                "1" if "ogrzewanie" in facility_texts else "0",
                "1" if "winda" in facility_texts else "0",
                "1" if "bezpłatny parking" in facility_texts else "0",
                "1" if "lodówka" in facility_texts else "0",
                "1" if "taras" in facility_texts else "0",
                "1" if "suszarka do włosów" in facility_texts else "0",
                "1" if "codzienne sprzątanie" in facility_texts else "0",
            ]
            result.extend(utilities)

            languages = [
                "1" if "polski" in facility_texts else "0",
                "1" if "angielski" in facility_texts else "0",
                "1" if "niemiecki" in facility_texts else "0",
                "1" if "rosyjski" in facility_texts else "0",
                "1" if "ukraiński" in facility_texts else "0",
                "1" if "francuski" in facility_texts else "0",
                "1" if "hiszpański" in facility_texts else "0",
                "1" if "włoski" in facility_texts else "0",
            ]
            result.extend(languages)

            result.append(get_size(self))
            result.append(get_nearest_transport(self))
            result.append(get_nearest_attraction(self))
            result.append(get_nearest_restaurant(self))
            result.append(get_check_in(self))
            result.append(get_check_out(self))
            result.append(allows_pets(self))
            result.append(get_price_per_person(self))

            data.append(result)
        except Exception as e:
            print(f"Error extracting attributes: {e}")
            if len(result) >= 7:
                result.extend(["-1"] * (45 - len(result)))
                data.append(result)
        finally:
            if len(self.window_handles) > 1:
                self.close()
                self.switch_to.window(self.window_handles[0])