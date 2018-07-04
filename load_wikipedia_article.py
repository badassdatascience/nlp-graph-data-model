
#
# import useful libraries
#
import wikipediaapi  # pip3 install wikipedia-api
import nltk
import pprint as pp
import json
import sys
from neo4j.v1 import GraphDatabase
from nltk import word_tokenize
import nltk

from credentials import uri, username, password

#
# user settings
#
page_title = sys.argv[1]
language = 'en'
source = 'wikipedia'

#
# connect to Wikipedia
#
wiki_wiki = wikipediaapi.Wikipedia(language)

#
# retrieve the page
#
page = wiki_wiki.page(page_title)

#
# extract the page summary
#
summary = page.summary
summary_sentences = nltk.sent_tokenize(summary)
section_list = [
    {
        'title' : 'summary',
        'text' : [x.strip() for x in summary_sentences],
        'level' : 0,
        }
    ]

#
# extract the page sections
#
def extract_sections(sections, section_list, level=0):
    for s in sections:
        section_list.append(
            {
                'title' : s.title.lower(),
                'text' : [x.strip() for x in nltk.sent_tokenize(s.text)],
                'level' : level,
                }
            )
        extract_sections(s.sections, section_list, level=level+1)

extract_sections(page.sections, section_list)


#
# connect to Neo4j
#
driver = GraphDatabase.driver(uri, auth=(username, password))

#
# create article
#
cmd = 'MATCH (s:SOURCE) WHERE s.name = $source and s.language = $language MERGE (a:ARTICLE)-[r:HAS_SOURCE]->(s) ON CREATE SET a.name = $article_name RETURN a;'

with driver.session() as session:
    results = session.run(cmd, article_name=page_title.lower(), language=language.lower(), source=source.lower())

    count = 0
    for record in results:
        count += 1
        article_id = record['a'].id

    if count > 1:
        print('Houston, we have a problem! Exiting.')
        sys.exit(0)

#
# create the headers
#
old_header_id = None 
title_to_header_id = {}
for i, section in enumerate(section_list):
    title = section['title']
    level = section['level']

    cmd = 'MATCH (a:ARTICLE) WHERE ID(a) = $article_id MERGE (h:HEADING {title : $title})-[r:HAS_ARTICLE]->(a) ON CREATE SET h.level = $level, h.position_in_article = $position RETURN a, h, r;'

    with driver.session() as session:
        results = session.run(cmd, article_id = article_id, title = title.lower(), level = level, position = i)
    
    count = 0
    for record in results:
        count += 1
        new_header_id = record['h'].id
    if count > 1:
        print('Houston, we have a problem! Exiting.')
        sys.exit(0)

    title_to_header_id[title.lower()] = new_header_id

    if old_header_id != None:
        cmd = 'MATCH (oh:HEADING), (nh:HEADING) WHERE ID(nh) = $new_header_id AND ID(oh) = $old_header_id MERGE (oh)-[r:HAS_NEXT_HEADING]->(nh) RETURN oh, r, nh;'
        with driver.session() as session:
            results = session.run(cmd, new_header_id = new_header_id, old_header_id = old_header_id)
    
    old_header_id = new_header_id

