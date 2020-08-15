import bs4
import requests
import pandas as pd
from sqlalchemy import create_engine

# Nifty lists are updated once in six months. There is no provision in the code to update the existing lists in database table
# Each time this program is run, the existing database tables are replaced / overwritten
def nifty_list_extraction(url):
    res = requests.get(url, timeout = 2, headers = {"User-Agent": 
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)",
    "Referer": "http://example.com"})

    # Check if the webpage has been correctly parsed
    try:
        res.raise_for_status()
    except:
        return 'Error in parsing the webpage'
    soup = bs4.BeautifulSoup(res.content, 'html.parser')

    nifty_table = soup.find(class_ = 'tbldata14 bdrtpg')
    nifty_table_list = nifty_table.find_all('tr')

    company_details = []
    for i in nifty_table_list[1:]:
        company_details.append(i.find_all('b'))

    company_details = [(i[0].text, i[1].text) for i in company_details]

    # Extracting company codes from href tag in the list (these codes will be used to prepare URLs while parsing financial statements)
    url_ref = []
    for i in nifty_table_list[1:]:
        url_ref.append(i.a['href'])
    codes_list = []
    for i in url_ref:
        codes_list.append((i.split('/')[-2], i.split('/')[-1]))

    # Master list is a list of tuples (Company name, Company sector, long code, short code)
    # Long code and short code will be used to create URL address while extracting financial data of the company
    master_list = []
    for i, j in zip(company_details, codes_list):
        master_list.append(i + j)

    columns_list = ['Company Name', 'Company Sector', 'Long Code', 'Short Code']
    df = pd.DataFrame(master_list, columns = columns_list)

    list_outer_class = soup.find(class_ = 'PT15')
    list_name = list_outer_class.find_all(class_ = 'gL_12 PT15')[1].find('b').text
    return df, list_name

# url_1 = URL for nifty50
url_1 = 'https://www.moneycontrol.com/stocks/marketstats/indexcomp.php?optex=NSE&opttopic=indexcomp&index=9'
# url_2 = URL for nifty50 USD
url_2 = 'https://www.moneycontrol.com/stocks/marketstats/indexcomp.php?optex=NSE&opttopic=indexcomp&index=8'
# url_3 = URL for nifty next 50
url_3 = 'https://www.moneycontrol.com/stocks/marketstats/indexcomp.php?optex=NSE&opttopic=indexcomp&index=6'
url_list = [url_1, url_2, url_3]
# More URLs can be added to the above list in future to expand number of companies for which fundamental analysis is to be performed

engine = create_engine('sqlite:///OneDrive/Desktop/Projects/Fundamental Analysis_Stock Market/nifty_lists.db?check_same_thread=False')

for i in url_list:
    df, list_name = nifty_list_extraction(i)
    df.to_sql(list_name, con = engine, if_exists = 'replace')