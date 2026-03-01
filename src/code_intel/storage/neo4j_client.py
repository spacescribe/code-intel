from neo4j import GraphDatabase
import os

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()

    def store_functions(self, results):
        with self.driver.session() as session:
            for func in results:
                session.execute_write(self._create_function_node, func)

    @staticmethod
    def _create_function_node(tx, func):
        tx.run(
            """
            MERGE (f:Function {name: $name})
            SET f.file = $file,
                f.summary = $summary
            """,
            name=func["function_name"],
            file=func["file"],
            summary=func.get("summary", "")
        )

        for called in func["calls"]:
            tx.run(
                """
                MERGE (caller:Function {name: $caller})
                MERGE (callee:Function {name: $callee})
                MERGE (caller)-[:CALLS]->(callee)
                """,
                caller=func["function_name"],
                callee=called
            )

    def get_impact(self, function_name: str):
        with self.driver.session() as session:
            result = session.execute_read(self._impact_query, function_name)
            return result 

    @staticmethod
    def _impact_query(tx, function_name):
        query = """
        MATCH (f:Function {name: $name})<-[:CALLS*]-(dependent)
        RETURN DISTINCT dependent.name AS name
        """
        result = tx.run(query, name = function_name)
        return [record["name"] for record in result]