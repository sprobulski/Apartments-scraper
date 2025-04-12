# src/extractors.py
import re
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

def is_preferred(deal_box) -> bool:
    """Check if the property is Preferred (but not Preferred Plus)."""
    try:
        spans = deal_box.find_elements(By.CSS_SELECTOR, 'span[class*="c2cc050fb8"]')
        if not spans:
            return False
        for span in spans:
            class_list = span.get_attribute('class').split()
            if 'c2cc050fb8' in class_list and 'b3d142134a' not in class_list:
                return True
        return False
    except Exception:
        return False

def is_preferred_plus(deal_box) -> bool:
    """Check if the property is Preferred Plus."""
    try:
        spans = deal_box.find_elements(By.CSS_SELECTOR, 'span[class*="b3d142134a"]')
        if not spans:
            return False
        for span in spans:
            class_list = span.get_attribute('class').split()
            if 'b3d142134a' in class_list:
                return True
        return False
    except Exception:
        return False

def get_reviews(driver) -> List[str]:
    """Extract detailed review scores."""
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="c624d7469d f034cf5568 c69ad9b0c2 b57676889b c6198b324c a3214e5942"]'))
        )
        scores = {
            "Personel": "-1",
            "Udogodnienia": "-1",
            "Czystość": "-1",
            "Komfort": "-1",
            "Stosunek jakości do ceny": "-1",
            "Lokalizacja": "-1",
            "Bezpłatne WiFi": "-1"
        }
        all_containers = driver.find_elements(By.CSS_SELECTOR, 'div[class="c624d7469d f034cf5568 c69ad9b0c2 b57676889b c6198b324c a3214e5942"]')
        valid_indices = []
        for i in range(len(all_containers)):
            try:
                container = driver.find_elements(By.CSS_SELECTOR, 'div[class="c624d7469d f034cf5568 c69ad9b0c2 b57676889b c6198b324c a3214e5942"]')[i]
                container.find_element(By.CSS_SELECTOR, 'span[class="be887614c2"]')
                container.find_element(By.CSS_SELECTOR, 'div[class="ccb65902b2 bdc1ea4a28"]')
                valid_indices.append(i)
            except Exception:
                continue

        for idx in valid_indices:
            for attempt in range(3):
                try:
                    container = driver.find_elements(By.CSS_SELECTOR, 'div[class="c624d7469d f034cf5568 c69ad9b0c2 b57676889b c6198b324c a3214e5942"]')[idx]
                    category = container.find_element(By.CSS_SELECTOR, 'span[class="be887614c2"]').text.strip()
                    score = container.find_element(By.CSS_SELECTOR, 'div[class="ccb65902b2 bdc1ea4a28"]').text.strip().replace(',', '.')
                    if category in scores:
                        scores[category] = score
                    break
                except Exception:
                    if attempt == 2:
                        break
        return [
            scores["Personel"],
            scores["Udogodnienia"],
            scores["Czystość"],
            scores["Komfort"],
            scores["Stosunek jakości do ceny"],
            scores["Lokalizacja"],
            scores["Bezpłatne WiFi"]
        ]
    except Exception:
        return ["-1"] * 7

def get_size(driver) -> str:
    """Extract the room size."""
    try:
        size_divs = driver.find_elements(By.CSS_SELECTOR, 'div.hprt-facilities-facility')
        for div in size_divs:
            try:
                size_span = div.find_element(By.CSS_SELECTOR, 'span.bui-badge')
                size_text = size_span.text.strip()
                match = re.search(r'\d+\s*m²', size_text)
                if match:
                    return match.group(0)
            except:
                continue
        return "-1"
    except Exception:
        return "-1"

def get_nearest_attraction(driver) -> str:
    """Extract the name and distance of the first attraction."""
    try:
        poi_blocks = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="poi-block"]')
        for block in poi_blocks:
            try:
                header = block.find_element(By.CSS_SELECTOR, 'div[class="e1eebb6a1e e6208ee469 d0caee4251"]').text.strip()
                if header == "Najlepsze atrakcje":
                    items = block.find_elements(By.CSS_SELECTOR, 'li[class="a8b57ad3ff d50c412d31 fb9a5438f9 c7a5a1307a"]')
                    if items:
                        item = items[0]
                        name = item.find_element(By.CSS_SELECTOR, 'div[class="dc5041d860 c72df67c95 fb60b9836d"]').text.strip()
                        distance = item.find_element(By.CSS_SELECTOR, 'div[class="a53cbfa6de f45d8e4c32 cea0c192d7"]').text.strip()
                        return f"{name}, {distance}"
            except Exception:
                continue
        return "-1"
    except Exception:
        return "-1"

