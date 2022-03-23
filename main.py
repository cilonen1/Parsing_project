import argparse
from scraping import collect_data
parser = argparse.ArgumentParser(description='Collect league and year')
parser.add_argument('league', type=str)
parser.add_argument('year', type=str)
args = parser.parse_args()
odds_df = collect_data(args.league, args.year)