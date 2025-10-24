"""CLI command to create a new review project."""
import click
import json
from database.connection import get_database_connection
from database.queries import ReviewDatabase

@click.command()
@click.option('--name', required=True, help='Review project name')
@click.option('--question', required=True, help='Research question')
@click.option('--reviewers', required=True, help='Comma-separated reviewer IDs')
@click.option('--criteria', help='Inclusion criteria (JSON string)')
@click.option('--ai/--no-ai', default=True, help='Use AI theme suggestions')
@click.option('--db-path', help='Database path (default: literature_review.db)')
def create_review(name, question, reviewers, criteria, ai, db_path):
    """Initialize a new literature review project."""
    # Parse reviewers
    reviewer_list = [r.strip() for r in reviewers.split(',')]

    # Parse criteria
    if criteria:
        try:
            criteria_dict = json.loads(criteria)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON for criteria", err=True)
            raise click.Abort()
    else:
        criteria_dict = {}

    # Create review
    conn = get_database_connection(db_path)
    review_db = ReviewDatabase(conn)

    review_id = review_db.create_review(
        review_name=name,
        research_question=question,
        inclusion_criteria_json=json.dumps(criteria_dict),
        reviewers_json=json.dumps(reviewer_list),
        use_ai_suggestions=ai
    )

    conn.close()

    # Output success
    click.echo(f"✓ Created review project: {review_id}")
    click.echo(f"  Name: {name}")
    click.echo(f"  Research Question: {question}")
    click.echo(f"  Reviewers: {', '.join(reviewer_list)}")
    click.echo(f"  AI Suggestions: {'Enabled' if ai else 'Disabled'}")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  1. Import papers: python cli/import_papers.py --review-id {review_id} --pdf-dir path/to/pdfs")
    click.echo(f"  2. Start screening: python cli/run_screening.py --review-id {review_id} --reviewer-id <your-id> --stage title_abstract")

if __name__ == '__main__':
    create_review()
