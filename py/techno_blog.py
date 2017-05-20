import feedparser
import pandas as pd
import csv

# liste de urls de fils rss
feeds = {
'http://spectrum.ieee.org/rss/blog/energywise/fulltext':'ieee energywise',
'http://spectrum.ieee.org/rss/blog/cars-that-think/fulltext':'ieee cars',
'http://spectrum.ieee.org/rss/blog/the-human-os/fulltext':'ieee human-os',
'http://spectrum.ieee.org/rss/blog/riskfactor/fulltext':'ieee risks',
'http://spectrum.ieee.org/rss/blog/nanoclast/fulltext':'ieee nano',
'http://spectrum.ieee.org/rss/blog/tech-talk/fulltext':'ieee techtalk',
'http://spectrum.ieee.org/rss/blog/view-from-the-valley/fulltext':'ieee valley',
'http://spectrum.ieee.org/rss/aerospace/fulltext':'ieee aerospace',
'http://spectrum.ieee.org/rss/at-work/fulltext':'ieee atwork',
'http://spectrum.ieee.org/rss/blog/automaton/fulltext':'ieee automaton',
'http://feeds.arstechnica.com/arstechnica/technology-lab':'arstechnica techlab',
'http://feeds.arstechnica.com/arstechnica/gadgets':'arstechnica gadgets',
'http://feeds.arstechnica.com/arstechnica/business':'arstechnica business',
'http://feeds.arstechnica.com/arstechnica/security':'arstechnica security',
'http://feeds.arstechnica.com/arstechnica/tech-policy':'arstechnica tech-policy',
'http://feeds.arstechnica.com/arstechnica/apple':'arstechnica apple',
'http://feeds.arstechnica.com/arstechnica/gaming':'arstechnica gaming',
'http://feeds.arstechnica.com/arstechnica/science':'arstechnica science',
'http://feeds.arstechnica.com/arstechnica/multiverse':'arstechnica multiverse',
'http://feeds.arstechnica.com/arstechnica/cars':'arstechnica cars',
'http://feeds.arstechnica.com/arstechnica/staff-blogs':'arstechnica staff',
}


# Pandas DataFrame
docs = pd.DataFrame(columns = ['rubrique', 'journal', 'content', ])

# Boucle sur les url RSS et construction de la DataFrame
i = 0
for rss, subject in feeds.items():
    llog = feedparser.parse(rss)

    print("%d entrées pour %s" % (len(llog.entries), subject) )
    for entry in llog.entries:
        docs.loc[i,'journal']   = subject.split(' ')[0]
        docs.loc[i,'rubrique']  = subject.split(' ')[1]

        # simple nettoyage: on remplace certains caracteres par des blancs
        docs.loc[i,'content']   = entry.content[0].value.replace('\xa0',' ').replace('"',"'").replace('-'," ")
        i +=1

# Sauvons la dataframe dans un fichier CSV
docs.to_csv('../data/techno.csv',index=False, quoting = csv.QUOTE_ALL)


