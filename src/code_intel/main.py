import argparse
import os
from dotenv import load_dotenv

from code_intel.parser.python_parser import parse_repo
from code_intel.storage.neo4j_client import Neo4jClient
from code_intel.llm.llm_service import LLMService
from code_intel.memory.chroma_service import ChromaService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Path to repository")
    parser.add_argument("--impact", help="Find functions impacted by given function name")
    parser.add_argument("--rank", action="store_true", help="Rank critical functions")
    parser.add_argument("--dead-code", action="store_true")
    parser.add_argument("--ask", type=str)

    args = parser.parse_args()

    load_dotenv()

    neo4j = Neo4jClient(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
    )

    llm = LLMService()
    memory = ChromaService()

    if args.ask:
        relevant_docs = memory.query(args.ask)

        context = "\n".join(relevant_docs)

        prompt = f"""
        You are analyzing a Python codebase.

        Relevant function summaries:
        {context}

        Question:
        {args.ask}

        Answer concisely and technically.
        """

        response = llm.client.chat.completions.create(
            model="anthropic/claude-opus-4.6",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        print("\n🧠 Answer:\n")
        print(response.choices[0].message.content.strip())
        return

    if args.dead_code:
        dead_functions = neo4j.get_dead_code()

        if dead_functions:
            print("\n🧹 Dead Code Detected:\n")
            for func in dead_functions:
                print(f"- {func}")
        else:
            print("\n✅ No dead code found.")
        
        return

    if args.rank:
        ranking = neo4j.get_global_risk()
        print("\n📊 Critical Function Ranking:\n")

        for entry in ranking:
            risk = neo4j.calculate_global_risk(entry)
            print(f"{entry['name']} → Dependents: {entry['total_dependents']}, Depth: {entry['depth']}, Risk: {risk}")

        return

    # 🔥 If impact flag is provided, just query impact
    if args.impact:
        impact = neo4j.get_impact(args.impact)

        print(f"\nFunctions impacted by changes to '{args.impact}':\n")

        if not impact:
            print("No dependent functions found.")
        else:
            risk = neo4j.calculate_risk(impact)
            print(f"\n🔥 Risk Score: {risk}")

            explanation = llm.explain_impact(
                function_name=args.impact,
                impact_data=impact,
                risk_score=risk
            )

            print("\n🧠 AI Explanation:\n")
            print(explanation)

        neo4j.close()
        return

    # 🔥 Otherwise parse + summarize + store
    results = parse_repo(args.repo)

    print("\nParsed Functions:\n")
    for func in results:
        print(f"File: {func['file']}")
        print(f"Function: {func['function_name']}")
        print(f"Calls: {func['calls']}")
        print("-" * 40)

    print("\nGenerating AI summaries...\n")

    for func in results:
        summary = llm.summarize_function(func["source"])
        memory.store_function_summary(func['function_name'], summary)
        func["summary"] = summary
        print(f"Summary for {func['function_name']}: {summary}")

    neo4j.store_functions(results)
    neo4j.close()

    print("\nData stored in Neo4j successfully 🚀")


if __name__ == "__main__":
    main()