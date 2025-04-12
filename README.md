# BookingScraper

## Overview  
`BookingScraper` is a Python-based web scraping tool designed to extract hotel data from the Polish version of Booking.com. This project was created for **educational purposes only** to demonstrate web scraping techniques using Selenium, data processing with pandas, and automation of dynamic websites. It collects information such as hotel names, ratings, facilities, check-in/check-out times, and more, saving the results to a CSV file.  

**Note**: This script is tailored to work with the Polish version of Booking.com (e.g., selectors and text patterns are in Polish). It is not intended for production use or to scrape Booking.com without permission.  

---

## Disclaimer  
This project is for **educational purposes only**. Scraping Booking.com may violate its [Terms of Service](https://www.booking.com/content/terms.html). Do not use this code to scrape Booking.com or any other website without explicit permission from the website owner. The author is not responsible for any misuse of this code or any consequences arising from its use. Always respect the legal and ethical guidelines of web scraping, including compliance with applicable laws (e.g., GDPR, CFAA) and website policies.  

---

## Features  
- Scrapes hotel data from the Polish version of Booking.com, including:  
  - Hotel name, district, distance from center  
  - Ratings (overall, staff, facilities, cleanliness, etc.)  
  - Facilities (e.g., Wi-Fi, TV, kitchen, balcony)  
  - Languages spoken by staff  
  - Room size, nearest attraction, restaurant, transport  
  - Check-in/check-out times, pet policy, price per person  
- Handles dynamic content (e.g., "Load more" button) and deduplicates results  
- Saves scraped data to a CSV file (`output/booking_results.csv`)  
- Includes error handling and logging for debugging  
- Modular design with separate utility and extraction functions  

---

## Prerequisites  
Before running the script, ensure you have the following installed:  

- **Python 3.8+**  
- **Google Chrome** (matching the version of ChromeDriver)  
- **ChromeDriver**:  
  - Download the appropriate version of [ChromeDriver](https://chromedriver.chromium.org/downloads) for your Chrome browser.  
  - Place the `chromedriver` executable in the directory specified in the script (default: `C:\SeleniumDriver`), or update the `driver_path` in the script to match your location.  

### Install Python Dependencies  
```bash
pip install -r requirements.txt
```
## Setup & Usage

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/booking-scraper.git
cd booking-scraper
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Scraper
Navigate to the project root and execute:

```bash
python -m scripts.run_scraper
```

**Output:**  
Data will be saved to `output/booking_results.csv`.

### Customize Parameters (Optional)
Edit `scripts/run_scraper.py` to modify:
- Location (e.g., `"Warszawa"`)
- Dates (e.g., `"2025-05-01"` to `"2025-05-05"`)
- Number of adults (e.g., `scraper.select_adults(4)`)

## Limitations
- **Language Specific**: Works only with the Polish version of Booking.com
- **Dynamic Content**: Website updates may break selectors
- **Legal Compliance**: Scraping without permission violates Booking.com's ToS
- **No Headless Mode**: Runs in visible browser mode by default

## Future Improvements
- Add multi-language support
- Implement configuration files for parameters
