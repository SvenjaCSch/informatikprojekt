# informatikprojekt
Automatische Themen-Segmentierung von Nachrichten-Videos

Vorgehensweise:
Im Zuge der Informatikprojekts an der TH Köln wurde zunächst ein englischens Transkript aus Youtube-Nachrichten-Videos erstellt. 
Danach erfolgte eine Segmentierung der Themen via TextTiling und Latent Dirchilet Allocation. Die Wort-Vektorisierung wird mittels CountVectorizer und TF-IDF vorgenommen und dann die Methode mit der besten Werten ausgewählt. 
Die Ergebnisse der LDA wird zum einen mit K-Means und zum anderen mit DBSCAN geclustert.

Data:
Für die Datensätze wird zum einen der BBC-News-Datensatz (https://www.kaggle.com/datasets/pariza/bbc-news-summary) genutzt. Hiermit werden die gewählten Methoden auf Ihre Nutzbarkeit überprüft. Außerdem werden englischsprachigen Nachrichten-Videos unterschiedlicher Länder und Kanäle von Youtube auf ihre Transkripte gecrawlt. Die genutzten Nachrichten können im Code nachvollzogen werden.

Weiteres Vorgehen:
Da diese Methoden-Kombination zu einem noch nicht zufriedenstellenden Ergebnis kam, wurden im nächsten Schritt eine Interpunktionsrekonstruktion via BERT angestrebt, die auf der Annahme resultiert, dass TextTiling ohne Satzenden-Gebrauch unzureichende Ergebnisse liefert. Außerdem wird die Multilingualität theoretisch beleuchtet und mittels eines weiteren gecrawlten Transkript auf deutsch überprüft. Dieser Code kann hier aus Vertraulichkeitsgründen des Unternehmens nicht dargestellt werden. 

Die Bachelorarbeit exploriert zudem weitere akustische und lexikale Methoden. Da diese noch in Bearbeitung ist und ebenfalls in Kombination des Unternehmens geschrieben wird, können hier keine näheren Angaben gemacht werden.

Präsentation
Für die Präsentation der Segmentierung neuer Nachrichtenblöcke der Bachelorarbeit wird Tkinter gewählt.
