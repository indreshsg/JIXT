"""
######################################################################
######################################################################
                        Journal Search
    
Descp: Searches for journal names from the index created by Whoosh
if match is found returns the title of the match

Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""

import re
import os
import sys
import whoosh.index as index
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
import whoosh.qparser as Qparser
from whoosh.query import FuzzyTerm
from whoosh import scoring
from fuzzywuzzy import process
import load_config
import calendar
from difflib import SequenceMatcher
import jellyfish
import author_tagger

glbl_quote_marker = 'aaaa'

"""
Check if a given string has any digit
"""
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)
        
"""
creates Ngram from a list
"""
def list_Ngrams(input_list, n):
  return list(zip(*[input_list[i:] for i in range(n)]))
    
"""
remove any month name from given list
"""
def removeMonth(str_lst):
    for month_idx in range(1, 13):
        month_name = calendar.month_name[month_idx].lower()
        month_abbr = calendar.month_abbr[month_idx].lower()
        str_lst = [each.replace(month_name, " ")  for each in str_lst]
        str_lst = [each.replace(month_abbr, " ")  for each in str_lst]
    return str_lst
    
"""
Remove any http links present in the text
"""
def strip_http(full_string):
    http_index = full_string.find("http")-1
    full_string = full_string[:http_index]
    return full_string
    
"""
provides sequence match ratio between a string and list
"""
def similar(srch_str, lookup_lst):
    high_score = 0.0
    match_title = ''
    for each_item in lookup_lst:
        #score = SequenceMatcher(None, srch_str, each_item).ratio()
        score = jellyfish.jaro_distance(srch_str, each_item)
        #print(srch_str + "|" + each_item + "|" + str(score))
        if score > high_score:
            match_title = each_item
            high_score = score
    #print("########" + match_title + "|" + str(high_score))
    return [match_title, high_score]

"""
Get the index of the first marker from the given string
"""
def marker_index(full_string):
    spec_chars = set(""":?'";,0123456789!()~#@^&$%*""")
    for chars in full_string:
        if chars in spec_chars:
            return full_string.index(chars)
    return len(full_string)
    
"""
finds a probable full name by using markers like : , ' etc
returns the probable name
"""    
def strip_using_marker(full_string, key_word):
    full_string = strip_http(full_string)
    
    #remove any of the following ()-?
    full_string = re.sub('[-|.|\|/]', ' ', full_string)
    
    if key_word not in full_string:
        return None
         
    pivot = full_string.index(key_word)
    #Search for any special character from the pivot   
    rvrse_fullstr = ''.join(reversed(full_string[:pivot]))
        
    start_index = pivot - marker_index(rvrse_fullstr)
    end_index = marker_index(full_string[pivot:]) + pivot
    
    #Get full name and removes any spaces in from or back
    prob_name = full_string[start_index:end_index]
    
    #Check if et al is present and name and remove anything before it
    prob_lst = prob_name.split(' ')
    for i in range(0, len(prob_lst)):
        if prob_lst[i] == 'al':
            prob_name = (' ').join(prob_lst[i+1:])
            break
    #Remove any vol keyword
    prob_name = re.sub(r'\bvol\b', ' ', prob_name)
    return prob_name.strip()
    
"""
PIVOT RATIO: gives the ratio of length of pivot string with 
respect to the entire marker seperated string
"""
def pivot_ratio(full_string, key_word):
    marked_string = strip_using_marker(full_string, key_word)
    if marked_string:
        ratio = len(key_word)/len(marked_string)
    else:
        ratio = 0
    return ratio

"""
Check if a given list has 'Journal' present, if so extract the journal
name from the string
"""
def hasJournal(journal_lst, info_str):
    id = 0
    end = 0
    isPresent = False
    
    #Fisrt do a simple search for keyword journal
    word_lst = [word.lower() for word in journal_lst]
    if 'journal' in word_lst:
        id = word_lst.index('journal')
        isPresent = True
    elif 'patent office' in word_lst or 'uspto' in word_lst:
        return [True, 'No journal match']
    else:
        return [isPresent, None]
      
    #If name journal is present, get the full name of journal
    #NOTE: end of name is usually marked by presence of number 
    #or a special charcter ',' in the end
    journal_name = strip_using_marker(info_str.lower(), 'journal')
            
    return [isPresent, journal_name]
    
