'''
'''

from datetime import datetime as dt
import pandas as pd
import numpy as np
import string
import enchant

import csv
import re
import json
import time
import csv

from nltk.util import ngrams, skipgrams
from nltk import word_tokenize
from nltk.corpus import stopwords

from string import digits
from invariants import Invar

from collections import Counter

import matplotlib.pyplot as plt
import seaborn as sns;
sns.set(color_codes=True)

import nltk
from nameparser.parser import HumanName

import spacy
nlp     = spacy.load('en')

pd.options.mode.chained_assignment = None

class Prepare():
    def __init__(self, frac = 1):
        # filter out comment less than 2 tokens
        min_token   = 2
        start_time  = time.time()
        punctuation_chars = ''.join([s for s in string.punctuation if s !='_'  ]) + "\x08" + '\r\n“”…’' + digits
        translator_chars = str.maketrans(' ', ' ', punctuation_chars)


        # ---------------------------------------------------------------------
        #  Load data
        # ---------------------------------------------------------------------
        dtypes = {
                    'from_id': str,     'media_id': str,
                    'post_id': str,     'parent_id': str,
                    'comment_id': str,  'cc_id': str,
                    'place_id':str,     'place_zip':str,
                    'tagged_id_list':str
                }

        df = pd.read_csv('data/tagged_fbtge.csv', low_memory=False, dtype = dtypes ).sample(frac = frac)
        print("Data loaded in {0:.2f}s".format(time.time() - start_time))

        # ---------------------------------------------------------------------
        #  NaNs, columns, length of message, pid
        # ---------------------------------------------------------------------
        # rm names only comments

        df = df[df.tagged_message != 'prsn']
        df['clean_message'] = df.tagged_message
        print(df.shape)

        # ---------------------------------------------------------------------
        #  Group by
        # ---------------------------------------------------------------------
        print("Group by pid")
        self.full_df = df
        df = df.groupby('pid').apply(self.join_and_sum)

        df.reset_index(inplace = True)
        print(df.shape)
        print(df.columns)

        # ---------------------------------------------------------------------
        #  STM prep
        #  message is untouched. tokens are extracted from tmp feature
        # ---------------------------------------------------------------------
        print("----- STM prep -----")
        t0 = time.time()

        # remove punctuation and digits
        print('punctuation')
        df['clean_message']       = df.clean_message.apply(lambda s : s.translate(translator_chars))

        # ---------------------------------------------------------------------
        #   tokenize
        # ---------------------------------------------------------------------
        print('tokenize and lemmatize')
        df['tokens']    = df.clean_message.apply(self.lemmatize_spacy)

        # Count tokens
        # lower case
        df['tokens']    = df.tokens.apply(lambda tk : [ s.lower() for s in tk  ] )

        # rm stopwords, filter out words shorter than 2
        print('stopwords')
        list_stopwords = stopwords.words('english') + Invar.extra_stopwords()
        df['tokens']   = df.tokens.apply(lambda tk : [w for w in tk if (w not in list_stopwords) & (len(w) > 2) ] )

        # build list of non English words

        # remove non words from tokens
        print("remove non english words")
        ench         = enchant.DictWithPWL("en_US", 'data/acceptable_words.txt')
        df['tokens'] = df.tokens.apply(lambda tk : [w for w in tk if self.existing_word(ench,w) ] )

        print('count tokens')
        df['token_count'] = df.tokens.apply(lambda t : len(t))

        print('rm is less than 5 tokens')
        df['keep_row'] = df.token_count.apply(lambda nt : nt > 5 )
        df = df[df.keep_row]
        print(df.shape)

        # bigrams, skipgrams
        print("bigrams")
        # df['bigrams']   = df.tokens.apply(lambda tk : ['_'.join(tu) for tu in list(ngrams(tk,2))]  )
        # df['skipgrams'] = df.tokens.apply(lambda tk : ['_'.join(tu) for tu in list(skipgrams(tk,2,2))]  )

        # rebuild sentences with tokens, bigrams and skipgrams
        df['sent_tokens'] = df[['tokens']].apply( lambda d: self.sentencify(d)   , axis = 1)
        # df['sent_tokens_bigrams'] = df[['tokens', 'bigrams']].apply( lambda d: self.sentencify(d) , axis = 1)
        # df['sent_tokens_skipgrams'] = df[['tokens', 'skipgrams']].apply( lambda d: self.sentencify(d) , axis = 1)

        print("STM prep in {0:.2f}s".format(time.time() - t0))
        print(df.head())

        # columns = ['pid', 'reaction_count', 'share_count',  'comment_count', 'len_message', 'token_count','message', 'tokens', 'bigrams', 'skipgrams' , 'sent_tokens', 'sent_tokens_bigrams', 'sent_tokens_skipgrams']
        self.df = df

        print("Initialized in {0:.2f}s".format(time.time() - start_time))

    def lemmatize_spacy(self,text):
        doc = nlp(text)
        return [ token.lemma_ for token in doc  ]

    def tagged_columns(self):
        columns = []
        # for key,words in Invar.entity_persons().items():
        #     columns.append( key.lower().replace(' ','_') )
        for key,words in Invar.entity_tagging().items():
            columns.append( key.lower().replace(' ','_') )

        return columns

    def existing_word(self,ench, tk):
        try:
            return ench.check(tk) | ench.check(tk.lower()) | ench.check( string.capwords(tk.lower()) )
        except:
            pass

    def sentencify(self, d):
        mergedlist = []
        for key in d.keys():
            mergedlist.extend( list(d[key]) )
        return ' '.join(mergedlist)

    def join_and_sum(self,x):
        d = {
            'reaction_count'    : x['reaction_count'].sum(),
            'share_count'       : x['share_count'].sum(),
            'comment_count'     : x['comment_count'].sum(),
            'message'           : '.\n\r\t '.join(x['message']),
            'clean_message'     : '. '.join(x['clean_message']),
            'started_at'        : np.min(x.created_at),
            'finished_at'       : np.max(x.created_at),
        }
        for key in self.tagged_columns():
            d[key] = x[key].sum()

        return pd.Series(d)

