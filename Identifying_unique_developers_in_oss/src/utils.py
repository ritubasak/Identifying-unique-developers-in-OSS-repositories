import logging
import csv
import os
from datetime import datetime
from typing import Dict, List, Any
import json

def setup_logging(level: str = 'INFO') -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/deduplication_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )

def save_duplicates_csv(duplicates: List[Dict], filename: str) -> None:
    """
    Save duplicate pairs to CSV file.
    
    Args:
        duplicates: List of duplicate pairs
        filename: Output CSV filename
    """
    if not duplicates:
        # Create empty CSV with headers
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'record1_name', 'record1_email', 'record1_normalized', 'record1_prefix',
                'record2_name', 'record2_email', 'record2_normalized', 'record2_prefix',
                'matched_conditions', 'similarity_scores'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        return
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'record1_name', 'record1_email', 'record1_normalized', 'record1_prefix',
            'record2_name', 'record2_email', 'record2_normalized', 'record2_prefix',
            'matched_conditions', 'similarity_scores'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for duplicate in duplicates:
            record1 = duplicate['record1']
            record2 = duplicate['record2']
            similarity_results = duplicate['similarity_results']
            matched_conditions = ', '.join(duplicate['matched_conditions'])
            
            # Format similarity scores as JSON string
            similarity_scores = json.dumps(similarity_results, indent=2)
            
            writer.writerow({
                'record1_name': record1['original_name'],
                'record1_email': record1['original_email'],
                'record1_normalized': record1['normalized_name'],
                'record1_prefix': record1['email_prefix'],
                'record2_name': record2['original_name'],
                'record2_email': record2['original_email'],
                'record2_normalized': record2['normalized_name'],
                'record2_prefix': record2['email_prefix'],
                'matched_conditions': matched_conditions,
                'similarity_scores': similarity_scores
            })

