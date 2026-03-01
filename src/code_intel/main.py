import argparse
import os
from dotenv import load_dotenv

from code_intel.parser.python_parser import parse_repo
from code_intel.storage.neo4j_client import Neo4jClient
from code_intel.llm.llm_service import LLMService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Path to repository")
    parser.add_argument("--impact", help="Find functions impacted by given function name")
    parser.add_argument("--rank", action="store_true", help="Rank critical functions")

    args = parser.parse_args()

    load_dotenv()

    neo4j = Neo4jClient(
        uri=os.getenv("NEO4J_URI"),
        user=os.getenv("NEO4J_USER"),
        password=os.getenv("NEO4J_PASSWORD"),
    )

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
            for f in impact:
                print(f"- {f['name']} (depth: {f['depth']})")

            risk = neo4j.calculate_risk(impact)
            print(f"\n🔥 Risk Score: {risk}")

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

    llm = LLMService()

    print("\nGenerating AI summaries...\n")

    for func in results:
        summary = llm.summarize_function(func["source"])
        func["summary"] = summary
        print(f"Summary for {func['function_name']}: {summary}")

    neo4j.store_functions(results)
    neo4j.close()

    print("\nData stored in Neo4j successfully 🚀")


if __name__ == "__main__":
    main()