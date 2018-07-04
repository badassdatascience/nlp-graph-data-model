
#
# load useful libraries
#
from credentials import uri, username, password

from neo4j.v1 import GraphDatabase
import json
import pprint as pp
from nltk import word_tokenize
import sys

#
# connect to Neo4j
#
driver = GraphDatabase.driver(uri, auth=(username, password))

#
# user settings
#
output_directory = 'output'

#
# load sentence IDs
#
with open(output_directory + '/sentences_to_id.json') as f:
    sentences_to_id = json.load(f)

#
# process OpenIE 5.0 output
#
results = {}
relations_dict = {}
f = open(output_directory + '/from_open_IE.txt')
for line in f.readlines():

    line = line.strip().split('\t')
    score = float(line[0])
    context = line[1]
    subject = line[2]
    relation = line[3]
    object = line[4]
    sentence = line[5]
    sentence_id = sentences_to_id[sentence]

    object_list = []
    try:
        object_list = [
            (
                x.split(',List([')[0].split('Argument(')[0].strip(),
                x.split(',List([')[0].split('Argument(')[1].strip(),
                int(x.split(',List([')[1].split(',')[0]),
                int(x.split(',List([')[1].split(', ')[1].split(')')[0]),
                )
            for x in object.split(';')
            ]

    except:
        pass

    relation_start = int(relation.split(',List([')[1].split(', ')[0])
    relation_end = int(relation.split(',List([')[1].split(', ')[1].split(')')[0])
    relation = relation.replace('Relation(', '').split(',List([')[0]


    subject_list = []
    try:
        subject_list = [
            (
                x.split(',List([')[0].split('Argument(')[0].strip(),
                x.split(',List([')[0].split('Argument(')[1].strip(),
                int(x.split(',List([')[1].split(',')[0]),
                int(x.split(',List([')[1].split(', ')[1].split(')')[0]),
                )
            for x in subject.split(';')
            ]
    except:
        pass

    if not sentence_id in results:
        results[sentence_id] = []
    results[sentence_id].append({
            'score' : score,
            'objects' : object_list,
            'relation' : relation,
            'relation_start' : relation_start,
            'relation_end' : relation_end,
            'subjects' : subject_list,
            'sentence' : sentence,
            })

    if not relation in relations_dict:
        relations_dict[relation] = 0
    relations_dict[relation] += 1

f.close()


#
# TEMPORARY
#
cmd = 'MATCH (q)-[r:SENTENCE_HAS_OPENIE_RELATION]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (q)-[r:SENTENCE_HAS_OPENIE_OBJECT]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (q)-[r:SENTENCE_HAS_OPENIE_SUBJECT]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (q)-[r:WORD_LOCAL_HAS_OPENIE_RELATION]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (q)-[r:WORD_LOCAL_HAS_OPENIE_OBJECT]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (q)-[r:WORD_LOCAL_HAS_OPENIE_SUBJECT]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (ro:OPENIE_RELATION) DELETE ro;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (ro:OPENIE_OBJECT) DELETE ro;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (ro:OPENIE_SUBJECT) DELETE ro;'
with driver.session() as session:
    query_results = session.run(cmd)



#
# create version information
#
cmd = 'MERGE (o:OPENIE_VERSION {version : $version, reference : $reference}) RETURN o;'
with driver.session() as session:
    query_results = session.run(cmd, version = 'OpenIE-standalone 5.0', reference = 'https://github.com/dair-iitd/OpenIE-standalone')
    for record in query_results:
        version_id = record['o'].id


# #
# # function for connecting local words
# #
# def get_local_positions(sentence, phrase):
#     # crude
#     sentence_tokens = [x.lower() for x in word_tokenize(sentence)]
#     location = 0
#     position_list = []
#     for token in sentence_tokens:
#         position = sentence.lower()[location:].find(token)
#         location = location + position
#         position_list.append(location)

#     phrase_tokens = [x.lower() for x in word_tokenize(phrase)]

#     n = len(phrase_tokens)

#     for ni in range(0, len(sentence_tokens) - n):
#         if sentence_tokens[ni:(ni+n)] == phrase_tokens:
#             return position_list[ni:(ni+n)]




