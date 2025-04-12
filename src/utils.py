# src/utils.py
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import re

def get_element_text(element, selector: str, default: str) -> str:
    """Extract text from an element using a CSS selector.

    Args:
        element: The WebElement to search within.
        selector (str): CSS selector to locate the element.
        default (str): Default value if the element is not found.

    Returns:
        str: The extracted text or default value.
    """
    try:
        return element.find_element(By.CSS_SELECTOR, selector).text.strip()
    except NoSuchElementException:
        return default

def extract_review_count(review_text: str) -> str:
    """Extract the number of reviews from a review text string.

    Args:
        review_text (str): Text containing the review count.

    Returns:
        str: The extracted review count or "0" if not found.
    """
    try:
        match = re.match(r'(\d+)\s+', review_text)
        if match:
            return match.group(1)
        return "0"
    except Exception:
        return "0"