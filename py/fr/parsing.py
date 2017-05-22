import numpy as np
import pandas as pd


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
from nltk import WordPunctTokenizer
from string import digits
from nltk.stem.snowball import FrenchStemmer
from nltk import sent_tokenize

from collections import Counter

print("loading spacy")
import spacy
nlp  = spacy.load('fr')

print("loading French lemmatizer")
from  french_lemmatizer import FrenchLemmatizer
lmtz = FrenchLemmatizer(lefff_file_path='py/lefff-3.4.mlex/lefff-3.4.mlex', lefff_additional_file_path= 'py/lefff-3.4.mlex/lefff-3.4-addition.mlex')


pd.options.mode.chained_assignment = None

personnages = []
actes = []
scenes = []
# paragraphes = {'editeur': ''}

# df = pd.DataFrame(columns = ['acte','scene','personnage','text'], )

class Parsing():

    @classmethod
    def valid_token(cls,tk):
        extra_stopwords = ["qu'",  "n'", 'vraiment', 'peut','pouvoir','voilà','voici', 'dire','dit','dis','voila', 'disais','disait',  'elles','ici', 'doit','celle','toutes','tout', 'tant','fait','faire', 'tous','bien','bon','bonne','plus','point', '-','a','ah','allons','après','assez','aussi','autres','cela','cest','cet','cette','comme','comment','contre','donc','dont','dun','dune','eh','encore','enfin','ils','jai','jen','les','là','na','nai','nen','nest','ni','non','ny','où','quel','quelle','quelque','quil','quoi','quon','quun','quà','si','sil','ça','être']
        return (tk not in stopwords.words('french'))  & (tk not in extra_stopwords)


    def __init__(self):
        roman = {'I':1,  'II':2,  'III':3,  'IV':4,  'V':5,  'VI':6,  'VII':7,  'VIII':8,  'IX':9,  'X':10,  'XI':11,  'XII':12,
        'XIII': 13, 'XIV':14, 'XV':15, 'XVI':16 }

        # open file
        # file = open("data/donjuan.txt", "r")
        file = open("data/avare.txt", "r")
        punctuation_chars   = ''.join([s for s in string.punctuation if s !='-'  ])
        translator_chars    = str.maketrans(' ',' ', punctuation_chars)

        rows_list=[]
        n = -1
        # personnage = 'Sganarelle'
        personnage = 'Valère'
        acte = 'Premier'
        scene = 'I'

        for line in file:
            # trim and remove
            commentaire = re.search(' \((.+?)\)', line)
            if commentaire:
                line = ''
            else:
                line = line.strip()

            acte_src = re.search('ACTE (.+?)\.', line)
            scene_src = re.search('Scène (.+?)\.', line)
            personnage_src = re.search('- (.+?) -', line)

            new_line = False
            if acte_src:
                acte = acte_src.group(1)
                actes.append(int(acte))
                new_line = True
                print(acte)

            if scene_src:
                scene = scene_src.group(1)
                scenes.append(scene)
                new_line = True
                print(scene)

            if new_line:
                n = "{0}-{1}".format(acte, scene)

            if personnage_src:
                personnage = personnage_src.group(1)
                personnages.append(personnage)
                new_line = True

            if new_line:
                t = '\n'
            else:
                t = line.replace('\n','')
                # .replace("'",' ').lower().translate(translator_chars)

            RecordtoAdd={}
            RecordtoAdd.update({
                'n': n,
                'acte' : int(acte),
                'scene' : roman[scene],
                'personnage' : personnage,
                'original': line,
                'texte': t
                })

            rows_list.append(RecordtoAdd)

        df = pd.DataFrame(rows_list)
        print(df.shape)
        df = df[df.texte != '\n']
        print(df.shape)
        df = df[df.texte != '']
        print(df.shape)
        self.df = df


