"""
Test suite for DataCompare class.

This module contains unit tests for the Bird et al. heuristic and improved methods.
"""

import pytest
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from DataCompare import DataCompare


class TestDataCompare:
    """Test cases for DataCompare class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.comparer = DataCompare(threshold=0.8)

    def test_calculate_similarity(self):
        """Test similarity calculation methods."""
        # Test Levenshtein similarity
        sim = self.comparer._calculate_similarity("john", "john", 'levenshtein')
        assert sim == 1.0

        sim = self.comparer._calculate_similarity("john", "jane", 'levenshtein')
        assert 0.0 <= sim <= 1.0

        # Test Jaro-Winkler similarity
        sim = self.comparer._calculate_similarity("john", "john", 'jaro_winkler')
        assert sim == 1.0

        sim = self.comparer._calculate_similarity("john", "jane", 'jaro_winkler')
        assert 0.0 <= sim <= 1.0

        # Test edge cases
        assert self.comparer._calculate_similarity("", "john", 'levenshtein') == 0.0
        assert self.comparer._calculate_similarity("john", "", 'levenshtein') == 0.0
        assert self.comparer._calculate_similarity("", "", 'levenshtein') == 0.0

    def test_condition_c1(self):
        """Test condition C1: full name similarity."""
        # Identical names
        assert self.comparer.condition_c1("john smith", "john smith") == True

        # Similar names above threshold
        assert self.comparer.condition_c1("john smith", "john smyth") == True

        # Different names below threshold
        assert self.comparer.condition_c1("john smith", "jane doe") == False

    def test_condition_c2(self):
        """Test condition C2: email prefix similarity."""
        # Identical prefixes
        assert self.comparer.condition_c2("johnsmith", "johnsmith") == True

        # Similar prefixes above threshold
        assert self.comparer.condition_c2("johnsmith", "johnsmyth") == True

        # Different prefixes below threshold
        assert self.comparer.condition_c2("johnsmith", "janedoe") == False

    def test_condition_c3(self):
        """Test condition C3: first and last name similarity."""
        # Both names similar
        assert self.comparer.condition_c3("john", "john", "smith", "smyth") == True

        # Only first name similar
        assert self.comparer.condition_c3("john", "john", "smith", "doe") == False

        # Only last name similar
        assert self.comparer.condition_c3("john", "jane", "smith", "smith") == False

        # Neither similar
        assert self.comparer.condition_c3("john", "jane", "smith", "doe") == False

    def test_condition_c4(self):
        """Test condition C4: prefix contains first initial + last name."""
        # Valid pattern
        assert self.comparer.condition_c4("jsmith", "john", "smith") == True

        # Invalid pattern
        assert self.comparer.condition_c4("jdoe", "john", "smith") == False

        # Edge cases
        assert self.comparer.condition_c4("", "john", "smith") == False
        assert self.comparer.condition_c4("jsmith", "", "smith") == False
        assert self.comparer.condition_c4("jsmith", "john", "") == False

    def test_condition_c5(self):
        """Test condition C5: prefix contains last initial + first name."""
        # Valid pattern
        assert self.comparer.condition_c5("sjohn", "john", "smith") == True

        # Invalid pattern
        assert self.comparer.condition_c5("djohn", "john", "smith") == False

    def test_condition_c6(self):
        """Test condition C6: prefix1 contains first initial + last name."""
        # Valid pattern
        assert self.comparer.condition_c6("jsmith", "jane", "smith") == True

        # Invalid pattern
        assert self.comparer.condition_c6("jdoe", "jane", "smith") == False

    def test_condition_c7(self):
        """Test condition C7: prefix1 contains last initial + first name."""
        # Valid pattern
        assert self.comparer.condition_c7("sjane", "jane", "smith") == True

        # Invalid pattern
        assert self.comparer.condition_c7("djane", "jane", "smith") == False

    def test_are_duplicates_bird(self):
        """Test Bird heuristic duplicate detection."""
        record1 = {
            'normalized_name': 'john smith',
            'email_prefix': 'johnsmith',
            'first_name': 'john',
            'last_name': 'smith'
        }

        record2 = {
            'normalized_name': 'john smith',
            'email_prefix': 'johnsmith',
            'first_name': 'john',
            'last_name': 'smith'
        }

        is_duplicate, results = self.comparer.are_duplicates_bird(record1, record2)
        assert is_duplicate == True
        assert 'c1' in results

    def test_check_nickname_match(self):
        """Test nickname matching."""
        variants1 = ['robert', 'bob']
        variants2 = ['bob', 'bobby']

        assert self.comparer._check_nickname_match(variants1, variants2) == True

        variants3 = ['john', 'johnny']
        assert self.comparer._check_nickname_match(variants1, variants3) == False

        # Edge cases
        assert self.comparer._check_nickname_match([], variants2) == False
        assert self.comparer._check_nickname_match(variants1, []) == False
        assert self.comparer._check_nickname_match([], []) == False

    def test_calculate_token_similarity(self):
        """Test token-based similarity."""
        # Identical names
        sim = self.comparer._calculate_token_similarity("john smith", "john smith")
        assert sim == 1.0

        # Partial overlap
        sim = self.comparer._calculate_token_similarity("john smith", "john doe")
        assert 0.0 < sim < 1.0

        # No overlap
        sim = self.comparer._calculate_token_similarity("john smith", "jane doe")
        assert sim == 0.0

        # Edge cases
        assert self.comparer._calculate_token_similarity("", "john smith") == 0.0
        assert self.comparer._calculate_token_similarity("john smith", "") == 0.0

    def test_calculate_domain_similarity(self):
        """Test email domain similarity."""
        # Identical domains
        sim = self.comparer._calculate_domain_similarity("john@example.com", "jane@example.com")
        assert sim == 1.0

        # Similar domains
        sim = self.comparer._calculate_domain_similarity("john@example.com", "jane@example.org")
        assert 0.0 <= sim <= 1.0

        # Edge cases
        assert self.comparer._calculate_domain_similarity("invalid-email", "jane@example.com") == 0.0
        assert self.comparer._calculate_domain_similarity("", "jane@example.com") == 0.0

    def test_are_duplicates_improved(self):
        """Test improved heuristic duplicate detection."""
        record1 = {
            'normalized_name': 'robert smith',
            'email_prefix': 'robertsmith',
            'first_name': 'robert',
            'last_name': 'smith',
            'name_variants': ['robert', 'bob'],
            'original_email': 'robert@example.com'
        }

        record2 = {
            'normalized_name': 'bob smith',
            'email_prefix': 'bobsmith',
            'first_name': 'bob',
            'last_name': 'smith',
            'name_variants': ['bob', 'robert'],
            'original_email': 'bob@example.com'
        }

        is_duplicate, results = self.comparer.are_duplicates_improved(record1, record2)
        # Should be detected as duplicate due to nickname matching
        assert is_duplicate == True
        assert 'c8' in results

    def test_get_matched_conditions(self):
        """Test matched conditions extraction."""
        similarity_results = {
            'c1': 0.9,
            'c2': 0.7,
            'c3_first': 0.9,
            'c3_last': 0.9,
            'c4': True,
            'c5': False,
            'c6': False,
            'c7': False
        }

        matched = self.comparer._get_matched_conditions(similarity_results)
        assert 'C1' in matched
        assert 'C3' in matched
        assert 'C4' in matched
        assert 'C5' not in matched