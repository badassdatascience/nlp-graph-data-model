
#
# load useful libraries
#
from credentials import uri, username, password

from neo4j.v1 import GraphDatabase
import json
import pprint as pp

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
        object_list = [(x.split(',List([')[0].split('Argument(')[0].strip(), x.split(',List([')[0].split('Argument(')[1].strip()) for x in subject.split(';')]
    except:
        pass

    relation = relation.replace('Relation(', '').split(',List([')[0]

    subject_list = []
    try:
        subject_list = [(x.split(',List([')[0].split('Argument(')[0].strip(), x.split(',List([')[0].split('Argument(')[1].strip()) for x in object.split(';')]
    except:
        pass

    if not sentence_id in results:
        results[sentence_id] = []
    results[sentence_id].append({
            'score' : score,
            'objects' : object_list,
            'relation' : relation,
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
cmd = 'MATCH (q)-[r:HAS_OPENIE_RELATION]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (q)-[r:HAS_OPENIE_OBJECT]-(n) DELETE r;'
with driver.session() as session:
    query_results = session.run(cmd)
cmd = 'MATCH (q)-[r:HAS_OPENIE_SUBJECT]-(n) DELETE r;'
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

#
# load Neo4j with OpenIE 5.0 results
#
for sentence_id in results.keys():
    for finding in results[sentence_id]:
        relation = finding['relation']

        sentence = finding['sentence']
        cmd = 'MATCH (s:SENTENCE) WHERE s.text = $sentence AND ID(s) = $sentence_id CREATE (ro:OPENIE_RELATION {text : $relation_text})<-[r:HAS_OPENIE_RELATION]-(s) RETURN s, ro, r;'
        with driver.session() as session:
            query_results = session.run(cmd, sentence = sentence, sentence_id = sentence_id, relation_text = relation)
        for record in query_results:
            relation_id = record['ro'].id

        for type, object in finding['objects']:
            cmd = 'MATCH (ro:OPENIE_RELATION) WHERE ID(ro) = $relation_id MERGE (ro)-[r:HAS_OPENIE_OBJECT]->(oo:OPENIE_OBJECT {type : $type, text : $text}) RETURN oo;'
            with driver.session() as session:
                query_results = session.run(cmd, relation_id = relation_id, type=type, text = object)






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
