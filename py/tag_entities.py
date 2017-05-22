'''
This script uses the entities defined in invariants.py to tag the comments
a bit of clean up is also carried out
names of persons that are not entites are replaced with token: prsn
results is stored in csv file
'''


import pandas as pd
import numpy as np
import string
import enchant

import csv
import re
import json
import time
import csv

from string import digits
from invariants import Invar

from collections import Counter

import matplotlib.pyplot as plt
import seaborn as sns; sns.set(color_codes=True)

import spacy

import inflect
pinf = inflect.engine()

start_time  = time.time()
frac        = 1

int_features = ['reaction_count','share_count','comment_count','is_post_published']
str_features = ['tagged_id_list', 'comment_id', 'post_id', 'from_id', 'cc_id',
                'parent_id', 'media_id', 'action', 'event', 'tagged_name_list']
drop_features= ['is_post_hidden', 'page', 'place_region', 'posting_application', 'tagged_type_list',
                'place_city', 'place_country', 'place_id', 'place_latitude', 'place_longitude',
                'place_name', 'place_state', 'place_street', 'place_zip']
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

df = pd.read_csv('data/main_fbtge.csv', low_memory=False, dtype = dtypes ).sample(frac = frac)
print("Data loaded in {0:.2f}s".format(time.time() - start_time))

ench         = enchant.DictWithPWL("en_US", 'data/acceptable_words.txt')
def existing_word(ench, tk):
    return ench.check(tk) | ench.check(tk.lower()) | ench.check( string.capwords(tk.lower()) )

def add_plural(words):
    plur_words = []
    for word in words:
        plural_word = pinf.plural(word)
        if existing_word(ench,plural_word):
            plur_words.append(plural_word)
    return words + plur_words


# ---------------------------------------------------------------------
#  NaNs, columns, length of message, pid
# ---------------------------------------------------------------------
print("rm NaNs, columns, names. Add len_message, pid")
df.dropna(axis=0, subset=['message'], inplace=True)
df.drop(drop_features, axis = 1, inplace = True)

# cast NaN as 0
for f in int_features:
    df[f].fillna(0, inplace = True)

# cast as str
for f in str_features:
    df[f].fillna('', inplace = True)

# extract post id from composite post_id
df['pid'] = df.post_id.apply(lambda p :  p.split('_')[1])

print(df.shape)

# ----------------------------------------------------------------------------
#  NER
# ----------------------------------------------------------------------------
nlp     = spacy.load('en')

for key,words in Invar.entity_tagging().items():
    key = key.lower().replace(' ','_')
    df[key] = 0

url_pattern = re.compile(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', re.IGNORECASE)

with open( 'data/acceptable_words.txt'  ) as f:
    acceptable_words = f.readlines()
acceptable_words = [x.strip() for x in acceptable_words]

df['tagged_message'] = df.message
replaced_persons = []

print('lingo')
diction = { **Invar.lingo() }
pattern = re.compile(r'\b(' + '|'.join(diction.keys()) + r')\b', re.IGNORECASE)
df['tagged_message'] = df['tagged_message'].apply(lambda s : pattern.sub(lambda x: diction[x.group().lower()], s) )


# transform alternate apostrophe
print("apostrophe")
translate_apostrophe = str.maketrans('’', "'") # ’ => '
df['tagged_message']        = df.tagged_message.apply(lambda s : s.translate(translate_apostrophe))

print('contractions')
diction = {**Invar.contractions()}
pattern = re.compile(r'\b(' + '|'.join(diction.keys()) + r')\b', re.IGNORECASE)
df['tagged_message'] = df['tagged_message'].apply(lambda s : pattern.sub(lambda x: diction[x.group().lower()], s) )


# regex replace
print("regex replace")
for rgx in Invar.regex_translate().items():
    p = re.compile(rgx[0], re.IGNORECASE)
    df['tagged_message'] = df['tagged_message'].apply(lambda s : p.sub(rgx[1], s) )

# remove posessive
print('remove posessive')
df['tagged_message'] = df['tagged_message'].apply(lambda s : s.replace("'s",'') )

# add plural to entities
entity_persons = {}
for key,words in Invar.entity_persons().items():
    entity_persons[key] = add_plural(words)

entity_tagging = {}
for key,words in Invar.entity_tagging().items():
    entity_tagging[key] = add_plural(words)

for i,d in df.iterrows():

    message = d.message
    # remove urls
    message =  url_pattern.sub('url', message)

    # entities persons: tag and replace
    for key,words in entity_persons.items():
        tag =  key.lower().replace(' ','_')

        pattern = re.compile(r'\b(' + '|'.join( words ) + r')\b', re.IGNORECASE)
        if pattern.search(message):
            # df.loc[i, tag ] = 1
            message =  pattern.sub(key, message)

    # entity_tagging just tag the comment
    for key,words in entity_tagging.items():

        tag =  key.lower().replace(' ','_')
        pattern = re.compile(r'\b(' + '|'.join( words ) + r')\b', re.IGNORECASE)
        if pattern.search(message):
            df.loc[i, tag ] = 1


    # replace non personnalities names
    doc = nlp(message)
    if len(doc.ents) > 0:
        for ent in doc.ents:
            if ( (ent.label_ == 'PERSON')
                    and (ent.text not in Invar.entity_persons().keys() )
                    and (ent.text not in Invar.entity_tagging().keys() )
                    and (ent.text not in acceptable_words ) ):
                replaced_persons.append(ent.text)
                message = message.replace(ent.text,'prsn')

    df.loc[i,'tagged_message'] = message

    if (i % 1000 == 0):
        print("\n-------- {2}\n{0}\n{1}".format(d.message, message,i))

# replaced_persons = sorted(list(set(replaced_persons)))
df.to_csv('data/tagged_fbtge_0514.csv')
replaced_persons = sorted(replaced_persons)
open('data/replaced_persons_0514.txt', 'w').write("\n".join( replaced_persons ))





