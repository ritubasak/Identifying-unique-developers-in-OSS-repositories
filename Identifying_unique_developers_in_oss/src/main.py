import argparse
import logging
import json
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from DataExtract import DataExtract
from DataCompare import DataCompare
from utils import setup_logging, generate_report, save_duplicates_csv

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Identify unique developers in open-source repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --repo https://github.com/numpy/numpy --threshold 0.85
  python main.py --repo https://github.com/torvalds/linux --threshold 0.8 --max-commits 5000
  python main.py --repo https://github.com/microsoft/vscode --threshold 0.9 --max-pairs 2000
        """
    )
    
    parser.add_argument(
        '--repo',
        required=True,
        help='GitHub repository URL to analyze'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.85,
        help='Similarity threshold for matching (0.0 to 1.0, default: 0.85)'
    )
    
    parser.add_argument(
        '--max-commits',
        type=int,
        help='Maximum number of commits to process (default: all)'
    )
    
    parser.add_argument(
        '--max-pairs',
        type=int,
        default=1000,
        help='Maximum number of candidate pairs to check (default: 1000)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory for results (default: output)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--clean-repo',
        action='store_true',
        help='Clean cloned repository after analysis'
    )
    
    parser.add_argument(
        '--skip-extraction',
        action='store_true',
        help='Skip data extraction and use existing processed data'
    )
    
    return parser.parse_args()

def validate_repository_url(repo_url: str) -> bool:
    """Validate that the repository URL is a valid GitHub URL."""
    return (repo_url.startswith('https://github.com/') or 
            repo_url.startswith('http://github.com/'))

def run_analysis(args) -> Dict:
    """Run the complete analysis pipeline."""
    logger = logging.getLogger(__name__)
    
    # Validate repository URL
    if not validate_repository_url(args.repo):
        logger.error(f"Invalid repository URL: {args.repo}")
        logger.error("Please provide a valid GitHub repository URL")
        sys.exit(1)
    
    # Validate threshold
    if not 0.0 <= args.threshold <= 1.0:
        logger.error(f"Invalid threshold: {args.threshold}")
        logger.error("Threshold must be between 0.0 and 1.0")
        sys.exit(1)
    
    logger.info(f"Starting analysis for repository: {args.repo}")
    logger.info(f"Threshold: {args.threshold}")
    logger.info(f"Max commits: {args.max_commits or 'all'}")
    logger.info(f"Max pairs: {args.max_pairs}")
    
    # Initialize data extractor
    extractor = DataExtract(args.repo, args.max_commits)
    
    # Extract developer data
    if args.skip_extraction:
        logger.info("Skipping data extraction, using existing data")
        processed_file = os.path.join(extractor._DataExtract__processed_data_dir, 
                                    f"{extractor.repo_name}_processed.csv")
        if not os.path.exists(processed_file):
            logger.error(f"Processed data file not found: {processed_file}")
            sys.exit(1)
        
        df = pd.read_csv(processed_file)
        developer_records = df.to_dict('records')
    else:
        logger.info("Extracting developer data from repository")
        developer_records, _, processed_file = extractor.run_extraction()
        
        if not developer_records:
            logger.error("No valid developer records found")
            sys.exit(1)
    
    logger.info(f"Found {len(developer_records)} unique developer records")
    
    # Limit pairs for analysis if specified
    if len(developer_records) > args.max_pairs:
        logger.warning(f"Limiting analysis to first {args.max_pairs} records")
        developer_records = developer_records[:args.max_pairs]
    
    # Initialize data comparer
    comparer = DataCompare(args.threshold)
    
    # Run Bird heuristic
    logger.info("Running Bird et al. heuristic")
    bird_duplicates = comparer.find_duplicates_bird(developer_records)
    
    # Run improved heuristic
    logger.info("Running improved heuristic")
    improved_duplicates = comparer.find_duplicates_improved(developer_records)
    
    # Generate results
    results = {
        'repository_info': extractor.get_repository_stats(),
        'analysis_parameters': {
            'threshold': args.threshold,
            'max_commits': args.max_commits,
            'max_pairs': args.max_pairs,
            'total_records': len(developer_records)
        },
        'bird_results': {
            'total_duplicates': len(bird_duplicates),
            'duplicates': bird_duplicates
        },
        'improved_results': {
            'total_duplicates': len(improved_duplicates),
            'duplicates': improved_duplicates
        },
        'comparison': {
            'bird_only': len([d for d in bird_duplicates if d not in improved_duplicates]),
            'improved_only': len([d for d in improved_duplicates if d not in bird_duplicates]),
            'common': len([d for d in bird_duplicates if d in improved_duplicates])
        }
    }
    
    # Save results
    save_results(results, args.output_dir, extractor.repo_name)
    
    # Clean up repository if requested
    if args.clean_repo:
        logger.info("Cleaning up cloned repository")
        extractor.clean_repository()
    
    return results

def save_results(results: Dict, output_dir: str, repo_name: str):
    """Save analysis results to files."""
    logger = logging.getLogger(__name__)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save Bird duplicates
    bird_file = os.path.join(output_dir, f"{repo_name}_bird_duplicates.csv")
    save_duplicates_csv(results['bird_results']['duplicates'], bird_file)
    logger.info(f"Bird duplicates saved to {bird_file}")
    
    # Save improved duplicates
    improved_file = os.path.join(output_dir, f"{repo_name}_improved_duplicates.csv")
    save_duplicates_csv(results['improved_results']['duplicates'], improved_file)
    logger.info(f"Improved duplicates saved to {improved_file}")
    
    # Save summary JSON
    summary_file = os.path.join(output_dir, f"{repo_name}_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Summary saved to {summary_file}")
    
    # Generate and save report
    report_file = os.path.join(output_dir, f"{repo_name}_report.md")
    generate_report(results, report_file)
    logger.info(f"Report saved to {report_file}")

def main():
    """Main function."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Run analysis
        results = run_analysis(args)
        
        # Print summary
        print("\n" + "="*60)
        print("ANALYSIS SUMMARY")
        print("="*60)
        print(f"Repository: {results['repository_info']['repository_name']}")
        print(f"Total commits: {results['repository_info']['total_commits']}")
        print(f"Total contributors: {results['repository_info']['total_contributors']}")
        print(f"Threshold: {results['analysis_parameters']['threshold']}")
        print(f"Records analyzed: {results['analysis_parameters']['total_records']}")
        print()
        print("DUPLICATE DETECTION RESULTS:")
        print(f"Bird heuristic duplicates: {results['bird_results']['total_duplicates']}")
        print(f"Improved heuristic duplicates: {results['improved_results']['total_duplicates']}")
        print()
        print("COMPARISON:")
        print(f"Common duplicates: {results['comparison']['common']}")
        print(f"Bird only: {results['comparison']['bird_only']}")
        print(f"Improved only: {results['comparison']['improved_only']}")
        print("="*60)
        
        logger.info("Analysis completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()