"""
Gets the index from the first character of journal name
"""
def get_alphaindex(name):
    alpha_index = name.lower()   
    if alpha_index.isdigit():
        alpha_index = 0
    else:
        alpha_index = ord(alpha_index) - ord('a') + 1
        
    alpha_index = 0 if alpha_index > ord('z') else alpha_index
    return alpha_index
    
"""
Search for quotes in the line and return the end of quotes
If no quotes found return -1
"""
def strip_Quote(line_str, quote_marker=None):
    if quote_marker is None:
        quote_marker = glbl_quote_marker
        
    #Remove any apostrophe if found
    line_str = re.sub(r"'s ", ' ', line_str)
    strlen = len(line_str)
    srch_char = "'"
    #Get the firts and last occurence, if either -1, it indicates error
    first = line_str.find(srch_char)
    last = line_str.find(srch_char, first+1)
    #If the no of quotes is odd, return the same string back, else strip
    if first is -1 or last is -1:
        strip_strng =  line_str
    else:
        strip_strng = line_str[:first] + quote_marker + line_str[last+1:]
        
    return strip_strng  
    
"""
From a given list of words, creates N-gram bucket pool
Removes any numbers or special characters if present
"""   
def create_Ngram(str_bucket):
    #Remove special characters, numbers and then et al
    str_bucket = [re.sub(r'\bet\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bal\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\boffice\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bpatent\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bno\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\beuropean\b', ' ', each) for each in str_bucket]
    str_bucket = [re.sub(r'\bny\b', ' ', each) for each in str_bucket]
    #str_bucket = [re.sub(r'\bj\b', 'journal', each) for each in str_bucket]
    #str_bucket = [re.sub(r'\bproc\b', 'proceeding', each) for each in str_bucket]
    str_bucket = removeMonth(str_bucket)
      
    #Remove empty elemnts from end of list
    if str_bucket:
        while not str_bucket[-1]:
            str_bucket.pop()
        
    #Combine multiple spaces into one
    str_bucket = " ".join(str_bucket).split()
    
    #remove quote_marker and replace with double space
    if glbl_quote_marker in str_bucket:
        str_bucket[str_bucket.index(glbl_quote_marker)] = "    "
    
    #Create Gram from list
    Ngram_lst = []
    bucket_len = len(str_bucket)
    for gram in range(2, bucket_len):
        gram_list = list_Ngrams(str_bucket, gram) #create N gram list
        for each in gram_list:
            srch_word = " ".join(each)
            Ngram_lst.append(srch_word)
           
    return Ngram_lst
        
######################################################################
######################################################################
#ournal DB Table Infor
#Min length : 2 
#Max length: Title = 235 and abbrevation = 21
#Min word length: 1
#Max wod length: Title = 31 and abbrevation = 7

