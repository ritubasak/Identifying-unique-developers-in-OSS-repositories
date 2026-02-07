
import pytest
import sys
import os
import tempfile
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import save_duplicates_csv, calculate_precision_recall, validate_duplicate_pair

class TestUtils:
    """Test cases for utility functions."""
    
    def test_save_duplicates_csv_empty(self):
        """Test saving empty duplicates list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            filename = f.name
        
        try:
            save_duplicates_csv([], filename)
            
            # Check that file was created with headers
            with open(filename, 'r') as f:
                content = f.read()
                assert 'record1_name' in content
                assert 'record1_email' in content
                assert 'record2_name' in content
                assert 'record2_email' in content
        finally:
            os.unlink(filename)
    
    def test_save_duplicates_csv_with_data(self):
        """Test saving duplicates with data."""
        duplicates = [
            {
                'record1': {
                    'original_name': 'John Smith',
                    'original_email': 'john@example.com',
                    'normalized_name': 'john smith',
                    'email_prefix': 'john'
                },
                'record2': {
                    'original_name': 'John Smyth',
                    'original_email': 'john@example.org',
                    'normalized_name': 'john smyth',
                    'email_prefix': 'john'
                },
                'similarity_results': {'c1': 0.9, 'c2': 0.8},
                'matched_conditions': ['C1', 'C2']
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            filename = f.name
        
        try:
            save_duplicates_csv(duplicates, filename)
            
            # Check that file was created with data
            with open(filename, 'r') as f:
                content = f.read()
                assert 'John Smith' in content
                assert 'John Smyth' in content
                assert 'john@example.com' in content
                assert 'john@example.org' in content
                assert 'C1, C2' in content
        finally:
            os.unlink(filename)
    
    def test_calculate_precision_recall(self):
        """Test precision and recall calculation."""
        duplicates = [{'id': 1}, {'id': 2}, {'id': 3}]
        
        # Perfect precision and recall
        metrics = calculate_precision_recall(duplicates, 3, 0)
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1_score'] == 1.0
        
        # Some false positives
        metrics = calculate_precision_recall(duplicates, 2, 1)
        assert metrics['precision'] == 2/3
        assert metrics['recall'] == 2/3
        assert metrics['f1_score'] == 2/3
        
        # No duplicates detected
        metrics = calculate_precision_recall([], 0, 0)
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1_score'] == 0.0
    
    def test_validate_duplicate_pair(self):
        """Test duplicate pair validation."""
        record1 = {
            'normalized_name': 'john smith',
            'original_email': 'john@example.com',
            'email_prefix': 'john'
        }
        
        record2 = {
            'normalized_name': 'john smyth',
            'original_email': 'john@example.org',
            'email_prefix': 'john'
        }
        
        validation = validate_duplicate_pair(record1, record2)
        
        assert 'is_likely_duplicate' in validation
        assert 'confidence' in validation
        assert 'evidence' in validation
        assert 'warnings' in validation
        
        # Should be likely duplicate due to identical email prefixes
        assert validation['is_likely_duplicate'] == True
        assert validation['confidence'] > 0.5
        assert len(validation['evidence']) > 0
    
    def test_validate_duplicate_pair_different(self):
        """Test validation of clearly different records."""
        record1 = {
            'normalized_name': 'john smith',
            'original_email': 'john@example.com',
            'email_prefix': 'john'
        }
        
        record2 = {
            'normalized_name': 'jane doe',
            'original_email': 'jane@different.com',
            'email_prefix': 'jane'
        }
        
        validation = validate_duplicate_pair(record1, record2)
        
        # Should not be likely duplicate
        assert validation['is_likely_duplicate'] == False
        assert validation['confidence'] < 0.5