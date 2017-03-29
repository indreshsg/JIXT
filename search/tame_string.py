"""
######################################################################
######################################################################
                        String Tamer
    
Descp: CLenases string from inavldi conditions
    
Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""
import nltk
import os
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
import re
import enchant
import calendar

#engDict = enchant.Dict("en_US")
engDict = enchant.DictWithPWL("en_US", "scimajor_lib.txt")

"""
remove any month name from given list
"""
def removeMonth(text):
    str_lst = text.split(' ')
    for month_idx in range(1, 13):
        month_name = calendar.month_name[month_idx].lower()
        month_abbr = calendar.month_abbr[month_idx].lower()
        str_lst = [each.lower().replace(month_name, " ")  for each in str_lst]
        str_lst = [each.lower().replace(month_abbr, " ")  for each in str_lst]
    return ' '.join(str_lst)
    
def in_corner(indx, list):
    if indx == 0 or indx == len(list):
        return True
    else:
        return False
      
"""
Remove THE from the string
"""
def handle_THE(text):
    if text == None:
        return text
    text = re.sub(r'\bthe\b', '', text)
    return text


"""
Remove any NUM from the text
"""
def handle_NUM(text):
    if text == None:
        return text
    tokens = word_tokenize(text)
    taged_keys = pos_tag(tokens)
    new_tokens = []
    for each in taged_keys:
        #if each[1] != 'CD' and each[0] != '-':
        if each[1] != 'CD':
            new_tokens.append(each[0])
        else:
            new_tokens.append(".")
    return ' '.join(new_tokens)
            
"""
Check all & in the string. If the previous and next word of '&'
is english word, replace it with AND
"""
def handle_AND(text):
    key = '&'
    if text == None:
        return text
    tokens = word_tokenize(text)
    new_tokens = tokens
    if key in tokens:
        indices = [i for i, x in enumerate(tokens) if x == key]
        for indx in indices:
            if in_corner(indx, tokens) == False:
                prev_word = tokens[indx-1]
                nxt_word = tokens[indx+1]
                if not prev_word or not nxt_word:
                    continue
                if engDict.check(prev_word) and engDict.check(nxt_word):
                    new_tokens[indx] = "and"  
    return ' '.join(new_tokens)
    
"""
Check all . in the string. If the previous word is an english word
then keep the . else remove it, probably an abbreviation
"""
def handle_FULLSTOP(text):
    key = '.'
    if text == None:
        return text
    tokens = word_tokenize(text)
    new_tokens = tokens
    if key in tokens:
        indices = [i for i, x in enumerate(tokens) if x == key]
        for indx in indices:
            if in_corner(indx, tokens) == False:
                prev_word = tokens[indx-1]
                if not prev_word:
                    continue
                if len(prev_word) > 5:
                    if engDict.check(prev_word):
                        new_tokens[indx] = "."
                else:
                    new_tokens[indx] = ""
    return ' '.join(new_tokens) 

    
def manirate_citation(citation): 
    citation = re.sub(r'\bno\b', '@', citation)
    citation = re.sub(r'\bvol\b', '@', citation)
    manit_citation = handle_THE(citation)
    manit_citation = handle_AND(manit_citation)
    manit_citation = handle_FULLSTOP(manit_citation)
    manit_citation = handle_NUM(manit_citation)
    manit_citation = removeMonth(manit_citation)
            
    #Replace any double space with single space
    manit_citation = ' '.join(manit_citation.split())
    replace_str = 'united states of '
    if replace_str in manit_citation:
        manit_citation = re.sub(r'united states of ', 'usa ', manit_citation)
        
    replace_str = "j."
    if replace_str in manit_citation:
        manit_citation = manit_citation.replace(replace_str, "j")
        
    replace_str = "am."
    if replace_str in manit_citation:
        manit_citation = manit_citation.replace(replace_str, "am")
        
    print(manit_citation)
    return manit_citation


