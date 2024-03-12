#!/bin/env python3
#
# This project can scrape the CPU Mega Page at:
# https://www.cpubenchmark.net/CPU_mega_page.html
#
# It uses requests_html library
# https://requests.readthedocs.io/projects/requests-html/en/latest/
#

import sys
import time
from requests_html import HTMLSession

MEGA_PAGE_URL = 'https://www.cpubenchmark.net/CPU_mega_page.html'

def int_with_default(text, default_int):
    '''
    Convert input to integer or return default if parsing failed
    
    @param text input text to convert
    @param default_int default integer to use if parsing failed
    
    @returns converted int or default
    '''
    try:
        return int(text)
    except:
        return int(default_int)

def parse_tr_tds(row):
    '''
    Parse all table rows from CPU Mega Page

    @param row row to parse
    
    @returns
      dictionary
    '''
    tmp = row.find('td')
    d = {}
    for idx, td in enumerate(tmp):
        if idx == 1:
            d['cpu_name'] = td.text
        elif idx == 2:
            d['cores'] = int_with_default(td.text, -1)
        elif idx == 3:
            d['cpu_mark'] = int_with_default(td.text.replace(',', ''), -1)
        elif idx == 4:
            d['thread_mark'] = int_with_default(td.text.replace(',', ''), -1)
        elif idx == 5:
            d['tdp'] = int_with_default(td.text, -1)
        elif idx == 6:
            d['socket'] = td.text
        elif idx == 7:
            d['category'] = td.text
    return d

def format_csv(items):
    '''
    Format items as CSV output

    @param items items
    
    @stdout
        CSV output
    '''
    print('cpu_name;cores;cpu_mark;thread_mark;tdp;socket;category')
    for item in items:
        print(f'{item['cpu_name']};{item['cores']};{item['cpu_mark']};{item['thread_mark']};{item['tdp']};{item['socket']};{item['category']}')

def append_no_duplicates(items, new_items):
    '''
    Add items without duplicates

    @param items item list
    @param new_items new items to add
    '''
    #items += page_items
    for new_item in new_items:
        if not new_item in items:
            items.append(new_item)
    return items

def get_page_data(r, items, page):
    '''
    Get data from the mega page
    
    @param r request_html object
    @param items list of items to add new items to
    @param page page number to use
    
    @returns
        True if everything has been done already, False otherwise
    '''
    script = """
() => {
function goNext() {
  el = document.getElementById("cputable_next");
  el.querySelector("a").click();
}

function sleepFor(sleepDuration){
    var now = new Date().getTime();
    while(new Date().getTime() < now + sleepDuration){ 
        /* Do nothing */ 
    }
}

setTimeout(function(){
"""

    last_item = { 'cpu_name': None }
    if len(items) > 0:
        last_item = items[len(items) - 1]
    for i in range(1, page):
        script += "sleepFor(100);  goNext();"

    script += """   
}, 3000);
}
"""

    sleep_time = (3 + (page * 0.1)) + 2;

    r.html.render(script=script, reload=True, sleep=sleep_time)
    data = r.html.find("#cputable", first=True)
    tbody = data.find("tbody", first=True)

    trs = tbody.find("tr")
    page_items = []
    for tr in trs:
        page_items.append( parse_tr_tds(tr) )
        
    done = (page_items[len(page_items) - 1]['cpu_name'] == last_item['cpu_name'])
    if not done:
        items = append_no_duplicates(items, page_items)

    return done

def parse_all_pages(url):
    '''
    Parse all the pages from CPU Mega Page
    
    @param url page URL
    
    @return
        items dictionary
    '''
    session = HTMLSession()
    r = session.get(url)
    r.html.render(sleep=5)
    data = r.html.find("#cputable", first=True)
    tbody = data.find("tbody", first=True)
    nxt = r.html.find("#cputable_next", first=True)

    items = []
    trs = tbody.find("tr")
    for tr in trs:
        items.append( parse_tr_tds(tr) )

    i = 2
    done = False
    while not done:
        done = get_page_data(r, items, i)
        i = i + 1

    session.close()
    return items

items = parse_all_pages(MEGA_PAGE_URL)
format_csv(items)

print('Finished. Found %s entries.' % len(items), file=sys.stderr)