def get_nearest_restaurant(driver) -> str:
    """Extract the name and distance of the first restaurant or cafe."""
    try:
        poi_blocks = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="poi-block"]')
        for block in poi_blocks:
            try:
                header = block.find_element(By.CSS_SELECTOR, 'div[class="e1eebb6a1e e6208ee469 d0caee4251"]').text.strip()
                if header == "Restauracje i kawiarnie":
                    items = block.find_elements(By.CSS_SELECTOR, 'li[class="a8b57ad3ff d50c412d31 fb9a5438f9 c7a5a1307a"]')
                    if items:
                        item = items[0]
                        name = item.find_element(By.CSS_SELECTOR, 'div[class="dc5041d860 c72df67c95 fb60b9836d"]').text.strip()
                        type_span = item.find_elements(By.CSS_SELECTOR, 'span[class="b6f930dcc9"]')
                        if type_span:
                            type_text = type_span[0].text.strip()
                            name = name.replace(type_text, "").strip()
                        distance = item.find_element(By.CSS_SELECTOR, 'div[class="a53cbfa6de f45d8e4c32 cea0c192d7"]').text.strip()
                        return f"{name}, {distance}"
            except Exception:
                continue
        return "-1"
    except Exception:
        return "-1"

def get_nearest_transport(driver) -> str:
    """Extract the name and distance of the first public transport option."""
    try:
        poi_blocks = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="poi-block"]')
        for block in poi_blocks:
            try:
                header = block.find_element(By.CSS_SELECTOR, 'div[class="e1eebb6a1e e6208ee469 d0caee4251"]').text.strip()
                if header == "Transport publiczny":
                    items = block.find_elements(By.CSS_SELECTOR, 'li[class="a8b57ad3ff d50c412d31 fb9a5438f9 c7a5a1307a"]')
                    if items:
                        item = items[0]
                        name = item.find_element(By.CSS_SELECTOR, 'div[class="dc5041d860 c72df67c95 fb60b9836d"]').text.strip()
                        type_span = item.find_elements(By.CSS_SELECTOR, 'span[class="b6f930dcc9"]')
                        if type_span:
                            type_text = type_span[0].text.strip()
                            name = name.replace(type_text, "").strip()
                        distance = item.find_element(By.CSS_SELECTOR, 'div[class="a53cbfa6de f45d8e4c32 cea0c192d7"]').text.strip()
                        return f"{name}, {distance}"
            except Exception:
                continue
        return "-1"
    except Exception:
        return "-1"

def allows_pets(driver) -> str:
    """Check if pets are allowed at the property."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, 'div[class="a53cbfa6de"]')
        for element in elements:
            try:
                text = element.text.strip()
                lines = text.split('\n')
                for line in lines:
                    if "Zwierzęta są akceptowane" in line:
                        return "1"
            except Exception:
                continue
        return "0"
    except Exception:
        return "0"

def get_check_in(driver) -> str:
    """Extract the check-in time range."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, 'div[class="a53cbfa6de"]')
        for element in elements:
            try:
                text = element.text.strip()
                if re.match(r"Od \d{1,2}:\d{2} do \d{1,2}:\d{2}", text):
                    return text
            except Exception:
                continue
        return "-1"
    except Exception:
        return "-1"

def get_check_out(driver) -> str:
    """Extract the check-out time."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, 'div[class="a53cbfa6de"]')
        for element in elements:
            try:
                text = element.text.strip()
                if re.match(r"Do \d{1,2}:\d{2}", text):
                    return text
            except Exception:
                continue
        return "-1"
    except Exception:
        return "-1"

def get_price_per_person(driver) -> float:
    """Extract the price per person."""
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, 'span[class="bui-u-sr-only"]')
        price_text = elements[1].text.replace(' ', '')
        persons_text = elements[0].text
        price_match = re.search(r'(\d+)\s*zł', price_text)
        persons_match = re.search(r'\b(\d+)\b', persons_text)
        if price_match and persons_match:
            return float(price_match.group(1)) / int(persons_match.group(1))
        return 0.0
    except Exception:
        return 0.0