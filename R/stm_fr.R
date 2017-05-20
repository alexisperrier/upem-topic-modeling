# ------------------------------------------------------------------------------
#  Packages
# ------------------------------------------------------------------------------

# install.packages( c("stm", "tm", "splines", "stmBrowser", 'wordcloud', 'igraph', 'data.table', "stringr", "RColorBrewer", "stringr", dependencies = TRUE) )
library(stringr)
library('stm')
library('stmBrowser')
library('wordcloud')
library('igraph')
library('geometry')
library('Rtsne')
library('data.table')
library(SnowballC)
library(GetoptLong)

qq.options("cat_prefix" = function(x) format(Sys.time(), "\n[%H:%M:%S] "))

# ------------------------------------------------------------------------------
#  Load data. Assuming the notes have been cleaned
#  thresh.upper  <- 400
# ------------------------------------------------------------------------------

setwd("/Users/alexisperrier/amcp/upem/R")
data_path <- '/Users/alexisperrier/amcp/upem/data/'
img_path <- '/Users/alexisperrier/amcp/upem/images/'

trial         <- 'avare'
thresh.lower  <- 2
min_wordlen   <- 3
text_feature  <- 'sent_tokens'
save_envt     <- FALSE
max_rows      <- 0

input_file    <- qq("@{data_path}@{trial}.csv")
envt_filename <- qq("@{data_path}@{trial}.RData")
topic_file    <- qq("@{img_path}@{trial}.png")


# ------------------------------------------------------------------------------
#  Load data, rm heldout
# ------------------------------------------------------------------------------
qqcat("Load data from @{input_file}")

df        <- read.csv(input_file)
cond      <- (df[,text_feature] != '')
df        <- df[cond,]
dim(df)

if (max_rows > 0){
  qqcat("limit to @{max_rows} docs")
  df        <- df[0:max_rows, ]
}

# ------------------------------------------------------------------------------
# 1) pre processed the text with basic NLP massaging
# content candidates: df$NoteContent df$ActivityDetails or combination df$text
# ------------------------------------------------------------------------------

qqcat("pre processing\n")

processed <- textProcessor(df[,text_feature],
                           lowercase        = FALSE,
                           removestopwords  = FALSE,
                           removenumbers    = FALSE,
                           removepunctuation = FALSE,
                           wordLengths      = c(3,Inf),
                           striphtml        = FALSE,
                           stem             = FALSE,
                           metadata         = df)

out   <- prepDocuments(processed$documents, processed$vocab, processed$meta,
                       lower.thresh = thresh.lower)

docs  <- out$documents
vocab <- out$vocab
meta  <- out$meta

meta$personnage    <- as.factor(meta$personnage)
# meta$acte    <- as.factor(meta$acte)

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

n_topics = seq(from = 10, to = 50, by = 5)

gridsearch <- searchK(out$documents, out$vocab,
                      K = n_topics,
                      prevalence  =~ personnage,
                      reportevery = 20,
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
#  STM
# also try with k=0
# check residuals
# checkBeta(stmobject, tolerance = 0.01): Looks for words that load exclusively onto a topic
# ------------------------------------------------------------------------------
qqcat("fit stm\n")
fit <- stm(out$documents, out$vocab, 10,
            prevalence  =~ personnage,
            data        = meta,
            reportevery = 10,
            # max.em.its  = 100,
            emtol       = 1.5e-4,
            init.type   = "Spectral",
            seed        = 1)

qqcat("stm done\n")
if (save_envt){
  qqcat("saving to @{envt_filename}")
  save.image(envt_filename)
}


# labelTopics(fit, n=20)
print(labelTopics(fit, n=10))

# png(topic_file, width = 800, height = 1200)
# par(mar=c(2,0.5,1,10))
plot.STM(fit,type = "summary", labeltype= 'frex', main= 'Don Juan - Topic proportions', n = 10, xlim =c(0, 0.2))
# dev.off()


#
topicQuality(model=fit, documents=docs, main='Topic Quality',bty="n")
#
plot(fit, labeltype=c("frex"), main = 'Topic Most Frequent Words',bty="n", n= 5)
#
# plotModels(fit, main='Model Selection - Best Likelihood')
#
stmBrowser(fit, data=out$meta, c("personnage"), text="texte", labeltype='frex', n = 4)

cloud(fit, 9)

# which documents are the mst representative of a topic
findThoughts(fit, texts = out$meta$note, topics = 11, n = 10 )

# which topic contains the keywords
findTopic(fit,n = 20, c("amour"))

