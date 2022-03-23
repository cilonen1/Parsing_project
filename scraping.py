from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import re
import time
from selenium.webdriver.common.action_chains import ActionChains
from collections import *
import numpy as np
import pandas as pd

def first_coef(driver, pi, col_n, row):
    """
    Collecting opening odds of the game 

    Parameters
    ----------
    init_row : int
        start row number for searching
    pi: int
        column number of the sportsbook
    col_n: int
        column number of the team

    Returns
    ---------
    row: float
        opening odds for the team
    """
    book = driver.find_elements_by_class_name('table-main.detail-odds.sortable')
    opup =  book[0].find_elements_by_xpath(f'//*[@id="odds-data-table"]/div[{row}]/table/tbody/tr[{pi}]/td[{col_n}]')[0]
    actions = ActionChains(driver)
    actions.move_to_element(book[0])
    actions.click(opup)
    actions.perform()
    #taking data from popup
    string = driver.find_element_by_xpath("//*[@id='tooltiptext']")
    odds1 = string.text
    return float(odds1.split('\n')[-1].split(' ')[-1])

def count_row(driver, init_row, pi, all_hd, url):
    """
    Looking for row number of needful sportsbook 

    Parameters
    ----------
    init_row : int
        start row number for searching
    pi: int
        column number of the sportsbook
    all_hd: list
        list of possible handicaps for the game

    Returns
    ---------
    row: int
        number of row of needful sportsbook
    """
    driver.get(url)#не обновляется с 1-го раза
    book = driver.find_elements_by_class_name('table-main.detail-odds.sortable')
    for row in range(init_row, len(all_hd) + 20):
        if book[0].find_elements_by_xpath(f'//*[@id="odds-data-table"]/div[{row}]/table/tbody/tr[{pi}]/td[3]'):
            break
    return row

def get_odds(game, driver, hd, all_hd, link, url, sportsbook):
    if float(hd) in all_hd:
        init_row = all_hd.index(float(hd))+1
        url = game + link + hd + ';0'
        driver.get(url)
        driver.get(url)#don't refresh from the 1st time
        book = driver.find_elements_by_class_name('table-main.detail-odds.sortable')
        #looking for pinnacle
        num = len(book[0].find_elements_by_tag_name("tr"))
        pi = 0
        for i in range(num):
            pinc = book[0].find_elements_by_tag_name("tr")[i].text.split('\n')[0].strip(' ')
            if pinc == sportsbook:
                #print(i, pinc)
                pi = i
                break
        if pi != 0:#row number of sportsbook in handicap(for each handicap row number could be different for the same sportsbook)
            row = count_row(driver, init_row, pi, all_hd, url)
            book = driver.find_elements_by_class_name('table-main.detail-odds.sortable')
            last1 = book[0].find_elements_by_xpath(f'//*[@id="odds-data-table"]/div[{row}]/table/tbody/tr[{pi}]/td[3]')[0].text
            last2 = book[0].find_elements_by_xpath(f'//*[@id="odds-data-table"]/div[{row}]/table/tbody/tr[{pi}]/td[4]')[0].text
            first1 = first_coef(driver, pi, 3, row)
            first2 = first_coef(driver, pi, 4, row)
            return first1, first2, last1, last2
        else:
            return np.zeros(4)