#
# load Neo4j with OpenIE 5.0 results
#
for sentence_id in results.keys():
    for finding in results[sentence_id]:
        relation = finding['relation']
        relation_start = finding['relation_start']
        relation_end = finding['relation_end']

        sentence = finding['sentence']



        cmd = 'MATCH (s:SENTENCE) WHERE s.text = $sentence AND ID(s) = $sentence_id CREATE (ro:OPENIE_RELATION {text : $relation_text})<-[r:SENTENCE_HAS_OPENIE_RELATION]-(s) RETURN s, ro, r;'
        with driver.session() as session:
            query_results = session.run(cmd, sentence = sentence, sentence_id = sentence_id, relation_text = relation)
        for record in query_results:
            relation_id = record['ro'].id


#         local_position_list = get_local_positions(sentence, relation)

#         rtype = 'RELATION'
#         for pi, local_position in enumerate(local_position_list):
#             cmd = 'MATCH (ro:OPENIE_' + rtype + ')-[rro:SENTENCE_HAS_OPENIE_' + rtype + ']-(s:SENTENCE)-[r:HAS_SENTENCE]-(lw:WORD_LOCAL) WHERE ID(ro) = $relation_id AND s.text = $sentence AND ID(s) = $sentence_id AND lw.character_position_in_sentence = $char_pos MERGE (lw)-[rlwo:WORD_LOCAL_HAS_OPENIE_' + rtype + ']->(ro) ON CREATE SET rlwo.order = $pi RETURN s, r, lw, ro, rro;'
#             with driver.session() as session:
#                 query_results = session.run(cmd, sentence = sentence, sentence_id = sentence_id, char_pos = local_position, relation_id = relation_id, pi=pi)



        phtype = 'OBJECT'
        for type, object, start, end in finding['objects']:
            cmd = 'MATCH (ro:OPENIE_RELATION) WHERE ID(ro) = $relation_id MERGE (ro)-[r:SENTENCE_HAS_OPENIE_OBJECT]->(oo:OPENIE_OBJECT {type : $type, text : $text}) RETURN oo;'
            with driver.session() as session:
                query_results = session.run(cmd, relation_id = relation_id, type=type, text = object)

#             local_position_list = get_local_positions(sentence, object)

#             #if sentence_id == 93282:
#             #    print()
#             #    print(local_position_list)
#             #    print(object)
#             #    print(sentence)

#             for pi, local_position in enumerate(local_position_list):
#                 cmd = 'MATCH (ph:OPENIE_' + phtype + ')-[q]-(ro:OPENIE_' + rtype + ')-[rro:SENTENCE_HAS_OPENIE_' + rtype + ']-(s:SENTENCE)-[r:HAS_SENTENCE]-(lw:WORD_LOCAL) WHERE ID(ro) = $relation_id AND s.text = $sentence AND ID(s) = $sentence_id AND lw.character_position_in_sentence = $char_pos MERGE (lw)-[rlwo:WORD_LOCAL_HAS_OPENIE_' + phtype + ']->(ph) ON CREATE SET rlwo.order = $pi RETURN s, r, lw, ro, rro;'
#                 with driver.session() as session:
#                     query_results = session.run(cmd, sentence = sentence, sentence_id = sentence_id, char_pos = local_position, relation_id = relation_id, pi=pi)







        for type, subject, start, end in finding['subjects']:
            cmd = 'MATCH (ro:OPENIE_RELATION) WHERE ID(ro) = $relation_id MERGE (ro)-[r:SENTENCE_HAS_OPENIE_SUBJECT]->(oo:OPENIE_SUBJECT {type : $type, text : $text}) RETURN oo;'
            with driver.session() as session:
                query_results = session.run(cmd, relation_id = relation_id, type=type, text = subject)

       





# {81462: [{'objects': [('Simple', 'electronics')],
#           'relation': 'to be embedded',
#           'score': 0.8211012035398638,
#           'sentence': 'Electronic textiles, also known as smart garments, '
#                       'smart clothing, smart textiles, or smart fabrics, are '
#                       'fabrics that enable digital components such as a '
#                       'battery and a light (including small computers), and '
#                       'electronics to be embedded in them.',
#           'subjects': [('Simple', 'in them')]},
#          {'objects': [('Simple', 'fabrics')],
#           'relation': 'enable',
#           'score': 0.919760603584431,
#           'sentence': 'Electronic textiles, also known as smart garments, '
#                       'smart clothing, smart textiles, or smart fabrics, are '
#                       'fabrics that enable digital components such as a '
#                       'battery and a light (including small computers), and '
#                       'electronics to be embedded in them.',
#           'subjects': [('Simple',
#                         'digital components such as a battery and a light '
#                         '(including small computers')]},
