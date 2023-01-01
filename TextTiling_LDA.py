# -*- coding: utf-8 -*-
"""TT1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lKrNE63lJtWKUE5tq4GbwahUpwHMIREt

## Downloads

#### Installation
"""

!pip install pandarallel
!python -m spacy download en_core_web_lg
!npm install stopwords-en
!pip install wordcloud

"""#### Imports
Import aller libraries, die wir brauchen plus Import einer eigenen Stopwörterliste, die zusätzlich als Stopwörter genutzt werden.
"""

# Commented out IPython magic to ensure Python compatibility.
# Standard
import pandas as pd
import numpy as np
from pandarallel import pandarallel  # parallelization
pandarallel.initialize()
from google.colab import files
import io
import math
from math import sqrt
from __future__ import division
import sys
import random

# NLP
import nltk
print ("nltk", nltk.__version__)
from nltk.tokenize import RegexpTokenizer
nltk.download('wordnet')
from nltk.corpus import wordnet as wn
nltk.download('stopwords')
from nltk.corpus import stopwords
stop_words = stopwords.words('english')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from nltk.stem import WordNetLemmatizer 
from nltk.tokenize import word_tokenize 
from collections import Counter
from nltk.util import ngrams
from nltk.corpus import wordnet as wn

import spacy
print ("spacy", spacy.__version__)
import spacy.cli
spacy.cli.download("en_core_web_lg")

import re
print ("re", re.__version__)

# Machine Learning
import sklearn
print ("sklearn", sklearn.__version__)
from sklearn.decomposition import LatentDirichletAllocation, TruncatedSVD
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import GridSearchCV

from sklearn.metrics.pairwise import euclidean_distances
from pprint import pprint
from sklearn.feature_extraction.text import TfidfVectorizer as tf_idf
from sklearn.model_selection import train_test_split

# Plotting Tools
import matplotlib.pyplot as plt
# %matplotlib inline
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.cluster import DBSCAN
from sklearn import metrics
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler

uploaded = files.upload()

moreStopwords = pd.read_csv("pyrouge.txt", sep=" ")
moreStopwords = list(moreStopwords.reuters)

"""#### Data
Upload der gecrawlten Daten. Es handelt sich um über 68 Stunden Youtube-Nachrichten-Transkripte aus der USA, UK, Australien und Kanada. Alle Nachrichten sind englisch und die Transkripte via Youtube automatisch erstellt. Dadurch keine Satzzeichen. Damit die Herausforderung, dass man keine Sätze bilden kann und das Problem der Wort-Fehler-Rate
"""

uploaded = files.upload()

data = pd.read_csv(io.BytesIO(uploaded['TranscriptSegmentationMore.csv']), index_col=0)

data

data.drop(["Unnamed: 0.1", "Unnamed: 0.1.1", "Unnamed: 0.1.1.1"], axis = 1)

"""## Preprocessing
#### Tokens, Stopwords English, Lemmatize, POS, Frequencies
"""

def preprocessText(pre_data):
  tokenizer = RegexpTokenizer(r'\w+')
  lemmatizer = WordNetLemmatizer()
  pre_data["text"] = pre_data.parallel_apply(lambda row: re.sub(r'[0-9]+', " ", str(row["text"])), axis=1)
  pre_data["text"] = pre_data.parallel_apply(lambda row: re.sub(r"(\[(.*?)\])", " ", str(row["text"])), axis=1)
  pre_data["tokens"] = pre_data.parallel_apply(lambda row: tokenizer.tokenize(str(row["text"].lower())), axis=1)
  stop_words = stopwords.words('english')
  stop_words.extend(moreStopwords)
  pre_data["tokens"] = pre_data.parallel_apply(lambda row: [element for element in row["tokens"] if element not in stop_words], axis=1)
  pre_data["tokens"] = pre_data.parallel_apply(lambda row: [element for element in row["tokens"] if len(element) > 2], axis=1)
  pre_data["pos"] = pre_data.parallel_apply(lambda row: nltk.pos_tag(row["tokens"]), axis=1)
  pre_data["lemmata"] = pre_data.parallel_apply(lambda row: [lemmatizer.lemmatize(word) for word in row["tokens"]], axis=1)
  return pre_data

