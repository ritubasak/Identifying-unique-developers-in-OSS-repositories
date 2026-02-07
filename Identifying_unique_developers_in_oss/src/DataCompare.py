import logging
from typing import List, Dict, Tuple, Optional
from rapidfuzz import fuzz
from Levenshtein import ratio as levenshtein_ratio
import re

class DataCompare:
    
    def __init__(self, threshold: float = 0.8):
        """
        Initialize the DataCompare class.
        
        Args:
            threshold: Similarity threshold for matching (0.0 to 1.0)
        """
        self.logger = logging.getLogger(__name__)
        self.threshold = threshold
        
        # Results storage for debugging
        self.similarity_results = {
            'c1': 0.0,  # Name similarity
            'c2': 0.0,  # Email prefix similarity
            'c3_first': 0.0,  # First name similarity
            'c3_last': 0.0,   # Last name similarity
            'c4': False,  # Prefix contains first initial + last name
            'c5': False,  # Prefix contains last initial + first name
            'c6': False,  # Prefix1 contains first initial + last name
            'c7': False   # Prefix1 contains last initial + first name
        }

    def _calculate_similarity(self, str1: str, str2: str, method: str = 'levenshtein') -> float:
        """
        Calculate similarity between two strings.
        
        Args:
            str1: First string
            str2: Second string
            method: Similarity method ('levenshtein' or 'jaro_winkler')
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not str1 or not str2:
            return 0.0
            
        if method == 'levenshtein':
            return levenshtein_ratio(str1.lower(), str2.lower())
        elif method == 'jaro_winkler':
            return fuzz.ratio(str1.lower(), str2.lower()) / 100.0
        else:
            raise ValueError(f"Unknown similarity method: {method}")

    def condition_c1(self, name1: str, name2: str) -> bool:
        """
        Condition C1: Similarity between full names >= threshold.
        
        Args:
            name1: First normalized name
            name2: Second normalized name
            
        Returns:
            True if condition is satisfied
        """
        similarity = self._calculate_similarity(name1, name2)
        self.similarity_results['c1'] = similarity
        return similarity >= self.threshold

    def condition_c2(self, prefix1: str, prefix2: str) -> bool:
        """
        Condition C2: Similarity between email prefixes >= threshold.
        
        Args:
            prefix1: First email prefix
            prefix2: Second email prefix
            
        Returns:
            True if condition is satisfied
        """
        similarity = self._calculate_similarity(prefix1, prefix2)
        self.similarity_results['c2'] = similarity
        return similarity >= self.threshold

    def condition_c3(self, first_name1: str, first_name2: str, 
                    last_name1: str, last_name2: str) -> bool:
        """
        Condition C3: Both first name AND last name similarity >= threshold.
        
        Args:
            first_name1: First person's first name
            first_name2: Second person's first name
            last_name1: First person's last name
            last_name2: Second person's last name
            
        Returns:
            True if condition is satisfied
        """
        first_sim = self._calculate_similarity(first_name1, first_name2)
        last_sim = self._calculate_similarity(last_name1, last_name2)
        
        self.similarity_results['c3_first'] = first_sim
        self.similarity_results['c3_last'] = last_sim
        
        return first_sim >= self.threshold and last_sim >= self.threshold

    def condition_c4(self, prefix2: str, first_name1: str, last_name1: str) -> bool:
        """
        Condition C4: prefix2 contains first initial of name1 + full last name of name1.
        
        Args:
            prefix2: Second person's email prefix
            first_name1: First person's first name
            last_name1: First person's last name
            
        Returns:
            True if condition is satisfied
        """
        if not first_name1 or not last_name1 or not prefix2:
            return False
            
        first_initial = first_name1[0].lower()
        pattern = f"{first_initial}{last_name1.lower()}"
        result = pattern in prefix2.lower()
        self.similarity_results['c4'] = result
        return result

    def condition_c5(self, prefix2: str, first_name1: str, last_name1: str) -> bool:
        """
        Condition C5: prefix2 contains last initial of name1 + full first name of name1.
        
        Args:
            prefix2: Second person's email prefix
            first_name1: First person's first name
            last_name1: First person's last name
            
        Returns:
            True if condition is satisfied
        """
        if not first_name1 or not last_name1 or not prefix2:
            return False
            
        last_initial = last_name1[0].lower()
        pattern = f"{last_initial}{first_name1.lower()}"
        result = pattern in prefix2.lower()
        self.similarity_results['c5'] = result
        return result

    def condition_c6(self, prefix1: str, first_name2: str, last_name2: str) -> bool:
        """
        Condition C6: prefix1 contains first initial of name2 + full last name of name2.
        
        Args:
            prefix1: First person's email prefix
            first_name2: Second person's first name
            last_name2: Second person's last name
            
        Returns:
            True if condition is satisfied
        """
        if not first_name2 or not last_name2 or not prefix1:
            return False
            
        first_initial = first_name2[0].lower()
        pattern = f"{first_initial}{last_name2.lower()}"
        result = pattern in prefix1.lower()
        self.similarity_results['c6'] = result
        return result

    def condition_c7(self, prefix1: str, first_name2: str, last_name2: str) -> bool:
        """
        Condition C7: prefix1 contains last initial of name2 + full first name of name2.
        
        Args:
            prefix1: First person's email prefix
            first_name2: Second person's first name
            last_name2: Second person's last name
            
        Returns:
            True if condition is satisfied
        """
        if not first_name2 or not last_name2 or not prefix1:
            return False
            
        last_initial = last_name2[0].lower()
        pattern = f"{last_initial}{first_name2.lower()}"
        result = pattern in prefix1.lower()
        self.similarity_results['c7'] = result
        return result

    def are_duplicates_bird(self, record1: Dict, record2: Dict) -> Tuple[bool, Dict]:
        """
        Check if two developer records are duplicates using Bird et al. heuristic.
        
        Args:
            record1: First developer record
            record2: Second developer record
            
        Returns:
            Tuple of (is_duplicate, similarity_results)
        """
        # Reset similarity results
        self.similarity_results = {key: 0.0 if isinstance(val, (int, float)) else False 
                                 for key, val in self.similarity_results.items()}
        
        # Extract normalized data
        name1 = record1.get('normalized_name', '')
        name2 = record2.get('normalized_name', '')
        prefix1 = record1.get('email_prefix', '')
        prefix2 = record2.get('email_prefix', '')
        first_name1 = record1.get('first_name', '')
        first_name2 = record2.get('first_name', '')
        last_name1 = record1.get('last_name', '')
        last_name2 = record2.get('last_name', '')
        
        # Check all seven conditions
        conditions = [
            self.condition_c1(name1, name2),
            self.condition_c2(prefix1, prefix2),
            self.condition_c3(first_name1, first_name2, last_name1, last_name2),
            self.condition_c4(prefix2, first_name1, last_name1),
            self.condition_c5(prefix2, first_name1, last_name1),
            self.condition_c6(prefix1, first_name2, last_name2),
            self.condition_c7(prefix1, first_name2, last_name2)
        ]
        
        is_duplicate = any(conditions)
        
        return is_duplicate, self.similarity_results.copy()

    def find_duplicates_bird(self, developer_records: List[Dict]) -> List[Dict]:
        """
        Find all duplicate pairs using Bird et al. heuristic.
        
        Args:
            developer_records: List of developer records
            
        Returns:
            List of duplicate pairs with similarity details
        """
        duplicates = []
        total_pairs = len(developer_records) * (len(developer_records) - 1) // 2
        processed_pairs = 0
        
        self.logger.info(f"Checking {total_pairs} pairs for duplicates using Bird heuristic")
        
        for i in range(len(developer_records)):
            for j in range(i + 1, len(developer_records)):
                record1 = developer_records[i]
                record2 = developer_records[j]
                
                is_duplicate, similarity_results = self.are_duplicates_bird(record1, record2)
                
                if is_duplicate:
                    duplicate_info = {
                        'record1': {
                            'original_name': record1['original_name'],
                            'original_email': record1['original_email'],
                            'normalized_name': record1['normalized_name'],
                            'email_prefix': record1['email_prefix']
                        },
                        'record2': {
                            'original_name': record2['original_name'],
                            'original_email': record2['original_email'],
                            'normalized_name': record2['normalized_name'],
                            'email_prefix': record2['email_prefix']
                        },
                        'similarity_results': similarity_results,
                        'matched_conditions': self._get_matched_conditions(similarity_results)
                    }
                    duplicates.append(duplicate_info)
                
                processed_pairs += 1
                if processed_pairs % 1000 == 0:
                    self.logger.info(f"Processed {processed_pairs}/{total_pairs} pairs, found {len(duplicates)} duplicates")
        
        self.logger.info(f"Bird heuristic complete: found {len(duplicates)} duplicate pairs")
        return duplicates

    def _get_matched_conditions(self, similarity_results: Dict) -> List[str]:
        """
        Get list of conditions that were matched.
        
        Args:
            similarity_results: Dictionary of similarity results
            
        Returns:
            List of matched condition names
        """
        matched = []
        
        if similarity_results['c1'] >= self.threshold:
            matched.append('C1')
        if similarity_results['c2'] >= self.threshold:
            matched.append('C2')
        if similarity_results['c3_first'] >= self.threshold and similarity_results['c3_last'] >= self.threshold:
            matched.append('C3')
        if similarity_results['c4']:
            matched.append('C4')
        if similarity_results['c5']:
            matched.append('C5')
        if similarity_results['c6']:
            matched.append('C6')
        if similarity_results['c7']:
            matched.append('C7')
            
        return matched

    def are_duplicates_improved(self, record1: Dict, record2: Dict) -> Tuple[bool, Dict]:
        """
        Check if two developer records are duplicates using improved heuristic.
        
        This improved method combines multiple similarity measures and includes
        nickname matching and weighted scoring for better precision and recall.
        
        Args:
            record1: First developer record
            record2: Second developer record
            
        Returns:
            Tuple of (is_duplicate, similarity_results)
        """
        # Reset similarity results
        self.similarity_results = {key: 0.0 if isinstance(val, (int, float)) else False 
                                 for key, val in self.similarity_results.items()}
        
        # Extract normalized data
        name1 = record1.get('normalized_name', '')
        name2 = record2.get('normalized_name', '')
        prefix1 = record1.get('email_prefix', '')
        prefix2 = record2.get('email_prefix', '')
        first_name1 = record1.get('first_name', '')
        first_name2 = record2.get('first_name', '')
        last_name1 = record1.get('last_name', '')
        last_name2 = record2.get('last_name', '')
        variants1 = record1.get('name_variants', [])
        variants2 = record2.get('name_variants', [])
        
        # Calculate weighted similarity scores
        scores = {}
        
        # C1: Full name similarity (Levenshtein + Jaro-Winkler)
        lev_sim = self._calculate_similarity(name1, name2, 'levenshtein')
        jw_sim = self._calculate_similarity(name1, name2, 'jaro_winkler')
        scores['c1'] = (lev_sim + jw_sim) / 2
        
        # C2: Email prefix similarity (Levenshtein + Jaro-Winkler)
        lev_prefix = self._calculate_similarity(prefix1, prefix2, 'levenshtein')
        jw_prefix = self._calculate_similarity(prefix1, prefix2, 'jaro_winkler')
        scores['c2'] = (lev_prefix + jw_prefix) / 2
        
        # C3: First and last name similarity
        first_sim = self._calculate_similarity(first_name1, first_name2, 'jaro_winkler')
        last_sim = self._calculate_similarity(last_name1, last_name2, 'jaro_winkler')
        scores['c3_first'] = first_sim
        scores['c3_last'] = last_sim
        scores['c3'] = (first_sim + last_sim) / 2
        
        # C4-C7: Pattern matching (same as Bird)
        c4 = self.condition_c4(prefix2, first_name1, last_name1)
        c5 = self.condition_c5(prefix2, first_name1, last_name1)
        c6 = self.condition_c6(prefix1, first_name2, last_name2)
        c7 = self.condition_c7(prefix1, first_name2, last_name2)
        
        # C8: Nickname matching
        nickname_match = self._check_nickname_match(variants1, variants2)
        scores['c8'] = 1.0 if nickname_match else 0.0
        
        # C9: Token-based similarity
        token_sim = self._calculate_token_similarity(name1, name2)
        scores['c9'] = token_sim
        
        # C10: Email domain similarity
        domain_sim = self._calculate_domain_similarity(record1.get('original_email', ''), 
                                                      record2.get('original_email', ''))
        scores['c10'] = domain_sim
        
        # Update similarity results
        self.similarity_results.update(scores)
        self.similarity_results['c4'] = c4
        self.similarity_results['c5'] = c5
        self.similarity_results['c6'] = c6
        self.similarity_results['c7'] = c7
        self.similarity_results['c8'] = nickname_match
        
        # Calculate weighted score
        weights = {
            'c1': 0.25,    # Full name similarity
            'c2': 0.20,    # Email prefix similarity
            'c3': 0.15,    # First + last name similarity
            'c4': 0.10,    # Pattern matching
            'c5': 0.10,    # Pattern matching
            'c6': 0.10,    # Pattern matching
            'c7': 0.10,    # Pattern matching
            'c8': 0.15,    # Nickname matching
            'c9': 0.10,    # Token similarity
            'c10': 0.05    # Domain similarity
        }
        
        weighted_score = sum(weights[key] * scores.get(key, 0) for key in weights)
        
        # Check pattern conditions
        pattern_match = c4 or c5 or c6 or c7
        
        # Determine if duplicates based on multiple criteria
        is_duplicate = (
            weighted_score >= self.threshold or
            (scores['c1'] >= self.threshold and scores['c2'] >= 0.6) or
            (scores['c3'] >= self.threshold and scores['c2'] >= 0.6) or
            (pattern_match and scores['c1'] >= 0.6) or
            (nickname_match and scores['c2'] >= 0.7) or
            (scores['c1'] >= 0.9) or  # Very high name similarity
            (scores['c2'] >= 0.9)     # Very high email similarity
        )
        
        return is_duplicate, self.similarity_results.copy()

    def _check_nickname_match(self, variants1: List[str], variants2: List[str]) -> bool:
        """
        Check if any nickname variants match between two records.
        
        Args:
            variants1: Name variants for first record
            variants2: Name variants for second record
            
        Returns:
            True if any variants match
        """
        if not variants1 or not variants2:
            return False
            
        return bool(set(variants1) & set(variants2))

    def _calculate_token_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate token-based similarity between two names.
        
        Args:
            name1: First name
            name2: Second name
            
        Returns:
            Token similarity score
        """
        if not name1 or not name2:
            return 0.0
            
        tokens1 = set(name1.lower().split())
        tokens2 = set(name2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0

    def _calculate_domain_similarity(self, email1: str, email2: str) -> float:
        """
        Calculate similarity between email domains.
        
        Args:
            email1: First email
            email2: Second email
            
        Returns:
            Domain similarity score
        """
        if not email1 or not email2 or '@' not in email1 or '@' not in email2:
            return 0.0
            
        domain1 = email1.split('@')[1].lower()
        domain2 = email2.split('@')[1].lower()
        
        return self._calculate_similarity(domain1, domain2, 'jaro_winkler')

    def find_duplicates_improved(self, developer_records: List[Dict]) -> List[Dict]:
        """
        Find all duplicate pairs using improved heuristic.
        
        Args:
            developer_records: List of developer records
            
        Returns:
            List of duplicate pairs with similarity details
        """
        duplicates = []
        total_pairs = len(developer_records) * (len(developer_records) - 1) // 2
        processed_pairs = 0
        
        self.logger.info(f"Checking {total_pairs} pairs for duplicates using improved heuristic")
        
        for i in range(len(developer_records)):
            for j in range(i + 1, len(developer_records)):
                record1 = developer_records[i]
                record2 = developer_records[j]
                
                is_duplicate, similarity_results = self.are_duplicates_improved(record1, record2)
                
                if is_duplicate:
                    duplicate_info = {
                        'record1': {
                            'original_name': record1['original_name'],
                            'original_email': record1['original_email'],
                            'normalized_name': record1['normalized_name'],
                            'email_prefix': record1['email_prefix']
                        },
                        'record2': {
                            'original_name': record2['original_name'],
                            'original_email': record2['original_email'],
                            'normalized_name': record2['normalized_name'],
                            'email_prefix': record2['email_prefix']
                        },
                        'similarity_results': similarity_results,
                        'matched_conditions': self._get_matched_conditions_improved(similarity_results)
                    }
                    duplicates.append(duplicate_info)
                
                processed_pairs += 1
                if processed_pairs % 1000 == 0:
                    self.logger.info(f"Processed {processed_pairs}/{total_pairs} pairs, found {len(duplicates)} duplicates")
        
        self.logger.info(f"Improved heuristic complete: found {len(duplicates)} duplicate pairs")
        return duplicates

    def _get_matched_conditions_improved(self, similarity_results: Dict) -> List[str]:
        """
        Get list of conditions that were matched in improved heuristic.
        
        Args:
            similarity_results: Dictionary of similarity results
            
        Returns:
            List of matched condition names
        """
        matched = []
        
        if similarity_results.get('c1', 0) >= self.threshold:
            matched.append('C1')
        if similarity_results.get('c2', 0) >= self.threshold:
            matched.append('C2')
        if (similarity_results.get('c3_first', 0) >= self.threshold and 
            similarity_results.get('c3_last', 0) >= self.threshold):
            matched.append('C3')
        if similarity_results.get('c4', False):
            matched.append('C4')
        if similarity_results.get('c5', False):
            matched.append('C5')
        if similarity_results.get('c6', False):
            matched.append('C6')
        if similarity_results.get('c7', False):
            matched.append('C7')
        if similarity_results.get('c8', False):
            matched.append('C8')
        if similarity_results.get('c9', 0) >= self.threshold:
            matched.append('C9')
        if similarity_results.get('c10', 0) >= 0.7:
            matched.append('C10')
            
        return matched
