import bs4
import pandas as pd
import requests
from sqlalchemy import create_engine
from time import sleep


def financial_statement(company_info, type_num, format_num, financial_type):
    # Company_Info: A tuple containing long code and short code notations of company
    # These codes will be used to create URL of the financial statements
    # Type_num: Consolidated: 1 / Standalone: 0
    # Format_num: New: 1 / Old: 0
    count = 0
    list_profit_loss = []
    while True:
        url = url_creation(company_info, type_num, format_num, count, financial_type)
        res = requests.get(url,
        headers = {"User-Agent":
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1 (.NET CLR 3.5.30729)", "Referer":
        "http://example.com"})

        try:
            res.raise_for_status()
        except:
            break

        soup = bs4.BeautifulSoup(res.content, 'html.parser')
        # Arriving at table of profit and loss statement with classes and ids
        table_data = soup.find(
            class_='tab-pane fade active in', id='standalone-new')
        if table_data == None:
            break
        table_body = table_data.find(class_='mctable1')

        table_for_columns = table_data.find_all('tr')
        list_of_columns = []
        for i in table_for_columns:
            list_of_columns.append(i.find('td').text)
        list_of_columns = [i for i in list_of_columns if i != u'\xa0']

        # Each element of table_body_list = row of profit and loss statement
        table_body_list = table_body.find_all('td')
        list_of_elements = []
        for i in table_body_list:
            list_of_elements.append(i.text)
        list_of_elements = [i for i in list_of_elements if i != u'\xa0']

        # Removing company specific information from the initial heading of all 3 statements so that multiple companies data
        # can be stored in one database table
        for i in range(len(list_of_columns)):
            if list_of_columns[i].startswith('Profit & Loss account of'):
                list_of_columns[i] = 'Profit and Loss Statement'
                break
            if list_of_columns[i].startswith('Balance Sheet of'):
                list_of_columns[i] = 'Balance Sheet Statement'
                break
            if list_of_columns[i].startswith('Cash Flow of'):
                list_of_columns[i] = 'Cash Flow Statement'
                break

        for i in range(len(list_of_elements)):
            if list_of_elements[i].startswith('Profit & Loss account of'):
                list_of_elements[i] = 'Profit and Loss Statement'
                break
            if list_of_elements[i].startswith('Balance Sheet of'):
                list_of_elements[i] = 'Balance Sheet Statement'
                break
            if list_of_elements[i].startswith('Cash Flow of'):
                list_of_elements[i] = 'Cash Flow Statement'
                break

        # Finding number of columns
        num_cols = 0
        for i in list_of_elements:
            if i.startswith('Mar') and len(i) == 6:
                num_cols += 1

        dict_data = {}
        for i in list_of_columns:
            if i in list_of_elements:
                num = list_of_elements.index(i)
                dict_data[i] = list_of_elements[num + 1: num + num_cols + 1]

        count = count + 1
        # Check if the data is repeating (e.g. this case happened with axis bank)
        if dict_data in list_profit_loss:
            break
        list_profit_loss.append(dict_data)

    # Combining the list of dictionaries to a single dictionary
    combined_dict = merge_dictionary(list_profit_loss)

    # Converting combined dictionary to pandas dataframe
    df_profit_loss = pd.DataFrame.from_dict(combined_dict)

    return df_profit_loss


def url_creation(company_info, type_num, format_num, count, financial_type):
    # Company_Info: A tuple containing long code and short code notations of company
    # These codes will be used to create URL of the financial statements
    # Type_num: Consolidated: 1 / Standalone: 0
    # Format_num: New: 1 / Old: 0
    # Example of webpages for profit and loss statement
    # Webpage 1: https://www.moneycontrol.com/financials/larsen&toubro/consolidated-profit-lossVI/LT#LT
    # Webpage 2: https://www.moneycontrol.com/financials/larsen&toubro/consolidated-profit-lossVI/LT/2#LT
    # Webpage 3: https://www.moneycontrol.com/financials/larsen&toubro/consolidated-profit-lossVI/LT/3#LT

    # Financial type = profit-loss / balance-sheet / cash-flow

    if type_num == 1:
        type_string = 'consolidated-'
    else:
        type_string = ''

    if format_num == 1:
        format_string = 'VI'
    else:
        format_string = ''

    if count == 0:
        url = ('https://www.moneycontrol.com/financials/' + company_info[0] + '/' + type_string + financial_type + format_string + '/' + company_info[1] +
               '#' + company_info[1])
    else:
        url = ('https://www.moneycontrol.com/financials/' + company_info[0] + '/' + type_string + financial_type + format_string + '/' + company_info[1] +
               '/' + str(count + 1) + '#' + company_info[1])
    return url