def cleanRow(pre_data):
  pre_data = pre_data[pre_data.text != ""]
  return pre_data

def getPseudoTokens(pseudosentences):
  pseudowordsList = []
  for sentence in pseudosentences:
    pseudowordsList.append(word_tokenize(sentence))
  return pseudowordsList

"""---

## TextTilling
Siehe Ausarbeitung. Der vorbereinigte Text wird in einen Text zusammengefügt und dann in Pseudosätze der Länge w unterteilt. Diese Pseudosätze werden in Blöcke k mittels vocabularyintroduction nach der Rate der neu-aufgetauchten Wörter innerhalb der Blöcke bewertet. Diese Rate wird weitergegeben und die Veränderungen der Wörter links und rechts betrachtet. Je höher der Score, desto wahrscheinlicher ein Sinnwechsel. Darauf werden die Sätze neu unterteilt und als newData ausgegeben


w und k können in Execution angegeben werden und kann als maßgebliche Veränderungsparameter genutzt werden.

### Methodes

Tokenisierung

Lexical Score Determination (Lücke zwischen den Sätzen)

Blockscore: Angrenzende Textblöcke nach Ähnlichkeit prüfen. Je mehr Wörter die Blöcke gemeinsam haben, desto höher der Score

Vocabulare Introduction: Da, wo neue Wörter erkannt werden, werden sie auch vermerkt. Score: neueTerme/SatzLückenNummer
"""

def createPseudosentences(text, w):
  pseudosentences = []
  example = text.split()
  pseudosentences.append([' '.join(example[i:i+w]) for i in range(0,len(example),w)])
  return pseudosentences

def vocabulary_introduction(pseudosentences, w):
  newWords1 = set()
  newWords2 = set(pseudosentences[0])
  scores = []
  for token in range(1, len(pseudosentences)-1):
    b1 = set(pseudosentences[token-1]).difference(newWords1)
    b2 = set(pseudosentences[token+1]).difference(newWords2)
    scores.append((len(b1) +len(b2))/(w*2))
    newWords1 = newWords1.union(pseudosentences[token-1])
    newWords2 = newWords2.union(pseudosentences[token+1])

  lastElement = len(set(pseudosentences[len(pseudosentences)-1]).difference(newWords1))
  scores.append(lastElement/(w*2))
  return scores

"""Boundary identification"""

def getDepthSideScore(lexScores, currentGap, left):
    depthScore = 0
    i = currentGap
    while lexScores[i] - lexScores[currentGap] >= depthScore:
        depthScore = lexScores[i] - lexScores[currentGap]
        i = i - 1 if left else i + 1
        if (i < 0 and left) or (i == len(lexScores) and not left):
            break
    return depthScore

def identifyBoundary(lexScores, w):
  boundaries = []
  depthCutOff = np.mean(lexScores) - np.std(lexScores)
  printScores(str("Score CutOff: "), depthCutOff)

  for currentGap, score in enumerate(lexScores):
    printScores(str("Current Gap: "), currentGap)
    depthLeftScore= getDepthSideScore(lexScores, currentGap, True)
    printScores(str("Left Score: "), depthLeftScore)
    depthRightScore= getDepthSideScore(lexScores, currentGap, False)
    printScores(str("Right Score: "), depthRightScore)
    depthScore = depthLeftScore + depthRightScore
    printScores(str("Depth Score: "), depthScore)
    if depthScore >= depthCutOff:
      boundaries.append(currentGap)
  return boundaries

def printScores(nameScore, score):
  print(str(nameScore) + str(score))

