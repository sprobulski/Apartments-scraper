# scripts/run_scraper.py
import time
import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
from src.scraper import BookingScraper

def main():
    with BookingScraper() as scraper:
        scraper.land_first_page()
        time.sleep(3)
        scraper.select_place_to_go("Grudziądz")
        scraper.select_dates("2025-04-12", "2025-04-13")
        time.sleep(1)
        scraper.select_adults(2)
        scraper.search()
        scraper.close_popup()
        time.sleep(2)
        scraper.apply_filters()
        df = scraper.collect_results()
        print(df)

if __name__ == "__main__":
    main()