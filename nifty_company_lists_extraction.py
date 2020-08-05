import bs4
import requests
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('sqlite:///OneDrive/Desktop\Projects/Fundamental Analysis_Stock Market/nifty50_companies.db?check_same_thread=False')

res = requests.get('https://www.moneycontrol.com/stocks/marketstats/indexcomp.php?optex=NSE&opttopic=indexcomp&index=9', timeout = 2,
headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)", "Referer": "http://example.com"})

# Check if the webpage has been correctly parsed
try:
    res.raise_for_status()
except:
    print('Error in parsing the webpage')
soup = bs4.BeautifulSoup(res.content, 'html.parser')

nifty50_table = soup.find(class_ = 'tbldata14 bdrtpg')
nifty_table_list = nifty50_table.find_all('tr')

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

df.to_sql('nifty50', con = engine, if_exists = 'replace')