def getBoundary(boundary, breaks, w):
  tokenIndices = [w * (gap+1) for gap in boundary]
  sentenceBoundary = set()
  for index in range(len(tokenIndices)):
    sentenceBoundary.add(min(breaks, key = lambda b: abs(b- tokenIndices[index])))
  return sorted(list(sentenceBoundary))

def getTextParts(pseudosentencesList, boundary):
  cuts = []
  for number in boundary:
    cuts.append(pseudosentencesList[number])
  return cuts

def cutText(cuts, text):
  substring = []
  newText = []
  for sentence in cuts:
    substring = text.partition(str(sentence))
    newText.append(substring[0])
    text = text.replace(substring[0], "")
  return newText

"""### Execution"""

w = 25
k = 2

data = preprocessText(data)
data = cleanRow(data)

paragraphs = list(data.text)
textlist = " ".join(paragraphs)
paragraphsInString = str(paragraphs)
paradict = {"sentence": paragraphsInString}
textdict = {"text": textlist}
tt = pd.DataFrame(textdict, paradict)
tt = preprocessText(tt)
tt

lemmata = list(tt.lemmata)
for token in lemmata:
  textlemma = " ".join(token)
textlemma

pseudosentences = createPseudosentences(textlemma, w)
pseudos = []
for sentence in pseudosentences:
  pseudos.append(sentence)
pseudos = pd.DataFrame(pseudosentences, paradict)
pseudos = pseudos.transpose()
pseudoSentenceList = list(pseudos.sentence)

pseudoWords = getPseudoTokens(pseudoSentenceList)
vocabularyIntroduction = vocabulary_introduction(pseudoWords, w)
boundary = identifyBoundary(vocabularyIntroduction, w)
str(boundary)
textParts = getTextParts(pseudoSentenceList, boundary)
newText = cutText(textParts, textlemma)

newData = pd.DataFrame(newText, columns=["text"])
newData=preprocessText(newData)
newData=cleanRow(newData)
newData['bigrams'] = newData['lemmata'].apply(lambda row: list(nltk.bigrams(row)))
newData["forvector"] = newData.parallel_apply(lambda row: str(row["lemmata"]), axis=1)

newData.to_csv("newData1.csv")

newData

"""## LDA Modell Testset"""

uploaded = files.upload()

test = pd.read_csv(io.BytesIO(uploaded['bbc-text.csv']))

newData=preprocessText(test)
newData=cleanRow(newData)
newData['bigrams'] = newData['lemmata'].apply(lambda row: list(nltk.bigrams(row)))
newData["forvector"] = newData.parallel_apply(lambda row: str(row["lemmata"]), axis=1)
newData.to_csv("testData.csv")

test["category"].value_counts()

"""## Latent Dirchlet Allocation
Die neuen Daten werden vektorisiert und über countVektorizer die Frequenz der Wörter in den berechneten Sinnabschnitten berechnet. TF-IDF normalisiert diese Frequenz nach der Länge der Sinnabschnitte. Die Methode mit der kleinsten Sparsictiy (Vektoren mit kaum Infos) und der kleinsten Perplexity (wie schnell ist die KI mit neuen Informationen überrascht) wird gewählt und für die LDA genutzt. 

Die LDA wird mittels Grid-Serach CV nach den besten Parametern gescannt. Dadurch einsteht zum einen die Sinnabschnitt-Thema-Matrix und die Thema-Wort-Matrix. Außerdem werden die Cluster des Eregbnisses mittels k-Means angezeigt (weiches Cluster). Nähere Infos in der Ausarbeitung.

In der Prediction soll ein neuer Sinnabschnitt hinzugefügt werden. Idaelerweise bekommt er die richtige Topic zugewiesen.

### Count Vectorizer vs TFIDF

#### Count Vectorizer
"""

