from neo4j import GraphDatabase
import os

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()

    def store_functions(self, results):
        function_names = {f["function_name"] for f in results}
        with self.driver.session() as session:
            for func in results:
                session.execute_write(self._create_function_node, func, function_names)

    @staticmethod
    def _create_function_node(tx, func, function_names):
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
            if called not in function_names:
                continue  

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
        MATCH (f:Function {name: $name})
        MATCH path = (dependent:Function)-[:CALLS*1..]->(f)
        RETURN dependent.name AS name,
            min(length(path)) AS depth
        ORDER BY depth
        """
        result = tx.run(query, name=function_name)
        return [
            {"name": record["name"], "depth": record["depth"]}
            for record in result
        ]
    
    def calculate_risk(self, impact_data):
        if not impact_data:
            return 0

        direct = sum(1 for f in impact_data if f["depth"] == 1)
        indirect = sum(1 for f in impact_data if f["depth"] > 1)
        max_depth = max(f["depth"] for f in impact_data)

        risk_score = (direct * 3) + (indirect * 2) + (max_depth * 2)

        return risk_score
    
    def get_global_risk(self):
        with self.driver.session() as session:
            return session.execute_read(self._global_risk_query)

    @staticmethod
    def _global_risk_query(tx):
        query = """
        MATCH (f:Function)
        OPTIONAL MATCH path = (dependent:Function)-[:CALLS*1..]->(f)
        WITH f,
            collect(DISTINCT dependent) AS dependents,
            max(length(path)) AS max_depth
        RETURN f.name AS name,
            size(dependents) AS total_dependents,
            coalesce(max_depth, 0) AS depth
        ORDER BY total_dependents DESC, depth DESC
        """
        result = tx.run(query)
        return [
            {
                "name": record["name"],
                "total_dependents": record["total_dependents"],
                "depth": record["depth"],
            }
            for record in result
        ]
    
    def calculate_global_risk(self, entry):
        return (entry["total_dependents"] * 3) + (entry["depth"] * 2)