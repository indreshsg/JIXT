"""
######################################################################
######################################################################
                    Journal Scrapper
    
Scraps web of science journal list and creates a database of
journal information with abbreviation for the Journal Names

Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""
import requests
from bs4 import BeautifulSoup as BS
import os

url_query_start = "http://images.webofknowledge.com/images/help/WOS/"
url_query_end = "_abrvjt.html"


field_list = ['0-9', 'A']
csv_field_names = ['journal', 'abbreviation']

#Populate the field list with letters from A-Zero
for i in range(1, 26):
    start = ord(field_list[1])
    letter = chr(start + i)
    field_list.append(letter)

csvFile = open('journal_database.txt', 'w')
csvFile.write("|".join(csv_field_names) + '\n')

#Scarp the web of science and create a list
for element in field_list:
    url_query = url_query_start + element + url_query_end
    response = requests.get(url_query)
    soup = BS(response.content, "html5lib")
    
    print('Processing Query:', element)

    for journal_name in soup.findAll('dt'):
        name = journal_name.get_text().rstrip()
        name = name.strip('"')
        abbr = journal_name.next_sibling.get_text().rstrip()
        csvFile.write(name + "|" + abbr + '\n')
     
    print('Done Processing Query:', element)
    
csvFile.close()  