import pytest
from click.testing import CliRunner
from cli.create_review import create_review
from database.connection import get_database_connection
from database.queries import ReviewDatabase

def test_create_review_command():
    """Test create review CLI command."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(create_review, [
            '--name', 'Test Review',
            '--question', 'What is the impact?',
            '--reviewers', 'reviewer_A,reviewer_B',
            '--ai'
        ])

        assert result.exit_code == 0
        assert 'Created review project' in result.output
        assert 'reviewer_A' in result.output

def test_create_review_no_ai():
    """Test creating review without AI."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(create_review, [
            '--name', 'Manual Review',
            '--question', 'Research question?',
            '--reviewers', 'reviewer_A',
            '--no-ai'
        ])

        assert result.exit_code == 0
        assert 'Created review project' in result.output
