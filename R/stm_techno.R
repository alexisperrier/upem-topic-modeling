# ------------------------------------------------------------------------------
#  Packages
#  Les packages suivant doivent etre installés
# ------------------------------------------------------------------------------

install.packages(
  c("stm", "tm", "stmBrowser", 'wordcloud',
    "stringr",'igraph',  "RColorBrewer",
    'Rtsne','SnowballC','GetoptLong'), dependencies = TRUE
)


library('stringr')
library('stm')
library('stmBrowser')
library('wordcloud')
library('igraph')
library('geometry')
library('Rtsne')
library('SnowballC')
library('GetoptLong')

# Indique l'heure avant chaque print
qq.options("cat_prefix" = function(x) format(Sys.time(), "\n[%H:%M:%S] "))

# ------------------------------------------------------------------------------
#  Initialization: adapter les path des repertoires suivant votre environnement
# ------------------------------------------------------------------------------

setwd("/Users/alexisperrier/amcp/upem-topic-modeling/R")
data_path <- '~/upem-topic-modeling/data/'

input_file    <- qq("@{data_path}techno.csv")

# ------------------------------------------------------------------------------
#  Chargement des données dans une dataframe
# ------------------------------------------------------------------------------
qqcat("Load data from @{input_file}")

df  <- read.csv(input_file)

dim(df)

# les 2 premiere lignes
df[1:2,]

# ------------------------------------------------------------------------------
# PRE-PROCESSING des textes
#   lowercase        : tout en minsucule
#   removestopwords  : filtrer les stopwords
#   removenumbers    : retirer les chiffres,
#   removepunctuation : enlever les signes de ponctuation
#   wordLengths      : ne garder que les mots de 3 characteres ou plus
#   striphtml        : enlever les tags HTML,
#   stem             : ne garder que la racine des mots (non utilisé)
#   metadata         : la sources des meta donnees: (journal et catégorie pour ce corpus)
# ------------------------------------------------------------------------------

qqcat("pre processing\n")

processed <- textProcessor(df[,'content'],
                           lowercase        = TRUE,
                           removestopwords  = TRUE,
                           removenumbers    = TRUE,
                           removepunctuation = TRUE,
                           wordLengths      = c(3,Inf),
                           striphtml        = TRUE,
                           stem             = FALSE,
                           metadata         = df)

# ------------------------------------------------------------------------------
# Quelques parametres pour filtrer les mots.
# Ne seront pris en compte que
#   * les mots qui apparaissent plus souvent que thresh.lower dans les documents
#   * les mots qui apparaissent moins souvent que thresh.upper dans les documents (non utilisé)
# ------------------------------------------------------------------------------

thresh.lower  <- 50
# thresh.upper  <- 300 # non utilisé

out   <- prepDocuments(processed$documents,
                        processed$vocab,
                        processed$meta,
                        lower.thresh = thresh.lower)

# ------------------------------------------------------------------------------
# out$documents est la matrice documents-mots
# out$vocab contient le vocabulaire, correspondance entre chaque mot et son ID
# ------------------------------------------------------------------------------


# Transformer les variables externes en Factor
meta          <- out$meta
meta$journal  <- as.factor(meta$journal)
meta$rubrique <- as.factor(meta$rubrique)

# ------------------------------------------------------------------------------
#  Recherche du nombre optimal de topics avec searchK
#  Grid search en faisant varier le nombre de topics
#    * max.em.its permet de limiter le nombre d'itérations
#    * emtol fixe une limite inférieure en dessous de laquelle le modele est estimé avoir convergé
# ------------------------------------------------------------------------------

# sequence du nombre de topics
n_topics = seq(from = 20, to = 50, by = 5)

# grid search
gridsearch <- searchK(out$documents, out$vocab,
                      K = n_topics,
                      prevalence  =~ journal+ rubrique ,
                      reportevery = 10,
                      # max.em.its = maxemits,
                      emtol       = 1.5e-4,
                      data = meta)

plot(gridsearch)
print(gridsearch)

