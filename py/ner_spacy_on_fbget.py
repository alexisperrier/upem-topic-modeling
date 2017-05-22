'''
Ce script load la data file data/main_fbget.csv
et en extrait toutes les entités a l'aide de spacy.io

'''

import pandas as pd
import numpy as np
import string

import csv
import re
import json
import time
import csv

import spacy

start_time   = time.time()

frac         = 1

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

df = pd.read_csv('../data/main_fbget.csv', low_memory=False, dtype = dtypes ).sample(frac = frac)
print("Data loaded in {0:.2f}s".format(time.time() - start_time))

# ---------------------------------------------------------------------
#  Remove empty message, fill in empty features with 0 or blank strings
#  NaNs, columns, length of message, pid
# ---------------------------------------------------------------------
print("rm NaNs, columns, names")
df.dropna(axis=0, subset=['message'], inplace=True)
df.drop(drop_features, axis = 1, inplace = True)

# Cast NaN as 0
for f in int_features:
    df[f].fillna(0, inplace = True)

# Cast as str
for f in str_features:
    df[f].fillna('', inplace = True)


# Extract post id from composite post_id
df['pid'] = df.post_id.apply(lambda p :  p.split('_')[1])

print(df.shape)

# ----------------------------------------------------------------------------
#  NER
#  Load english model in Spacy
#  memorize entities in lists: persons, GPE, ...
# ----------------------------------------------------------------------------

nlp     = spacy.load('en')
persons = []
GPE     = []
ORG     = []
NORP    = []
entities = []

# Loop over each row of the data and store entities in lists: persons, GPE, ...
for i,d in df.iterrows():

    doc = nlp(d.message)
    # PERSON, GPE, NORP and ORG are stored in respective lists
    # all other non date or numerical entity types are stored in entities
    if len(doc.ents) > 0:
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                persons.append(str(ent))
            elif ent.label_ == 'GPE':
                GPE.append(str(ent))
            elif ent.label_ == 'NORP':
                NORP.append(str(ent))
            elif ent.label_ == 'ORG':
                ORG.append(str(ent))
            # all the other entities that might make sense
            elif (ent.label_ not in ['CARDINAL', 'ORDINAL', 'PERCENT','DATE','TIME']) :
                entities.append((str(ent), ent.label_))

# Save lists of entities to txt files for manual review
open('../data/persons.txt', 'w').write("\n".join( sorted(persons) ))
open('../data/gpe.txt', 'w').write("\n".join( sorted(GPE) ))
open('../data/norp.txt', 'w').write("\n".join( sorted(NORP) ))
open('../data/org.txt', 'w').write("\n".join( sorted(ORG) ))

# Save all other entittes with related entity type
str_entities = [ "{0},{1}".format(e[1], str(e[0]).replace(',',' '))  for e in entities ]

open('../data/entities.csv', 'w').write("\n".join( str_entities ))

print("NER done in {0:.2f}s".format(time.time() - start_time))