def merge_dictionary(list_of_dict):
    master_dict = {}
    for i in list_of_dict:
        for k, v in i.items():
            if k not in master_dict:
                master_dict[k] = v
            else:
                temp_list = master_dict[k]
                temp_list.extend(v)
                master_dict[k] = temp_list
    return master_dict


def dataframes_merge(dataframes_list):
    # This function merge dataframes for different companies which have same columns (i.e. structure of financial statements is identical)
    concat_index = []
    for i in range(len(dataframes_list)):
        for j in range(len(dataframes_list))[i+1:]:
            if j in concat_index:
                continue
            elif list(dataframes_list[i].columns) == list(dataframes_list[j].columns):
                concat_index.append(j)
                dataframes_list[i] = dataframes_list[i].append(dataframes_list[j], ignore_index = True)

    # Deleting the dataframes that has already been merged in similar structured dataframes
    for i in sorted(concat_index, reverse = True):
        del dataframes_list[i]
    return dataframes_list


def check_duplicate_columns(df):
    columns_list = list(df.columns)
    columns_list = [i.lower() for i in columns_list]
    if len(columns_list) == len(set(columns_list)):
        return df
    l = len(columns_list)
    for i in range(l):
        if columns_list.count(columns_list[i]) == 1:
            continue
        else:
            count = columns_list.count(columns_list[i])
            num = 1
            for j in range(i+1, l):
                if columns_list[j] == columns_list[i]:
                    columns_list[j] = columns_list[j] + str(num)
                    num = num + 1
                    count = count - 1
                if count == 0:
                    break
    df.columns = columns_list
    return df


# Extract the Company Codes from various tables in nifty lists
engine = create_engine('sqlite:///OneDrive/Desktop/Projects/Fundamental Analysis_Stock Market/nifty_lists.db?check_same_thread=False')
tables_list = engine.table_names()
df_list = []
for i in tables_list:
    df = pd.read_sql_table(i, engine)
    df_list.append(df)

total_df = pd.concat(df_list).drop_duplicates().reset_index(drop=True)
type_num = 1
format_num = 1
list_of_dataframes = []
sleep_counter = 0
for i, j, k, l in (zip(total_df['Long Code'].tolist(), total_df['Short Code'].tolist(), total_df['Company Sector'].tolist(),
                       total_df['Company Name'].tolist())):
    if sleep_counter != 0:
        print('Sleeping for 5 seconds before beginning data extraction of next company')
        sleep(5)
    sleep_counter += 1
    print('Extracting information of company:{}'.format(l))
    company_info_tuple = (i, j)
    profit_loss = financial_statement(company_info_tuple, type_num, format_num, 'profit-loss')
    balance_sheet = financial_statement(company_info_tuple, type_num, format_num, 'balance-sheet')
    balance_sheet = balance_sheet.rename({'NON-CURRENT INVESTMENTS' : 'NON-CURRENT INVESTMENTS-HEADER'}, axis = 1)
    balance_sheet = balance_sheet.rename({'CURRENT INVESTMENTS' : 'CURRENT INVESTMENTS-HEADER'}, axis = 1)
    cash_flow = financial_statement(company_info_tuple, type_num, format_num, 'cash-flow')
    pl_bs_combined = profit_loss.join(balance_sheet, lsuffix='_profit and loss', rsuffix='_balance sheet')
    combined_dataframe = pl_bs_combined.join(cash_flow, rsuffix = '_cash flow')
    combined_dataframe['Sector'] = len(combined_dataframe) * [k]
    combined_dataframe['Company'] = len(combined_dataframe) * [l]
    # Check for duplicate columns in the dataframe
    # If there are duplicate columns, the function renames columns to avoid problem in pushing dataframes to database tables
    combined_dataframe = check_duplicate_columns(combined_dataframe)
    list_of_dataframes.append(combined_dataframe)
    print('Extracting information of company:{} is complete'.format(l))

list_of_dataframes = dataframes_merge(list_of_dataframes)

engine2 = create_engine('sqlite:///OneDrive/Desktop/Projects/Fundamental Analysis_Stock Market/financial_statement_data.db?check_same_thread=False')
count = 1
for i in list_of_dataframes:
    table_name = 'Table' + str(count)
    i.to_sql(table_name, con = engine2, if_exists = 'replace')
    count = count + 1