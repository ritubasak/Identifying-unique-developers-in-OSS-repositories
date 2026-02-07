
import pytest
import tempfile
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def sample_developer_records():
    """Sample developer records for testing."""
    return [
        {
            'original_name': 'John Smith',
            'original_email': 'john.smith@example.com',
            'normalized_name': 'john smith',
            'first_name': 'john',
            'last_name': 'smith',
            'email_prefix': 'johnsmith',
            'name_variants': ['john']
        },
        {
            'original_name': 'John Smyth',
            'original_email': 'john.smyth@example.org',
            'normalized_name': 'john smyth',
            'first_name': 'john',
            'last_name': 'smyth',
            'email_prefix': 'johnsmyth',
            'name_variants': ['john']
        },
        {
            'original_name': 'Robert Johnson',
            'original_email': 'robert@example.com',
            'normalized_name': 'robert johnson',
            'first_name': 'robert',
            'last_name': 'johnson',
            'email_prefix': 'robert',
            'name_variants': ['robert', 'bob']
        },
        {
            'original_name': 'Bob Johnson',
            'original_email': 'bob@example.com',
            'normalized_name': 'bob johnson',
            'first_name': 'bob',
            'last_name': 'johnson',
            'email_prefix': 'bob',
            'name_variants': ['bob', 'robert']
        },
        {
            'original_name': 'Jane Doe',
            'original_email': 'jane.doe@different.com',
            'normalized_name': 'jane doe',
            'first_name': 'jane',
            'last_name': 'doe',
            'email_prefix': 'janedoe',
            'name_variants': ['jane']
        }
    ]

@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_duplicates():
    """Sample duplicate pairs for testing."""
    return [
        {
            'record1': {
                'original_name': 'John Smith',
                'original_email': 'john.smith@example.com',
                'normalized_name': 'john smith',
                'email_prefix': 'johnsmith'
            },
            'record2': {
                'original_name': 'John Smyth',
                'original_email': 'john.smyth@example.org',
                'normalized_name': 'john smyth',
                'email_prefix': 'johnsmyth'
            },
            'similarity_results': {
                'c1': 0.9,
                'c2': 0.8,
                'c3_first': 1.0,
                'c3_last': 0.8
            },
            'matched_conditions': ['C1', 'C3']
        },
        {
            'record1': {
                'original_name': 'Robert Johnson',
                'original_email': 'robert@example.com',
                'normalized_name': 'robert johnson',
                'email_prefix': 'robert'
            },
            'record2': {
                'original_name': 'Bob Johnson',
                'original_email': 'bob@example.com',
                'normalized_name': 'bob johnson',
                'email_prefix': 'bob'
            },
            'similarity_results': {
                'c1': 0.7,
                'c2': 0.6,
                'c3_first': 0.5,
                'c3_last': 1.0,
                'c8': 1.0
            },
            'matched_conditions': ['C8']
        }
    ]