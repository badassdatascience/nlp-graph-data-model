#
# load useful libraries
#
from neo4j.v1 import GraphDatabase
from credentials import uri, username, password

#
# connect to Neo4j
#
driver = GraphDatabase.driver(uri, auth=(username, password))

#
# delete all relationships
#
cmd = 'MATCH (c1)-[r]-(c2) DELETE r;'
with driver.session() as session:
    session.run(cmd)

#
# delete all nodes
#
cmd = 'MATCH (c) DELETE c';
with driver.session() as session:
    session.run(cmd)

#
# close the connection
#
driver.close()