# Select the best number of topics that maximizes both exclusivity and semantic coherence
# Ces plots permettent de choisir le nombre de topics qui maximise a la fois
# la cohérence sémantique et l'exclusivité
# En général, l'exclusivité croit avec les nombre de topics (la distribution de dirichlet devient pointue)
# la cohérence sémantique correspond a des topics plus généraux (la distribution de dirichlet est plus aplatie)
plot(gridsearch$results$exclus, gridsearch$results$semcoh)
text(gridsearch$results$exclus, gridsearch$results$semcoh, labels=gridsearch$results$K, cex= 0.7, pos = 2)

plot(gridsearch$results$semcoh, gridsearch$results$exclus)
text(gridsearch$results$semcoh, gridsearch$results$exclus, labels=gridsearch$results$K, cex= 0.7, pos = 2)

# ------------------------------------------------------------------------------
# Appliquer STM
#  www.structuraltopicmodel.com
#  avec k=0, l'algo trouve de lui-meme un nombre de topics optimal, souvent assez grand
#   * prevalence: quelles sont les variables externes que l'on souhaite prendre en compte
#   * emtol: en dessous de ce niveau de changement entre 2 iterations, on arrete
#   * max.em.its: nombre maximal d'iterations
#  Si chaque itération prends trop de temps (plsu de quelques secondes)
#  essayer de réduire le nombre valeur prises par les variables externes
# ------------------------------------------------------------------------------
qqcat("fit stm\n")
fit <- stm(out$documents, out$vocab, 0,
            prevalence  =~ journal + rubrique,
            data        = meta,
            reportevery = 10,
            # max.em.its  = 100,
            emtol       = 1.5e-4,
            init.type   = "Spectral",
            seed        = 1)

qqcat("stm done\n")

# ----------------------------------- ------------------------------------------
# TADAAAA!
# Les topics avec 10 mots (n=10) chacun
#  Frex, proba, ... sont différentes façon d'associer les mots dans les topics
#  En general, Frex donne de bons résultats
# ------------------------------------------------------------------------------
print( labelTopics(fit, n=10) )

# ------------------------------------------------------------------------------
# Importance des topics
# ------------------------------------------------------------------------------

plot.STM( fit,
          type = "summary",
          labeltype= 'frex',
          main= 'Importance des topics',
          n = 10
)


# ------------------------------------------------------------------------------
# Corrélation des topics
# Réduire cutoff pour augmenter les liens entre topics dans le graph
# ------------------------------------------------------------------------------

topic_corr = topicCorr(fit, method = "simple", cutoff = 0.1)
plot(topic_corr, topics = c())

# ------------------------------------------------------------------------------
# Qualité des topics
# ------------------------------------------------------------------------------
topicQuality(model=fit, documents=out$documents, main='Topic Quality',bty="n")

plot(fit, labeltype=c("frex"), main = 'Topic Most Frequent Words',bty="n", n= 5)

# ------------------------------------------------------------------------------
# Nuage Nuage ... cloud(fit, numero du topic)
# ------------------------------------------------------------------------------

cloud(fit, 14)

# ------------------------------------------------------------------------------
# Visualisation interactive avec stmBrowser
# ------------------------------------------------------------------------------

stmBrowser(fit, data=out$meta, c("journal"), text="content", labeltype='frex', n = 900)

# ------------------------------------------------------------------------------
# Quels sont les documents les plus representatifs d'un topic?
# La matrice de répartition des topics par document est accessible dans fit$theta
# ------------------------------------------------------------------------------

findThoughts(fit, texts = out$meta$content, topics = 19, n = 3 )

# ------------------------------------------------------------------------------
# Quels topics contiennent un mot ou une serie de mots
# ------------------------------------------------------------------------------

findTopic(fit, c("autonomous"), n = 20)

# ------------------------------------------------------------------------------
# Sauvegarder l'environnement avec toutes les variables
# ------------------------------------------------------------------------------

# save.image('techno_topic_models.Rdata')

