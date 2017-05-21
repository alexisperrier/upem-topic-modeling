# ------------------------------------------------------------------------------
#  STM sur echantillon de 1000 posts du forum God Emperor Trump
#  https://www.facebook.com/GodEmperorTrump/
# ------------------------------------------------------------------------------

library('stringr')
library('stm')
library('stmBrowser')
library('wordcloud')
library('igraph')
library('geometry')
library('Rtsne')
library('SnowballC')
library('GetoptLong')

qq.options("cat_prefix" = function(x) format(Sys.time(), "\n[%H:%M:%S] "))

# ------------------------------------------------------------------------------
#  Initialize working directory
#  set file path
#  set input file
# ------------------------------------------------------------------------------

setwd("/Users/alexisperrier/amcp/upem-topic-modeling/R")
data_path <- '/Users/alexisperrier/amcp/upem-topic-modeling/data/'

input_file    <- qq("@{data_path}echantillon_god_emperor_trump.csv")

# ------------------------------------------------------------------------------
#  Load des donnees dans une dataframe
# ------------------------------------------------------------------------------
qqcat("Load data from @{input_file}")

df        <- read.csv(input_file)
dim(df)
# les 2 premiere lignes
df[1:2,]

# ------------------------------------------------------------------------------
# PRE-PROCESSING
# lowercase        : tout en minsucule
# removestopwords  : filtrer les stopwords
# removenumbers    : retirer les chiffres,
# removepunctuation : enlever les signes de ponctuation
# wordLengths      : ne garder que les mots de 3 characteres ou plus
# striphtml        : enlever les tags HTML,
# stem             : ne garder que la racine des mots (non utilisé)
# metadata         : la sources des meta donnees: journal et catogorie)
# ------------------------------------------------------------------------------

qqcat("pre processing\n")

processed <- textProcessor(df[,'message'],
                           lowercase        = TRUE,
                           removestopwords  = TRUE,
                           removenumbers    = TRUE,
                           removepunctuation = TRUE,
                           wordLengths      = c(3,Inf),
                           striphtml        = TRUE,
                           stem             = FALSE,
                           metadata         = df)

# ------------------------------------------------------------------------------
# Quelques parametres pour filtrer les mots. Ne seront pris en compte que
#   * les mots qui apparaissent plus souvent que thresh.lower dans les documents
#   * les mots qui apparaissent moins souvent que thresh.upper dans les documents (non utilisé)
# ------------------------------------------------------------------------------

thresh.lower  <- 50
# thresh.upper  <- 300

out   <- prepDocuments(processed$documents, processed$vocab, processed$meta,
                       lower.thresh = thresh.lower)

# ------------------------------------------------------------------------------
# out$documents est la matrice documents-mots
# out$vocab contient le vocabulaire, correspondance mot et ID du mot
# ------------------------------------------------------------------------------


# Tranformer les variables externes en Factor
meta  <- out$meta
meta$post_type  <- as.factor(meta$post_type)

# ------------------------------------------------------------------------------
#  Recherche du nombre optimal de topics avec searchK 
# ------------------------------------------------------------------------------


n_topics = seq(from = 20, to = 50, by = 5)

gridsearch <- searchK(out$documents, out$vocab,
                      K = n_topics,
                      # prevalence  =~ journal+ rubrique ,
                      reportevery = 10,
                      # max.em.its = maxemits,
                      emtol       = 1.5e-4,
                      data = meta)

plot(gridsearch)
print(gridsearch)

# Select the best number of topics that maximizes both exclusivity  and semantic coherence
plot(gridsearch$results$exclus, gridsearch$results$semcoh)
text(gridsearch$results$exclus, gridsearch$results$semcoh, labels=gridsearch$results$K, cex= 0.7, pos = 2)

plot(gridsearch$results$semcoh, gridsearch$results$exclus)
text(gridsearch$results$semcoh, gridsearch$results$exclus, labels=gridsearch$results$K, cex= 0.7, pos = 2)


# ------------------------------------------------------------------------------
# Appliquer STM
#  avec k=0, l'algo trouve de lui meme un nombre de topics optimal
#  prevalence: quelles sont les variables externes que l'on souhaite prendre en compte
#  emtol: en dessous de ce niveau de changement entre 2 iterations, on arrete
#  max.em.its: nombre maximal d'iterations
# ------------------------------------------------------------------------------
qqcat("fit stm\n")
fit <- stm(out$documents, out$vocab, 25,
           # prevalence  =~ journal + rubrique,
           data        = meta,
           reportevery = 10,
           max.em.its  = 100,
           emtol       = 1.0e-4,
           init.type   = "Spectral",
           seed        = 1)

fit_25 <-fit
qqcat("stm done\n")

# ----------------------------------- ------------------------------------------
# TADAAAA! Les topics avec 10 mots chacun
#  Frex, ... sont differentes façon d'associer les mots dans les topics
#  En general je choisi Frex ou ...
# ------------------------------------------------------------------------------
print( labelTopics(fit,14, n=10) )

# ------------------------------------------------------------------------------
# Importance des topics
# ------------------------------------------------------------------------------

plot(fit, labeltype=c("prob"), main = 'Topic Most Frequent Words',bty="n", n= 5)

# sauvegarder
# fit_0 <- fit

# ------------------------------------------------------------------------------
# Correlation des topics
# ------------------------------------------------------------------------------

topic_corr = topicCorr(fit, method = "simple", cutoff = 0.1)
plot(topic_corr, topics = c())

# Comparaison des mots entre 2 topics
plot.STM( fit,
          type = "perspectives",
          labeltype= 'frex',
          topics = c(5,2),
          main= 'Comparaison entre 2 topics',
          n = 5
)



# ------------------------------------------------------------------------------
# Qualité des topics
# ------------------------------------------------------------------------------
topicQuality(model=fit, documents=out$documents, main='Topic Quality',bty="n")


# ------------------------------------------------------------------------------
# Nuage Nuage cloud(fit, numero du topic)
# ------------------------------------------------------------------------------

cloud(fit, 6)

# ------------------------------------------------------------------------------
# Visualisation avec stmBrowser
# ------------------------------------------------------------------------------

stmBrowser(fit, data=out$meta,  text="message", labeltype='frex', n = 4)

# ------------------------------------------------------------------------------
# Quels sont les documents les plus representatifs d'un topic?
# ------------------------------------------------------------------------------

findThoughts(fit, texts = out$meta$message, topics = 14, n = 5 )

# ------------------------------------------------------------------------------
# Quels topics contiennent un mot ou une serie de mots
# ------------------------------------------------------------------------------

findTopic(fit, c("pussy"), n = 20)

# ------------------------------------------------------------------------------
# Sauvegarder l'environnement avec toutes les variables
# ------------------------------------------------------------------------------

save.image('echantillon_god_emperor_trump.Rdata')