def generate_report(results: Dict, filename: str) -> None:
    """
    Generate a comprehensive Markdown report.
    
    Args:
        results: Analysis results dictionary
        filename: Output report filename
    """
    repo_info = results['repository_info']
    analysis_params = results['analysis_parameters']
    bird_results = results['bird_results']
    improved_results = results['improved_results']
    comparison = results['comparison']
    
    report = f"""# Developer Deduplication Analysis Report

## Repository Information

- **Repository**: {repo_info['repository_name']}
- **URL**: {repo_info['repository_url']}
- **Total Commits**: {repo_info['total_commits']:,}
- **Total Contributors**: {repo_info['total_contributors']:,}
- **Valid Records**: {repo_info['valid_records']:,}
- **Invalid Records**: {repo_info['invalid_records']:,}

## Analysis Parameters

- **Similarity Threshold**: {analysis_params['threshold']}
- **Max Commits Processed**: {analysis_params['max_commits'] or 'All'}
- **Max Pairs Analyzed**: {analysis_params['max_pairs']:,}
- **Records Analyzed**: {analysis_params['total_records']:,}

## Results Summary

### Bird et al. Heuristic
- **Total Duplicates Found**: {bird_results['total_duplicates']:,}

### Improved Heuristic
- **Total Duplicates Found**: {improved_results['total_duplicates']:,}

### Comparison
- **Common Duplicates**: {comparison['common']:,}
- **Bird Only**: {comparison['bird_only']:,}
- **Improved Only**: {comparison['improved_only']:,}

## Method Comparison

| Metric | Bird Heuristic | Improved Heuristic | Difference |
|--------|----------------|-------------------|------------|
| Total Duplicates | {bird_results['total_duplicates']:,} | {improved_results['total_duplicates']:,} | {improved_results['total_duplicates'] - bird_results['total_duplicates']:+,} |
| Precision* | TBD | TBD | TBD |
| Recall* | TBD | TBD | TBD |

*Precision and Recall require manual validation of True Positives and False Positives

## Analysis Details

### Bird et al. Heuristic Conditions
The Bird heuristic checks seven conditions (C1-C7):
1. **C1**: Full name similarity ≥ threshold
2. **C2**: Email prefix similarity ≥ threshold  
3. **C3**: Both first name AND last name similarity ≥ threshold
4. **C4**: Email prefix contains first initial + last name
5. **C5**: Email prefix contains last initial + first name
6. **C6**: Email prefix1 contains first initial + last name
7. **C7**: Email prefix1 contains last initial + first name

### Improved Heuristic Enhancements
The improved heuristic adds:
- **C8**: Nickname matching (Bob ↔ Robert, Bill ↔ William)
- **C9**: Token-based similarity
- **C10**: Email domain similarity
- **Weighted scoring**: Combines multiple similarity measures
- **Jaro-Winkler similarity**: More robust than Levenshtein for names
- **Multiple thresholds**: Different criteria for different conditions

## Common False Positive Causes

1. **Reordered Names**: "John Smith" vs "Smith John"
2. **Nicknames**: "Bob" vs "Robert", "Bill" vs "William"
3. **Email Variations**: "john.smith@email.com" vs "johnsmith@email.com"
4. **Malformed Configurations**: Incomplete or corrupted git config
5. **Different Email Domains**: Same person using different email providers
6. **Name Variations**: "José" vs "Jose", "O'Connor" vs "OConnor"

## Recommendations

1. **Manual Review**: Validate a sample of detected duplicates
2. **Threshold Tuning**: Adjust threshold based on precision/recall requirements
3. **Domain Knowledge**: Use project-specific rules for common patterns
4. **Iterative Improvement**: Refine heuristics based on validation results

## Files Generated

- `{repo_info['repository_name']}_bird_duplicates.csv`: Bird heuristic results
- `{repo_info['repository_name']}_improved_duplicates.csv`: Improved heuristic results
- `{repo_info['repository_name']}_summary.json`: Complete analysis data
- `{repo_info['repository_name']}_report.md`: This report

## Technical Details

- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Python Version**: {os.sys.version}
- **Dependencies**: See requirements.txt

---

*This report was generated automatically by the Developer Deduplication Analysis Tool.*
"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

def calculate_precision_recall(duplicates: List[Dict], true_positives: int, false_positives: int) -> Dict[str, float]:
    """
    Calculate precision and recall metrics.
    
    Args:
        duplicates: List of detected duplicates
        true_positives: Number of true positive matches
        false_positives: Number of false positive matches
        
    Returns:
        Dictionary with precision and recall scores
    """
    total_detected = len(duplicates)
    
    if total_detected == 0:
        return {'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0}
    
    precision = true_positives / total_detected if total_detected > 0 else 0.0
    recall = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score
    }

def _get_email_domain(email: str) -> str:
    """Extract domain from an email address, or empty string if invalid."""
    if not email or '@' not in email:
        return ''
    parts = email.split('@', 1)
    return parts[1] if len(parts) == 2 else ''


def _char_jaccard_similarity(text1: str, text2: str) -> float:
    """Compute simple Jaccard similarity over character sets for two strings."""
    if not text1 or not text2:
        return 0.0
    set1 = set(text1.lower())
    set2 = set(text2.lower())
    union = set1 | set2
    if not union:
        return 0.0
    return len(set1 & set2) / len(union)


def validate_duplicate_pair(record1: Dict, record2: Dict) -> Dict[str, Any]:
    """
    Validate a duplicate pair for manual review.
    
    Args:
        record1: First developer record
        record2: Second developer record
        
    Returns:
        Dictionary with validation information
    """
    validation = {
        'is_likely_duplicate': False,
        'confidence': 0.0,
        'evidence': [],
        'warnings': []
    }
    
    # Check name similarity
    name_similarity = _char_jaccard_similarity(
        record1.get('normalized_name', ''),
        record2.get('normalized_name', '')
    )
    if name_similarity > 0.7:
        validation['evidence'].append(f"High name similarity: {name_similarity:.2f}")
        validation['confidence'] += 0.3

    # Check email similarity (domain match)
    domain1 = _get_email_domain(record1.get('original_email', ''))
    domain2 = _get_email_domain(record2.get('original_email', ''))
    if domain1 and domain2 and domain1 == domain2:
        validation['evidence'].append(f"Same email domain: {domain1}")
        validation['confidence'] += 0.2

    # Check for common patterns (identical prefixes)
    prefix1 = record1.get('email_prefix', '')
    prefix2 = record2.get('email_prefix', '')
    if prefix1 and prefix2 and prefix1 == prefix2:
        validation['evidence'].append("Identical email prefixes")
        validation['confidence'] += 0.4
    
    # Determine if likely duplicate
    validation['is_likely_duplicate'] = validation['confidence'] > 0.5
    
    return validation
