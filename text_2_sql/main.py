import json
from rich import print
from agents.table_selector import select_tables
from agents.metadata_context import build_context
from agents.sql_generator import generate_sql
from agents.sql_refiner import refine_sql

with open("table_repo.json") as f:
    table_repo = json.load(f)

with open("metadata_repo.json") as f:
    metadata_repo = json.load(f)

def main():
    print("\n[bold cyan]Interactive Text-to-SQL Agent (Gemini 2.5 Pro)[/bold cyan]\n")

    user_query = input("Ask your question: ")

    print("\n[bold yellow]Step 1: Table Identification[/bold yellow]")
    selected_tables = select_tables(user_query, table_repo)
    print("Identified tables:", selected_tables)

    confirm = input("\nConfirm tables? (y/n): ")
    if confirm.lower() != "y":
        selected_tables = json.loads(
            input("Enter corrected table list (JSON array): ")
        )

    print("\n[bold yellow]Step 2: Schema Context Building[/bold yellow]")
    schema_context = build_context(
        user_query,
        selected_tables,
        metadata_repo
    )

    print("\n[bold yellow]Step 3: SQL Generation[/bold yellow]")
    sql = generate_sql(user_query, schema_context)
    print("\n[bold green]Generated SQL[/bold green]\n")
    print(sql)

    while True:
        refine = input("\nRefine SQL? (y/n): ")
        if refine.lower() != "y":
            break

        refinement = input("Enter refinement: ")
        sql = refine_sql(sql, refinement)
        print("\n[bold green]Updated SQL[/bold green]\n")
        print(sql)

    print("\n[bold cyan]Session Complete ✔[/bold cyan]")

if __name__ == "__main__":
    main()