vectorizer = CountVectorizer(analyzer='word',       
                             min_df=2,                        # minimum occurences of a word 
                             stop_words='english',             
                             lowercase=True,                   # convert all words to lowercase
                             token_pattern='[a-zA-Z0-9]{3,}',  # num chars > 3
                             max_features=50000,             
                             #ngram_range = (1, 2)
                            )


matrix = vectorizer.fit_transform(newData.forvector)
counts = pd.DataFrame(matrix.toarray(),
                  columns=vectorizer.get_feature_names())

counts.to_csv("CountVectorizer.csv")

"""#### TFIDF"""

tfidf = tf_idf(norm = None)#, ngram_range=(1,2))
tfidf_lemma = tfidf.fit_transform(newData.forvector)

print(tfidf_lemma.shape)

result=pd.DataFrame(tfidf_lemma.toarray(), columns=tfidf.get_feature_names())

result.to_csv("tfidf.csv")

"""#### Decission"""

lda_model = LatentDirichletAllocation(n_components=8,           
                                      max_iter=10,               
                                      learning_method='online',   
                                      random_state=100,          
                                      batch_size=128,            
                                      evaluate_every = -1,       
                                      n_jobs = -1, 
                                     )
lda_output2 = lda_model.fit_transform(counts)
perplex_count = lda_model.perplexity(counts)
print("Perplexity CountVectorizer: ", perplex_count)

lda_output1 = lda_model.fit_transform(result)
perplex_tfidf = lda_model.perplexity(result)
print("Perplexity TF-IDF: ", perplex_tfidf)

# Materialize the sparse data
data_dense = matrix.todense()
sparsicity_countvec = (data_dense > 0).sum()/data_dense.size*100
# Compute Sparsicity = Percentage of Non-Zero cells
print("Sparsicity CountVectorizer: ", sparsicity_countvec, "%")

# Materialize the sparse data
data_dense1 = tfidf_lemma.todense()
sparsicity_tfidf = (data_dense1 > 0).sum()/data_dense1.size*100
# Compute Sparsicity = Percentage of Non-Zero cells
print("Sparsicity TF-IDF: ", sparsicity_tfidf, "%")

if(perplex_tfidf < perplex_count and sparsicity_tfidf < sparsicity_countvec):
  vectorizerSelected = tfidf
  counterSelected = result
else:
  vectorizerSelected = vectorizer
  counterSelected = counts

if(sparsicity_tfidf < sparsicity_countvec):
  vectorizerSelected = tfidf
  counterSelected = result
else:
  vectorizerSelected = vectorizer
  counterSelected = counts

"""### LDA Modell"""

search_params = {'n_components': [6], 'learning_decay': [.5, .7, .9], 'max_iter': [5, 7, 10]}
lda = LatentDirichletAllocation()
model = GridSearchCV(lda, param_grid=search_params)
model.fit(counterSelected)

best_lda = model.best_estimator_
print("Best Parameter: ", model.best_params_)
print("Best Perplexity: ", best_lda.perplexity(counterSelected))
print("Best Log Likelihood: ", best_lda.score(counterSelected))
pprint(best_lda.get_params())

"""### Matrices

#### Methods
"""

def make_blue(val):
    color = 'darkblue' if val > .1 else 'lightblue'
    return 'color: {col}'.format(col=color)

def make_bold(val):
    weight = 800 if val > .1 else 300
    return 'font-weight: {weight}'.format(weight=weight)

def show_topics(vectorizer=vectorizerSelected, lda_model=lda_model, n_words=15):
    keywords = np.array(vectorizerSelected.get_feature_names())
    topic_keywords = []
    for topic_weights in lda_model.components_:
        top_keyword = (-topic_weights).argsort()[:n_words]
        topic_keywords.append(keywords.take(top_keyword))
    return topic_keywords

"""#### Execution"""

