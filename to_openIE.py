
#
# load useful libraries
#
from credentials import uri, username, password

from neo4j.v1 import GraphDatabase
import json

#
# user settings
#
global_word = 'textil'
output_directory = 'output'

#
# connect to Neo4j
#
driver = GraphDatabase.driver(uri, auth=(username, password))

#
# extract all sentences containing the global word
#
cmd = 'MATCH (wg:WORD_GLOBAL)<-[rwlwg:HAS_WORD_GLOBAL]-(wl:WORD_LOCAL)-[rs:HAS_SENTENCE]->(s:SENTENCE)-[rh:HAS_HEADING]->(h:HEADING)-[ra:HAS_ARTICLE]->(a:ARTICLE) WHERE wg.text = "' + global_word + '" RETURN wg.text AS global_word, wl.text AS local_word, a.name AS article, h.title AS heading, s.text AS sentence, ID(s) as sentence_id ORDER BY h.position_in_article, s.position_in_heading;'

with driver.session() as session:
    results = session.run(cmd)

#
# get unique results (crude, should have done this in the query)
#
sentences_to_id = {}
for record in results:
    sentences_to_id[record['sentence']] = record['sentence_id']

#
# save ids
#
with open(output_directory + '/sentences_to_id.json', 'w') as f:
    json.dump(sentences_to_id, f, indent=4)

#
# write file for Open IE analysis
#
f = open(output_directory + '/send_to_open_IE.txt', 'w')
for sentence in sentences_to_id.keys():
    f.write(sentence + '\n')
    f.write('\n')
f.close()