#
# create the sentences
#
sentence_id_to_text = {}
for section_i, section in enumerate(section_list):
    title = section['title']
    level = section['level']

    old_sentence_id = None
    for sentence_i, sentence in enumerate(section['text']):
        sentence = sentence.replace('"', '\\"').replace('\n', ', ').strip()

        cmd = 'MATCH (a:ARTICLE)<-[rha:HAS_ARTICLE]-(h:HEADING) WHERE ID(a) = $article_id AND h.title = $title AND h.level = $level MERGE (s:SENTENCE {text : $text})-[r:HAS_HEADING]->(h) ON CREATE SET s.position_in_heading = $sentence_position RETURN a, rha, h, r, s;'

        with driver.session() as session:
            results = session.run(cmd, article_id = article_id, title = title, text = sentence, level = level, sentence_position = sentence_i)

        count = 0
        for record in results:
            count += 1
            new_sentence_id = record['s'].id
        if count > 1:
            print('Houston, we have a problem! Exiting.')
            sys.exit(0)

        sentence_id_to_text[new_sentence_id] = {'header_id' : title_to_header_id[title.lower()], 'text' : [x.lower() for x in word_tokenize(sentence)], 'sentence_lower' : sentence.lower()}

        if old_sentence_id != None:
            cmd = 'MATCH (os:SENTENCE), (ns:SENTENCE) WHERE ID(ns) = $new_sentence_id AND ID(os) = $old_sentence_id MERGE (os)-[r:HAS_NEXT_SENTENCE]->(ns) RETURN os, r, ns;'
            with driver.session() as session:
                results = session.run(cmd, new_sentence_id = new_sentence_id, old_sentence_id = old_sentence_id)

        old_sentence_id = new_sentence_id
    
#
# create the 'local' words
#
word_text_to_ids = {}
for sentence_id in sentence_id_to_text.keys():
    header_id = sentence_id_to_text[sentence_id]['header_id']
    word_list = sentence_id_to_text[sentence_id]['text']

    sentence_lower = sentence_id_to_text[sentence_id]['sentence_lower']
    location = 0
    char_position_list = []
    for token in word_list:
        char_position = sentence_lower[location:].find(token)
        location = location + char_position
        char_position_list.append(location)

    old_word_id = None
    for i, word, char_pos in zip(range(0, len(word_list)), word_list, char_position_list):
        cmd = 'MATCH (s:SENTENCE) WHERE ID(s) = $sentence_id CREATE (w:WORD_LOCAL {text : $word, position_in_sentence : $position_in_sentence, character_position_in_sentence : $char_pos})-[r:HAS_SENTENCE]->(s) RETURN w, r, s'
        with driver.session() as session:
            results = session.run(cmd, position_in_sentence = i, sentence_id = sentence_id, word = word, char_pos = char_pos)

        count = 0
        for record in results:
            count += 1
            new_word_id = record['w'].id
        if count > 1:
            print('Houston, we have a problem! Exiting.')
            sys.exit(0)

        if not word.lower() in word_text_to_ids:
            word_text_to_ids[word.lower()] = []
        word_text_to_ids[word.lower()].append(new_word_id)

        if old_word_id != None:
            cmd = 'MATCH (ow:WORD_LOCAL), (nw:WORD_LOCAL) WHERE ID(nw) = $new_word_id AND ID(ow) = $old_word_id MERGE (ow)-[r:HAS_NEXT_WORD]->(nw) RETURN ow, r, nw;'
            with driver.session() as session:
                results = session.run(cmd, new_word_id = new_word_id, old_word_id = old_word_id)

        old_word_id = new_word_id

#
# create and link the 'global' words
#
porter = nltk.PorterStemmer()
wnl = nltk.WordNetLemmatizer()
words_to_connect = {}
for word in word_text_to_ids.keys():
    lemmatized = wnl.lemmatize(word)
    stemmed = porter.stem(lemmatized)
    stemmed = stemmed.strip().replace('"', '\\"')
    if stemmed == '':
        continue

    if not stemmed in words_to_connect:
        words_to_connect[stemmed] = word_text_to_ids[word]

for key in words_to_connect.keys():
    cmd = 'MERGE (wg:WORD_GLOBAL {text : $text}) RETURN wg;'
    with driver.session() as session:
        results = session.run(cmd, text = key)

    for wlid in words_to_connect[key]:
        cmd = 'MATCH (wg:WORD_GLOBAL {text : $text}), (wl:WORD_LOCAL) WHERE ID(wl) = $wlid CREATE (wg)<-[r:HAS_WORD_GLOBAL]-(wl) RETURN wg, r, wl;'
        with driver.session() as session:
            results = session.run(cmd, text = key, wlid = wlid)


#
# close the connection
#
driver.close()