if __name__ == "__main__":
    start_time  = time.time()
    p = Prepare(frac = 1)

    p.df['klout'] = p.df.apply( lambda d : d.share_count + d.comment_count + d.reaction_count   , axis =1 )
    p.df['log_klout'] = round(np.log(p.df.klout+1), 0)
    p.df.loc[p.df.log_klout > 8, 'log_klout'] = 9
    print("Total time: {0:.2f}s".format(time.time() - start_time))

    # composition do corpus
    df = p.df[ (p.df.token_count > 100  )  & (p.df.token_count < 900) ]
    # df = p.df[ (p.df.token_count > 10  )  ]
    # --------------------------------------------------------------------------
    #  theme
    # --------------------------------------------------------------------------
    # theme = 'america'

    # output_file = "data/topics_01_0514.csv"

    # df = df[ df[theme] > 0 ]

    df.drop_duplicates(subset = 'sent_tokens', inplace = True)

    df.dropna(axis=0, subset=['reaction_count', 'comment_count','share_count'], inplace=True)

    df.sort_values(by = 'token_count', ascending=False, inplace = True)

    df['display_message'] =  df['display_message'] = df.apply(lambda d :
                ' '.join([ str(d.pid),'r:' + str(d.reaction_count),'c:'+ str(d.comment_count), 's:'+str(d.share_count), d.message]
            ), axis = 1  )

    df['days']          = df.apply(lambda d: int((dt.strptime(d.finished_at, '%Y-%m-%d %H:%M:%S').date() - dt.strptime(d.started_at, '%Y-%m-%d %H:%M:%S').date()).days), axis = 1)
    df['created_at']    = df.started_at.apply(lambda d: d.split(' ')[0]  )
    df['log_days']      = round(np.log(df.days+1), 0)
    df['token_count']   = round(df.token_count/100,0)*100
    df.drop(['clean_message'], inplace = True, axis=1)
    columns = ['pid','share_count', 'comment_count', 'reaction_count', 'alt_media', 'america', 'barackobama', 'brexit',
    'christian', 'communism', 'democrats', 'donaldtrump', 'europe', 'events', 'evil_people', 'hillaryclinton', 'islam',
    'judaism', 'left_orgs', 'memewar','mexico', 'msm_media', 'nazi',
    'other_countries', 'politician_dems', 'politician_reps', 'race', 'russia', 'war',
    'klout', 'log_klout', 'log_days', 'days', 'started_at', 'created_at','finished_at','tokens', 'token_count',
    'display_message', 'message', 'sent_tokens']
    df.to_csv('data/main_tagged_fbgte.csv', index=False)

    for key in self.tagged_columns():
        d[key] = round( np.log( df[key] + 1 ), 0 )

    # columns = ['pid', 'token_count' , 'log_klout', 'log_days', 'display_message', 'sent_tokens', 'hillaryclinton', 'barackobama', 'donaldtrump']
    # df = df[columns]
    df.to_csv('data/fbget_stm_ready_full_01.csv', index=False)



