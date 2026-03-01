class ToolRegistry:
    def __init__(self, neo4j_service, memory_service, llm_service):
        self.neo4j = neo4j_service
        self.memory = memory_service
        self.llm = llm_service

    def get_impact(self, function_name: str):
        impact = self.neo4j.get_impact(function_name)
        risk = self.neo4j.calculate_risk(impact)
        return {
            "impact": impact,
            "risk": risk
        }

    def get_dead_code(self):
        return self.neo4j.get_dead_code()

    def search_memory(self, query: str):
        return self.memory.query(query)

    def summarize_function(self, function_name: str):
        source = self.neo4j.get_function_source(function_name)
        return self.llm.summarize_function(source)