if __name__ == "__main__":

    p = Parsing()
    # stemmer = FrenchStemmer()
    df = p.df
    # gdf = df.groupby(by = ['acte','scene','personnage'] ).apply(lambda d: ' '.join(d.texte)   )
    gdf = df.groupby(by = ['n','personnage'] ).apply(lambda d: ' '.join(d.texte)   )
    gdf = gdf.reset_index()
    gdf.columns = ['scene','personnage','texte']
    gdf['tokens'] = ''

    allpos = []
    alltokens = []

    for i, d in gdf.iterrows():
        sentences = sent_tokenize(d.texte)
        for sent in sentences:
            sent = sent.replace('   ', ' ').replace('  ', ' ')
            print('\n' + '---'*10)
            print(sent)
            print('---'*10)
            doc = nlp(sent)
            tokens = []
            for tk in doc:
                allpos.append(tk.pos_)
                if tk.pos_ == 'NOUN':
                    print(" => [{2}] {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'n'), tk.pos_ ) )
                    tokens.append(lmtz.lemmatize(tk.text, pos = 'n'))
                elif tk.pos_ == 'VERB':
                    print(" => [{2}] {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'v'), tk.pos_ ) )
                    tokens.append(lmtz.lemmatize(tk.text, pos = 'v'))
                elif tk.pos_ == 'ADJ':
                    print(" => [{2}] {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'v'), tk.pos_ ) )
                    tokens.append(lmtz.lemmatize(tk.text, pos = 'a'))
                elif tk.pos_ == 'ADV':
                    print(" => [{2}] {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'r'), tk.pos_ ) )
                    tokens.append(lmtz.lemmatize(tk.text, pos = 'r'))
                else:
                    print(tk.text, tk.lemma_, tk.pos_)
            tokens = [tk.lower() for tk in tokens if Parsing.valid_token(tk.lower())]
            alltokens += tokens
        gdf.loc[i,'tokens'] = tokens

    # gdf.columns = ['acte','scene','personnage','texte']

    # expand, tokenize, lowercase, remove stopwords
    # gdf['tokens'] = gdf.texte.apply(lambda t: wpt.tokenize(t)  )

    # tokens = [ tk for i,tokens in  gdf.tokens.items() for tk in tokens]
    # c = Counter(tokens)

# doc = nlp("Je cours dans les champs, heureux et insouciant, avec ma bien aimée.")
# # lemma does not work
# for tk in doc:
#     print(tk.text, tk.lemma_, tk.pos_)
#     if tk.pos_ == 'NOUN':
#         print(" => {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'n') ) )
#     elif tk.pos_ == 'VERB':
#         print(" => {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'v') ) )

#     # remove stop words
#     gdf['tokens'] = gdf.tokens.apply(lambda tokens: [ tk for tk in tokens if Parsing.valid_token(tk)  ]  )
#     # gdf['tokens'] = gdf.tokens.apply(lambda tokens: [ stemmer.stem(tk) for tk in tokens ]  )
#     gdf['token_count'] = gdf.tokens.apply(len)
#     gdf.shape
#     gdf = gdf[gdf.token_count > 2]
#     gdf.shape
#     gdf['sent_tokens'] = gdf.tokens.apply( lambda tokens : ' '.join(tokens)  )


# ---------------------------------------------------------------------------

    # df = df.reset_index()

    # wpt = WordPunctTokenizer()
    # # expand, tokenize, lowercase, remove stopwords
    # df['tokens'] = df.texte.apply(lambda t: wpt.tokenize(t)  )

    # tokens = [ tk for i,tokens in  df.tokens.items() for tk in tokens]
    # c = Counter(tokens)

    # df['tokens'] = df.tokens.apply(lambda tokens: [ tk for tk in tokens if Parsing.valid_token(tk)  ]  )
    # df['tokens'] = df.tokens.apply(lambda tokens: [ stemmer.stem(tk) for tk in tokens ]  )

    # df['token_count'] = df.tokens.apply(len)
    # df.shape
    # df = df[df.token_count > 1]
    # df['sent_tokens'] = df.tokens.apply( lambda tokens : ' '.join(tokens)  )