def collect_data(league, year, low_board=1.68, high_board=2.25):
    """
    Download data first/last odds from oddsportal.com for total and handicap

    Parameters
    ----------
    league: str
        name of league in format 'brazil/serie-a'
    year: str
        year in format '2021'
    sportsbook: str
        name of sportsbook

    Returns
    ---------
    odds_df:
        dataframe with game's results and odds
    """
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(f'https://www.oddsportal.com/soccer/{league}-{year}/results/1')
    page = driver.find_element_by_id('pagination').text
    pages = max([int(i) for i in re.findall('\d+', page)[0]]) + 1
    matches_id = []
    for p in range(1, pages):
        driver.get(f'https://www.oddsportal.com/soccer/{league}-{year}/results/#/page/{p}')
        driver.get(f'https://www.oddsportal.com/soccer/{league}-{year}/results/#/page/{p}')
        match_id = driver.find_elements_by_class_name("name.table-participant [href]")
        matches_id.extend([el.get_attribute('href') for el in match_id])

    season_odd = []
    sportsbook = 'Pinnacle'
    hd_range = ['-2.50', '-2.00', '-1.50', '-1.00', '-0.50', '0.00', '0.50', '1.00', '1.50']
    hd_bins = np.array([1.05, 1.25, 1.45, 1.7, 1.85, 2.25, 2.8, 3.8, 5.5])
    func = lambda x: x-2 if x >1 else x
    for game in matches_id[:4]:
        #This part helps to get rid of scrapping ALL hd, we take k1 and put to bin
        url = game
        time.sleep(0.25)
        driver.get(url)
        start = driver.find_elements_by_class_name('table-main.detail-odds.sortable')
        st_point = np.digitize(float(start[0].text.split('\n')[2]), hd_bins)
        st_point = func(st_point)
        
        url = game + '#ah;2;'
        driver.get(url)
        driver.get(url)
        dt = driver.find_elements_by_css_selector("p[class^='date datet']")
        date = dt[0].text.split(',')[1]
        odds_game = driver.find_element_by_id('col-content')
        teams = odds_game.text.split('\n')[0]
        res = driver.find_elements_by_class_name('result')
        score = res[0].text.split(' ')[2]
        goal1, goal2 = score.split(':')
        print(date, teams, goal1, '-', goal2)
        
        all_hd = []
        #download all handicaps
        start = driver.find_elements_by_class_name('table-header-light.even')
        for el in start:
            all_hd.append(el.text.split(' ')[2].split('\n')[0])
        start = driver.find_elements_by_class_name('table-header-light.odd')
        for el in start:
            all_hd.append(el.text.split(' ')[2].split('\n')[0])
        all_hd = sorted([float(i) for i in all_hd])
        
        out_hd, out1, out2, oul1, oul2 = np.zeros(5)
        for hd in hd_range[st_point:]:
            first1, first2, last1, last2 = get_odds(game, driver, hd, all_hd, '#ah;2;', url, sportsbook)
            if low_board < first1 < high_board: 
                if min([first1,first2]) > min([out1, out2]):
                    out_hd, out1, out2, oul1, oul2 = hd, first1, first2, float(last1), float(last2)
                elif first2 <= low_board:
                    break
        print('equal',out_hd, out1, out2, oul1, oul2)        
                            
        url = game + '#over-under;2;'
        driver.get(url)
        time.sleep(0.25)
        driver.get(url)   
        all_tot = []
        #download all totals
        start = driver.find_elements_by_class_name('table-header-light.even')
        for el in start:
            all_tot.append(el.text.split(' ')[1].split('\n')[0].strip('+'))
        start = driver.find_elements_by_class_name('table-header-light.odd')
        for el in start:
            all_tot.append(el.text.split(' ')[1].split('\n')[0].strip('+'))
        all_tot = sorted([float(i) for i in all_tot])
        
        out_tot, tot1, tot2, tol1, tol2 = np.zeros(5)
        for tot in ['2.00', '2.50', '3.00']:
            first1, first2, last1, last2 = get_odds(game, driver, tot, all_tot, '#over-under;2;', url, sportsbook)
            if low_board < first1 < high_board: 
                if min([first1,first2]) > min([tot1, tot2]):
                    out_tot, tot1, tot2, tol1, tol2 = tot, first1, first2, float(last1), float(last2)
                elif first2 <= low_board:
                    break
        print('equal_tot',out_tot, tot2, tot1, tol2, tol1)

        season_odd.append((date, teams.split('-')[0].rstrip(' '), teams.split('-')[1].lstrip(' '), goal1, goal2, 
                        out_hd, out1, out2, oul1, oul2, out_tot, tot2, tot1, tol2, tol1))

    odds_df = pd.DataFrame(season_odd, columns = ['date', 'home', 'away', 'goal1', 'goal2', 'hd', 'k1', 'k2', 'l1', 'l2', 'tot',
                                                'und', 'ov', 'und_l', 'ov_l'])
    odds_df['date']  = odds_df['date'].map(lambda x: datetime.strptime(x, ' %d %b %Y'))

    odds_df.drop_duplicates(inplace=True)
    return odds_df