"""
Journal Search Class:
sanitize :: will remove any keyword called vol or volume and generate
            a list of words
jrnl_srch :: will first search for word 'Journal' if not present will
            initiate a complex N-gram search through the index file
"""
class jrnl_srch:
    #Load and open the index directory from xml file       
    def __init__(self, log_en):
        config = load_config.load_config()
        index_dir = config.index_foldr
        dbFileName = config.DB_file
        ix = index.open_dir(index_dir)
        self.authr_Tag = author_tagger.author_tag()
        #--------------- READ & CREATE THE DATABASE ----------------------#
        self.jrnl_DB_name_lst = [[]* 27 for i in range(27)]
        self.jrnl_DB_abbrv_lst = [[]* 27 for i in range(27)]   
        DB_index = 0
        #Read DB file and hold a list of all journals    
        with open(dbFileName, 'r') as dbcsvFile:
            db_lines = dbcsvFile.readlines()
            for db_line in db_lines:
                [name, abbrv, type] = db_line.strip('\n').split("|")
                
                alpha_index = get_alphaindex(name[0].lower())
                
                joint_abbrv = abbrv #"_".join(abbrv.split())
                self.jrnl_DB_name_lst[alpha_index].append(name.lower())
                self.jrnl_DB_abbrv_lst[alpha_index].append(joint_abbrv.lower())
                
                DB_index = DB_index + 1                
        print('Total Length of Database: ', DB_index)
        #------------- Create Searher Object for Whoosh -------------------#
        self.searcher = ix.searcher()#weighting=scoring.TF_IDF())
        self.title_parser = MultifieldParser(["title", "content"], ix.schema)
        self.title_parser.add_plugin(Qparser.FuzzyTermPlugin())
        if log_en is True:
            self.log_file = open('debug_results.txt', 'w')
        else:
            self.log_file = None

       
    def try_journal(self, srch_str):
        print(srch_str)
        srchquery = self.title_parser.parse(srch_str)
        results = self.searcher.search(srchquery)
        for i in range(0, results.scored_length()):
            print(results[i]['title'], results.score(i))

    """
    Perform a fuzzy search over DB and create a list of matching context
    """
    def fuzzy_search(self, srch_result_lst):
        title_repo = []
        abbrv_repo = []
        #For each result, serach for matching Levengshtein distance
        for i in range(0, len(srch_result_lst)):
            [srch_str, result] = srch_result_lst[i]
            
            alpha_index = get_alphaindex(srch_str.strip(" ")[0])
            title_match = process.extract( srch_str,   \
                                           self.jrnl_DB_name_lst[alpha_index], \
                                           limit=5)
            abbrv_match = process.extract( srch_str, \
                                           self.jrnl_DB_abbrv_lst[alpha_index], \
                                           limit=5)
            for each_title in title_match:
                title_repo.append(each_title[0])
                
            for each_abbrv in abbrv_match:
                abbrv_text = each_abbrv[0]
                abbrv_index = self.jrnl_DB_abbrv_lst[alpha_index].index(abbrv_text)
                abbrv_repo.append([each_abbrv[0], abbrv_index])
                
        return [title_repo, abbrv_repo]
        
    def get_best_match(self, Ngram_lst, full_str, threshold):
        title_srch_result = []
        positive_grams = []
        #Search through the title list for matches and hold highest score
        for gram_str in Ngram_lst:
            if len(gram_str.split(' ')) > 1:
                srch_str = strip_using_marker(full_str, \
                                              gram_str)
            else:
                srch_str = gram_str
            if srch_str is None:
                continue
            #srchquery = self.title_parser.parse(srch_str)
            #results = self.searcher.search(srchquery)
            if len(srch_str) != 0:                
                title_srch_result.append([srch_str, None])
                #Store the first search the resulted in a hit
                positive_grams.append(srch_str)
                
        #Create a repositry of matching context and title from fuzzy search
        [title_repo, abbrv_repo] = self.fuzzy_search(title_srch_result)
        
        final_lst = []
        abbrv_name_repo = [i[0] for i in abbrv_repo]
        abbrv_indx_repo = [i[1] for i in abbrv_repo]
        #From the first hit in Ngram search, perform another fuzzzy search
        for gram_str in positive_grams:
            [nearest_title, title_score] = similar(gram_str, title_repo)
            [nearest_abbrv, abbrv_score] = similar(gram_str, abbrv_name_repo)
            
            if title_score >= abbrv_score:
                title = nearest_title
                score = title_score
            else:
                alpha_index = get_alphaindex(nearest_abbrv.strip(" ")[0])
                abbrv_index = abbrv_indx_repo[abbrv_name_repo.index(nearest_abbrv)]
                try:
                    title = self.jrnl_DB_name_lst[alpha_index][abbrv_index]
                    score = abbrv_score
                except:
                    continue
            print('***'+gram_str)    
            print(title, score)
            match_dict = {'title':title,'score':score,'str':gram_str}
            final_lst.append(match_dict)
        
        max_score = 0
        #Get value with highest score and highest length
        if final_lst:
            max_dict = max(final_lst, key=lambda item:item['score'])
            max_score = max_dict['score']
        
        #Threshold to classify journal names
        if max_score < threshold:
            return ['No result match', max_score, None]
            
        best_indx = []
        for i in range(0, len(final_lst)):
            match_dict = final_lst[i]
            if match_dict['score'] == max_score:
                best_indx.append([match_dict['title'], len(match_dict['str'])])
        best_len = [i[1] for i in best_indx]
        max_len_indx = best_len.index(max(best_len))
        best_title = best_indx[max_len_indx][0]
            
        return [best_title, max_score, final_lst]
                      
    #Search for journal name across indexed database
    def get_journal(self, info_str): 
        #First sanitize the input string
        journal_lst = srch.sanitize(info_str)
        #Convert everything to lower case
        journal_lst = [each.lower() for each in journal_lst]    
        manirated_info_str = strip_Quote(info_str.lower()," '")
        manirated_info_str = self.authr_Tag.rmv_authors(manirated_info_str)
        
        print(manirated_info_str)
        
        ##------- Level 1: Search for 'journal' Tag --------
        #Check if text:'journal' is present
        [isPresent, journal_name] = hasJournal(journal_lst, info_str)
        if isPresent is True:
            alpha_index = get_alphaindex(journal_name.strip(" ")[0])
            prob_title_match = process.extractOne( journal_name,   \
                                                  self.jrnl_DB_name_lst[alpha_index])
            if prob_title_match[1] > 95:
                return [prob_title_match[0], prob_title_match[1]]
                
        self.log_file.write(" ".join(journal_lst) + '\n')
        
        ##------- Level 2: 1-Gram Search --------
        #Search through 1-gram for best batch
        [best_title, max_score, final_lst] =  self.get_best_match(journal_lst, \
                                                   manirated_info_str, \
                                                   0.95)
        prob_jrnl_name = strip_using_marker(manirated_info_str \
                                            ,best_title)
        #Ensure if 1-gram is not an alias, buy verifying using markers
        if prob_jrnl_name != None:
            jaro_reldist = jellyfish.jaro_distance(prob_jrnl_name, best_title)
            if jaro_reldist > 0.9:
                return [best_title, max_score]
        
        ##------- Level 3: N-Gram Pivoted Search --------
        #Create an Ngram list for first parsing
        Ngram_lst = create_Ngram(journal_lst)  
        [best_title, max_score, final_lst] =  self.get_best_match(Ngram_lst, \
                                                    manirated_info_str, \
                                                    0.90)
        return [best_title, max_score]
          
    #Remove any numbers and split the string based on comma
    #and return the list
    def sanitize(self, journal_str):
        #Remove vol or volume label
        sant_str = re.sub("(?i)vol\.","",journal_str)
        sant_str = re.sub("(?i)volume\.","",sant_str)
        
        #Remove any hyperlink in the text
        sant_str = strip_http(sant_str)
                           
        #Remove any quotes if present
        sant_str = strip_Quote(sant_str)
        
        #Remove any special character and number
        sant_str = re.sub('[^\wA-Za-z]', ' ', sant_str)
        sant_str = re.sub('\d+', ' ', sant_str)
        
        jrnl_lst = sant_str.split()
        return jrnl_lst
        
      

