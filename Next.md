Next

* lemma works
* need POS

Install TreeTagger in French
http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/


from  FrenchLefffLemmatizer import FrenchLefffLemmatizer
# lmtz = FrenchLefffLemmatizer()
lmtz = FrenchLefffLemmatizer(lefff_file_path='lefff-3.4.mlex/lefff-3.4.mlex', lefff_additional_file_path= 'lefff-3.4.mlex/lefff-3.4-addition.mlex')
lmtz.lemmatize('voulais', pos = 'v')
lmtz.lemmatize('madame', pos = 'n')

# POS
nlp = spacy.load('fr')
doc = nlp("Je cours dans les champs, heureux et insouciant, avec ma bien aimée.")
# lemma does not work
for tk in doc:
    print(tk.text, tk.lemma_, tk.pos_)
    if tk.pos_ == 'NOUN':
        print(" => {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'n') ) )
    elif tk.pos_ == 'VERB':
        print(" => {0}: {1}  ".format( tk.text, lmtz.lemmatize(tk.text, pos = 'v') ) )


# read https://hal.archives-ouvertes.fr/file/index/docid/521242/filename/lrec10lefff.pdf

# https://github.com/aboSamoor/polyglot
