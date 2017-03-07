"""
######################################################################
######################################################################
                        Author Tagger
Descp: Uses NER tagger to remove any names of author or
organization from the string and returns a corrected string

Copyright: (c) 2016, Indresh Sira, The Ohio State University
All rights reserved.
######################################################################
######################################################################
"""
import nltk
import os
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.chunk import ne_chunk
from nltk.tag import StanfordNERTagger
import load_config

"""
Iterates over Nlp generated tags and finds the tokens tagged with ORG
"""
def getValid_nodes(nlp_tags):
    keyword_lst = []
    for tags in nlp_tags:
        if type(tags) is nltk.Tree:
            if tags.label() == 'ORGANIZATION':
                for each_word in tags:
                    keyword_lst.append(each_word[0])
    return keyword_lst
    
class author_tag:
    NERTagger = None
    verbose = None
    def __init__(self, verbose=False):
        config = load_config.load_config()
        self.verbose = verbose
        os.environ['JAVAHOME'] = config.java_home
        self.NERTagger = StanfordNERTagger( config.NER_model \
                                      ,config.NER_jar)
           
    def rmv_authors(self, citation):
        trueCitation = citation
        stanford_tags = self.NERTagger.tag(trueCitation.split(' '))
        nlp_tags = ne_chunk(pos_tag(word_tokenize(trueCitation)))
        
        #Remove words with PERSON tags from stanford_tags
        for eachTag in stanford_tags:
            if eachTag[1] == "PERSON":
                keyword = eachTag[0]
                citation = citation.replace(keyword, '')
                if self.verbose is True:
                    print(keyword)

        #Remove words with ORGN tages from nlp tags
        word_lst = getValid_nodes(nlp_tags) 
        for eachTag in word_lst:
            if self.verbose is True:
                    print(eachTag)
            citation = citation.replace(eachTag, '')
        
        return citation

##---------------------------------
##      STAND ALONE TEST        
##---------------------------------
if __name__ == "__main__":
    import time
    
    user_in = input('Enter the string:')
    
    strt = time.time()
    
    ATag = author_tag(True)
    sanit_cit = ATag.rmv_authors(user_in)
    
    end = time.time() - strt
    
    print(sanit_cit)
    print('Time taken =', end)
        
        
        