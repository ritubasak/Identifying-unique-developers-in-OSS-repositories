import string
import re
import unidecode
from typing import Tuple, Optional, List
import logging

class DataClean:
    """
    Data cleaning and normalization utilities for developer identity deduplication.
    """
    
    def __init__(self):
        """Initialize the DataClean class with logging."""
        self.logger = logging.getLogger(__name__)
        
        # Common nickname mappings for improved matching
        self.nickname_mappings = {
            'bob': 'robert', 'bobby': 'robert', 'rob': 'robert',
            'bill': 'william', 'billy': 'william', 'will': 'william',
            'dick': 'richard', 'rick': 'richard', 'rich': 'richard',
            'jim': 'james', 'jimmy': 'james', 'jamie': 'james',
            'mike': 'michael', 'mickey': 'michael', 'mick': 'michael',
            'dave': 'david', 'davey': 'david',
            'steve': 'steven', 'stevie': 'steven',
            'chris': 'christopher', 'christy': 'christopher',
            'dan': 'daniel', 'danny': 'daniel',
            'matt': 'matthew', 'matty': 'matthew',
            'joe': 'joseph', 'joey': 'joseph',
            'tom': 'thomas', 'tommy': 'thomas',
            'pat': 'patrick', 'patty': 'patrick',
            'tim': 'timothy', 'timmy': 'timothy',
            'al': 'albert', 'alex': 'alexander', 'andy': 'andrew',
            'ben': 'benjamin', 'brad': 'bradley', 'brian': 'brian',
            'charles': 'charles', 'charlie': 'charles',
            'ed': 'edward', 'eddie': 'edward',
            'frank': 'franklin', 'fred': 'frederick',
            'george': 'george', 'greg': 'gregory',
            'henry': 'henry', 'harry': 'henry',
            'jeff': 'jeffrey', 'john': 'johnny',
            'ken': 'kenneth', 'kenny': 'kenneth',
            'larry': 'lawrence', 'leo': 'leonard',
            'mark': 'marcus', 'martin': 'martin',
            'paul': 'paul', 'pete': 'peter',
            'phil': 'philip', 'ray': 'raymond',
            'sam': 'samuel', 'scott': 'scott',
            'sean': 'sean', 'shawn': 'sean',
            'ted': 'theodore', 'tony': 'anthony',
            'vic': 'victor', 'walter': 'walter'
        }


    def _validate_email(self, email_address: str) -> int:
        """
        Validate email address format.
        
        Args:
            email_address: Email address to validate
            
        Returns:
            0 if email is valid, 1 if no @ symbol, 2 if no domain dot
        """
        if not email_address or not isinstance(email_address, str):
            return 2
            
        # Check for @ symbol
        if '@' not in email_address:
            return 1
            
        # Check for domain dot
        parts = email_address.split('@')
        if len(parts) != 2 or '.' not in parts[1]:
            return 2
        
        # Check for empty prefix (email starting with @)
        if not parts[0]:
            return 1
            
        return 0

    def normalize_name(self, name: str) -> str:
        """
        Normalize a developer name according to Bird et al. methodology.
        
        Args:
            name: Raw developer name
            
        Returns:
            Normalized name (lowercase, no accents, no punctuation)
        """
        if not name or not isinstance(name, str):
            return ""
            
        # Remove accents and diacritics
        normalized = unidecode.unidecode(name)
        
        # Convert to lowercase
        normalized = normalized.lower()
        
        # Remove punctuation and extra whitespace (but keep hyphens as spaces)
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = normalized.replace('-', ' ')
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()

    def split_name(self, name: str) -> Tuple[str, str]:
        """
        Split a normalized name into first and last components.
        
        Args:
            name: Normalized name
            
        Returns:
            Tuple of (first_name, last_name)
        """
        if not name:
            return "", ""
            
        parts = name.split()
        if len(parts) == 0:
            return "", ""
        elif len(parts) == 1:
            return parts[0], ""
        else:
            return parts[0], parts[-1]

    def normalize_email_prefix(self, email: str) -> str:
        """
        Extract and normalize the prefix part of an email address.
        
        Args:
            email: Email address
            
        Returns:
            Normalized email prefix (before @)
        """
        if not email or '@' not in email:
            return ""
            
        prefix = email.split('@')[0]
        
        # Remove common email prefixes and suffixes
        if prefix.startswith('+'):
            prefix = prefix[1:]
        prefix = prefix.replace('+', '')
        prefix = prefix.replace('.', '').replace('_', '').replace('-', '')
        
        # Convert to lowercase
        prefix = prefix.lower()
        
        return prefix

    def get_nickname_variants(self, name: str) -> List[str]:
        """
        Get nickname variants for a given name.
        
        Args:
            name: Name to get variants for
            
        Returns:
            List of possible nickname variants
        """
        variants = [name]
        name_lower = name.lower()
        
        # Check if name is a nickname
        for nickname, full_name in self.nickname_mappings.items():
            if name_lower == nickname:
                variants.append(full_name)
            elif name_lower == full_name:
                variants.append(nickname)
                
        return list(set(variants))  # Remove duplicates

    def is_valid_developer_record(self, name: str, email: str) -> bool:
        """
        Check if a developer record is valid for processing.
        
        Args:
            name: Developer name
            email: Developer email
            
        Returns:
            True if record is valid, False otherwise
        """
        if not name or not email:
            return False
            
        # Check if name is not just whitespace or special characters
        if not name.strip() or len(name.strip()) < 2:
            return False
            
        # Check if email is valid
        if self._validate_email(email) != 0:
            return False
            
        return True

    def preprocess_developer_data(self, name: str, email: str) -> Optional[dict]:
        """
        Preprocess a developer record for deduplication.
        
        Args:
            name: Raw developer name
            email: Raw developer email
            
        Returns:
            Dictionary with preprocessed data or None if invalid
        """
        if not self.is_valid_developer_record(name, email):
            return None
            
        normalized_name = self.normalize_name(name)
        first_name, last_name = self.split_name(normalized_name)
        email_prefix = self.normalize_email_prefix(email)
        
        return {
            'original_name': name,
            'original_email': email,
            'normalized_name': normalized_name,
            'first_name': first_name,
            'last_name': last_name,
            'email_prefix': email_prefix,
            'name_variants': self.get_nickname_variants(normalized_name)
        }
