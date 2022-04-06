import argparse
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from scraping import collect_data

parser = argparse.ArgumentParser(description='Collect league and year')
parser.add_argument('league', type=str)
parser.add_argument('start_year', type=int)
parser.add_argument('end_year', type=int)
args = parser.parse_args()
driver = webdriver.Chrome(ChromeDriverManager().install())
for year in range(args.start_year, args.end_year + 1):
    odds_df = collect_data(args.league, year, driver)
    country = args.league.split('/')[0]
    odds_df.to_excel(f'{country}_{year}.xlsx')