### If run as standlone, run a test 
if __name__ == "__main__": 
    srch = jrnl_srch(True)
    # while True:
        # jrnl_str = input('Enter Journal Name:').lower()
        # sanitize = srch.sanitize(jrnl_str)
        # srch.try_journal(jrnl_str)

    import time
    avg_time = 0
    out = open(sys.argv[2], 'w')
    no_lines = int(sys.argv[3])
    start_line = int(sys.argv[4]) - 1
    with open(sys.argv[1], 'r', encoding='utf-8', errors='ignore') as file:
        #Skip to start line
        for j in range(start_line):
            try:
                file.readline()
            except:
                continue
            
        for i in range(no_lines):
            strt = time.time()
                
            line = file.readline()                
            # try:
                # line = file.readline()
            # except:
                # print("Unicode error in line:" , i)
                # out.write("No Journal match, 0 \n")
                # continue
                
            string = line.split(",")
            info_str = ",".join(string[1:])
            info_str = str(line)
            
            if srch.log_file != None: 
                srch.log_file.write('Line:' + str(i+1) + "\n")
             
            journal = None
            # try:
            [journal, score] = srch.get_journal(info_str)
            # except:
                # print("Exception Occured in line below ===>")
                # print('Line : ',i+1,info_str)
                # continue
                
            if journal is None:
                out.write("No Journal match, 0 \n")
            else:
                out.write(journal + ", " + str(score) + '\n')
                
            end = time.time() - strt
            avg_time = avg_time + end
            print('Line:', (i+1),'|| Time taken = ', end)            

    print('Complete!!! --> Average time per serach = ', (avg_time/no_lines))
    out.close()
  


