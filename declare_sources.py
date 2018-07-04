
#
# user settings
#
source_file = 'data/sources.csv'

#
# load useful libraries
#
from neo4j.v1 import GraphDatabase
from credentials import uri, username, password
import pandas as pd

#
# connect to Neo4j
#
driver = GraphDatabase.driver(uri, auth=(username, password))

#
# load sources
#
sources = pd.read_csv(source_file)

#
# load sources into database
#
for name, language in zip(sources['name'], sources['language']):
    cmd = 'MERGE (s:SOURCE {name : $name, language : $language}) RETURN s;'
    with driver.session() as session:
        session.run(cmd, name=name.lower(), language=language.lower())

#
# close the connection
#
driver.close()
