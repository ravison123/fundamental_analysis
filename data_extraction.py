import bs4
import requests
import pandas as pd


def profit_and_loss(company_info, type_num, format_num, count):
    # Company_Info: A list containing full form and short form notations of company
    # Type_num: Consolidated: 1 / Standalone: 0
    # Format_num: New: 1 / Old: 0
    if type_num == 1:
        type_string = 'consolidated-'
    else:
        type_string = ''
    
    if format_num == 1:
        format_string = 'VI'
    else:
        format_string = ''

    if count == 0:
        url = ('https://www.moneycontrol.com/financials/' + company_info[0] + '/' + type_string + 'profit-loss' + format_string + '/' + company_info[1] +
        '#' + company_info[1])
    else:
        url = ('https://www.moneycontrol.com/financials/' + company_info[0] + '/' + type_string + 'profit-loss' + format_string + '/' + company_info[1] +
        '/' + str(count + 1) + '#' + company_info[1])

    # Example of webpages
    # Webpage 1: https://www.moneycontrol.com/financials/larsen&toubro/consolidated-profit-lossVI/LT#LT
    # Webpage 2: https://www.moneycontrol.com/financials/larsen&toubro/consolidated-profit-lossVI/LT/2#LT
    # Webpage 3: https://www.moneycontrol.com/financials/larsen&toubro/consolidated-profit-lossVI/LT/3#LT

    res = requests.get(url)
    try:
        res.raise_for_status()
    except:
        return 'Webpage not valid'

    soup = bs4.BeautifulSoup(res.content, 'html.parser')
    # Arriving at table of profit and loss statement with classes and ids
    table_data = soup.find(class_ = 'tab-pane fade active in', id = 'standalone-new')
    if table_data == None:
        return 'Webpage not valid'
    table_body = table_data.find(class_ = 'mctable1')


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

    # Finding number of columns
    num_cols = 0
    for i in list_of_elements:
        if i.startswith('Mar') and len(i) == 6:
            num_cols += 1
            

    # Renaming first column name (in both list_of_columns and list_of_elements) so that data from multiple companies can be clubbed together
    for i in range(len(list_of_columns)):
        if list_of_columns[i].startswith('Profit & Loss account of'):
            list_of_columns[i] = 'Profit & Loss Statement of Year'
            break
    for i in range(len(list_of_elements)):
        if list_of_elements[i].startswith('Profit & Loss account of'):
            list_of_elements[i] = 'Profit & Loss Statement of Year'
            break

    dict_data = {}
    for i in list_of_columns:
        if i in list_of_elements:
            num = list_of_elements.index(i)
            dict_data[i] = list_of_elements[num + 1: num + num_cols + 1]

    # Adding company name to dict_data
    length = len(dict_data['Profit & Loss Statement of Year'])
    dict_data['Company'] = length * [company_info[0]]

    # Adding type of profit and loss statement to dict_data
    if type_num == 1:
        dict_data['Type of Statement'] = length * ['Consolidated']
    else:
        dict_data['Type of Statement'] = length * ['Standalone']

    # Adding format of profit and loss statement to dict_data
    if format_num == 1:
        dict_data['Format'] = length * ['New']
    else:
        dict_data['Format'] = length * ['Old']
    
    return dict_data

list_of_dict = []
# Create a dictionary of tuples for Nifty 50 companies
company_info = ({'Tata Motors' : ('tatamotors', 'tm03'), 'Adani Ports' : ('adaniportsandspecialeconomiczone', 'MPS'),
'Sun Phrama' : ('sunpharmaceuticalindustries', 'SPI'), 'Cipla' : ('cipla', 'C'), 'Grasim Industries' : ('grasimindustries', 'gi01'),
'JSW Steel' : ('jswsteel', 'jsw01'), 'UPL Ltd' : ('upl', 'up04'), 'SBI' : ('statebankofindia', 'SBI'),
'Mahindra and Mahindra' : ('mahindramahindra', 'MM'), 'Axis Bank' : ('axisbank', 'ab16'), 'HCL Tech' : ('hcltechnologies', 'hcl02')})
type_num = 1
format_num = 1
for i, j in company_info.items():
    count = 0
    while True:
        dic = profit_and_loss(j, type_num, format_num, count)
        if dic == 'Webpage not valid':
            break
        list_of_dict.append(dic)
        count = count + 1

# Combining all dictionaries
master_dict = {}
for i in list_of_dict:
    for k, v in i.items():
        if k not in master_dict:
            master_dict[k] = v
        else:
            temp_list = master_dict[k]
            temp_list.extend(v)
            master_dict[k] = temp_list
            
df = pd.DataFrame.from_dict(master_dict)