# Document - Topic Matrix
lda_output = best_lda.transform(counterSelected)
topicnames = ["Topic " + str(i) for i in range(best_lda.n_components)]
docnames = ["Document " + str(i) for i in range(len(newData))]
document_topic_matrix = pd.DataFrame(np.round(lda_output, 2), columns=topicnames, index=docnames)

dominant_topic = np.argmax(document_topic_matrix.values, axis=1)
document_topic_matrix['dominant_topic'] = dominant_topic

document_topic_matrix = document_topic_matrix.head(15).style.applymap(make_blue).applymap(make_bold)
document_topic_matrix

# Topic-Keyword Matrix
df_topic_keywords = pd.DataFrame(best_lda.components_)
df_topic_keywords.columns = vectorizerSelected.get_feature_names()
df_topic_keywords.index = topicnames
df_topic_keywords.head()

# Topic - Keywords Dataframe
topic_keywords = show_topics(vectorizer=vectorizerSelected, lda_model=best_lda, n_words=15)
df_topic_keywords = pd.DataFrame(topic_keywords)
df_topic_keywords.columns = ['Word '+str(i) for i in range(df_topic_keywords.shape[1])]
df_topic_keywords.index = ['Topic '+str(i) for i in range(df_topic_keywords.shape[0])]
df_topic_keywords

df_topic_keywords.to_csv("topics.csv")

"""### Clustern

#### K-Means
"""

clusters = KMeans(n_clusters=best_lda.n_components, random_state=100).fit_predict(lda_output)
svd_model = TruncatedSVD(n_components=2)  # 2 components
lda_output_svd = svd_model.fit_transform(lda_output)

# X and Y axes of the plot using SVD decomposition
x = lda_output_svd[:, 0]
y = lda_output_svd[:, 1]

score = silhouette_score(lda_output, clusters, metric='euclidean')
print('Silhouette Score: %.3f' % score)

# Plot
plt.figure(figsize=(12, 12))
plt.scatter(x, y, c=clusters)
#plt.xlabel('Component 2')
#plt.xlabel('Component 1')
plt.title("Topic Clusters")

"""#### DBSCAN"""

db = DBSCAN(eps=0.2, min_samples=30).fit(lda_output)
core_samples = np.zeros_like(db.labels_, dtype=bool)
core_samples[db.core_sample_indices_] = True
labels = db.labels_

# Number of clusters in labels, ignoring noise if present.
n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
n_noise_ = list(labels).count(-1)

print("Estimated number of clusters: %d" % n_clusters_)
print("Estimated number of noise points: %d" % n_noise_)
print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(lda_output, labels))

foundlabels = set(labels)
# get colors, noise in black
colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(foundlabels))]
for k, col in zip(foundlabels, colors):
    if k == -1:
        col = [0, 0, 0, 1]
# get different shapes 
    class_member = (labels == k)
    marker = lda_output[class_member & core_samples]
    plt.plot(marker[:, 0], marker[:, 1], 'o', markerfacecolor=tuple(col),
             markeredgecolor='k', markersize=14)
 
    marker = lda_output[class_member & ~core_samples]
    plt.plot(marker[:, 0], marker[:, 1], 'o', markerfacecolor=tuple(col),
             markeredgecolor='k', markersize=6)
 
plt.title('Estimated number of clusters: %d' % n_clusters_)
plt.show()

"""### Prediction"""

def predict_topic(newtext):
  text = preprocessText(newtext)
  text["forvector"] = text.parallel_apply(lambda row: str(row["lemmata"]), axis=1)
  textVec = vectorizerSelected.transform(text.forvector)
  topic_probability_scores = best_lda.transform(textVec)
  topic = df_topic_keywords.iloc[np.argmax(topic_probability_scores), :].values.tolist()
  return topic, topic_probability_scores

# Predict the topic
mytext = ["The latests movie from actress Scarlett Johannson was a total success"]
mytext = pd.DataFrame(mytext, columns=["text"])
predictedTopic, prob_scores = predict_topic(mytext)

mytext

print(predictedTopic)