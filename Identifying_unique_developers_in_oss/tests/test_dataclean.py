
import pytest
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from DataClean import DataClean

class TestDataClean:
    """Test cases for DataClean class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cleaner = DataClean()
    
    
    def test_validate_email(self):
        """Test email validation."""
        assert self.cleaner._validate_email("test@example.com") == 0
        assert self.cleaner._validate_email("user.name@domain.org") == 0
        assert self.cleaner._validate_email("invalid-email") == 1
        assert self.cleaner._validate_email("test@") == 2
        assert self.cleaner._validate_email("@domain.com") == 1
        assert self.cleaner._validate_email("") == 2
        assert self.cleaner._validate_email(None) == 2
    
    def test_normalize_name(self):
        """Test name normalization."""
        assert self.cleaner.normalize_name("John Smith") == "john smith"
        assert self.cleaner.normalize_name("José María") == "jose maria"
        assert self.cleaner.normalize_name("O'Connor") == "oconnor"
        assert self.cleaner.normalize_name("  John   Smith  ") == "john smith"
        assert self.cleaner.normalize_name("") == ""
        assert self.cleaner.normalize_name(None) == ""
        assert self.cleaner.normalize_name("John-Smith") == "john smith"
    
    def test_split_name(self):
        """Test name splitting."""
        assert self.cleaner.split_name("john smith") == ("john", "smith")
        assert self.cleaner.split_name("john") == ("john", "")
        assert self.cleaner.split_name("john michael smith") == ("john", "smith")
        assert self.cleaner.split_name("") == ("", "")
        assert self.cleaner.split_name("   ") == ("", "")
    
    def test_normalize_email_prefix(self):
        """Test email prefix normalization."""
        assert self.cleaner.normalize_email_prefix("john.smith@example.com") == "johnsmith"
        assert self.cleaner.normalize_email_prefix("j.smith@example.com") == "jsmith"
        assert self.cleaner.normalize_email_prefix("john+tag@example.com") == "johntag"
        assert self.cleaner.normalize_email_prefix("john-smith@example.com") == "johnsmith"
        assert self.cleaner.normalize_email_prefix("invalid-email") == ""
        assert self.cleaner.normalize_email_prefix("") == ""
    
    def test_get_nickname_variants(self):
        """Test nickname variant generation."""
        variants = self.cleaner.get_nickname_variants("robert")
        assert "bob" in variants
        assert "robert" in variants
        
        variants = self.cleaner.get_nickname_variants("bob")
        assert "robert" in variants
        assert "bob" in variants
        
        variants = self.cleaner.get_nickname_variants("unknown")
        assert variants == ["unknown"]
    
    def test_is_valid_developer_record(self):
        """Test developer record validation."""
        assert self.cleaner.is_valid_developer_record("John Smith", "john@example.com") == True
        assert self.cleaner.is_valid_developer_record("", "john@example.com") == False
        assert self.cleaner.is_valid_developer_record("John Smith", "") == False
        assert self.cleaner.is_valid_developer_record("John Smith", "invalid-email") == False
        assert self.cleaner.is_valid_developer_record("J", "john@example.com") == False
        assert self.cleaner.is_valid_developer_record("   ", "john@example.com") == False
    
    def test_preprocess_developer_data(self):
        """Test complete preprocessing pipeline."""
        result = self.cleaner.preprocess_developer_data("John Smith", "john.smith@example.com")
        
        assert result is not None
        assert result['original_name'] == "John Smith"
        assert result['original_email'] == "john.smith@example.com"
        assert result['normalized_name'] == "john smith"
        assert result['first_name'] == "john"
        assert result['last_name'] == "smith"
        assert result['email_prefix'] == "johnsmith"
        assert isinstance(result['name_variants'], list)
        
        # Test invalid record
        result = self.cleaner.preprocess_developer_data("", "invalid-email")
        assert result is None
