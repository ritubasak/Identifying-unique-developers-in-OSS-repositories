import os
import csv
import pandas as pd
import shutil
import logging
from typing import List, Dict, Optional, Tuple
from pydriller import Repository
from DataClean import DataClean

class DataExtract(DataClean):
    """
    This class uses PyDriller to efficiently extract commit data from large repositories.
    """
    
    def __init__(self, repo_url: str, max_commits: Optional[int] = None):
        """
        Initialize the DataExtract class.
        
        Args:
            repo_url: URL of the repository to analyze
            max_commits: Maximum number of commits to process (None for all)
        """
        super().__init__()
        
        self.logger = logging.getLogger(__name__)
        self.repo_url = repo_url
        self.max_commits = max_commits
        
        # Project base directory
        self.__base_dir = os.path.dirname(os.path.abspath(__file__))
        self.__project_root = os.path.dirname(self.__base_dir)
        
        # Data folder paths
        self.__data_dir = os.path.join(self.__project_root, "data")
        self.__cloned_repo_dir = os.path.join(self.__data_dir, "cloned_repos")
        self.__raw_data_dir = os.path.join(self.__data_dir, "raw")
        self.__processed_data_dir = os.path.join(self.__data_dir, "processed")
        self.__output_dir = os.path.join(self.__project_root, "output")
        
        # Create directories if they don't exist
        for directory in [self.__data_dir, self.__cloned_repo_dir, 
                         self.__raw_data_dir, self.__processed_data_dir, self.__output_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Repository information
        self.repo_name = self._extract_repo_name(repo_url)
        self.repo_path = os.path.join(self.__cloned_repo_dir, self.repo_name)
        
        # Statistics
        self.stats = {
            'total_commits': 0,
            'total_contributors': 0,
            'valid_records': 0,
            'invalid_records': 0
        }

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        return os.path.basename(repo_url)

    def clone_repository(self) -> bool:
        """
        Clone the repository if it doesn't exist locally.
        
        Returns:
            True if repository is available, False otherwise
        """
        if os.path.exists(self.repo_path):
            self.logger.info(f"Repository already exists at {self.repo_path}")
            return True
            
        try:
            self.logger.info(f"Cloning repository from {self.repo_url}")
            from git import Repo
            Repo.clone_from(self.repo_url, self.repo_path)
            self.logger.info(f"Repository cloned successfully to {self.repo_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clone repository: {e}")
            return False

    def clean_repository(self) -> None:
        """Remove the cloned repository directory."""
        try:
            if os.path.exists(self.repo_path):
                shutil.rmtree(self.repo_path)
                self.logger.info(f"Repository {self.repo_path} removed")
        except Exception as e:
            self.logger.error(f"Failed to remove repository: {e}")

    def extract_developer_data(self) -> List[Dict]:
        """
        Extract developer data from the repository using PyDriller.
        
        Returns:
            List of developer records with preprocessed data
        """
        if not self.clone_repository():
            return []
            
        developer_records = []
        seen_combinations = set()
        
        self.logger.info(f"Extracting developer data from {self.repo_name}")
        
        try:
            commit_count = 0
            for commit in Repository(self.repo_path).traverse_commits():
                if self.max_commits and commit_count >= self.max_commits:
                    break

                commit_count += 1
                self.stats['total_commits'] = commit_count

                author_name = commit.author.name or ""
                author_email = commit.author.email or ""

                record_key = (author_name.lower().strip(), author_email.lower().strip())
                if record_key in seen_combinations:
                    continue
                seen_combinations.add(record_key)

                preprocessed = self.preprocess_developer_data(author_name, author_email)
                if preprocessed:
                    developer_records.append(preprocessed)
                    self.stats['valid_records'] += 1
                else:
                    self.stats['invalid_records'] += 1

                if commit_count % 1000 == 0:
                    self.logger.info(f"Processed {commit_count} commits, found {len(developer_records)} unique developers")

        except Exception as e:
            self.logger.error(f"Error during data extraction: {e}")
            return []
        
        self.stats['total_contributors'] = len(developer_records)
        self.logger.info(f"Extraction complete: {self.stats['total_commits']} commits, {self.stats['total_contributors']} unique developers")
        
        return developer_records

    def save_raw_data(self, developer_records: List[Dict]) -> str:
        """
        Save raw developer data to CSV file.
        
        Args:
            developer_records: List of developer records
            
        Returns:
            Path to the saved CSV file
        """
        raw_file = os.path.join(self.__raw_data_dir, f"{self.repo_name}_raw.csv")
        
        with open(raw_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['original_name', 'original_email', 'normalized_name', 
                         'first_name', 'last_name', 'email_prefix']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in developer_records:
                writer.writerow({
                    'original_name': record['original_name'],
                    'original_email': record['original_email'],
                    'normalized_name': record['normalized_name'],
                    'first_name': record['first_name'],
                    'last_name': record['last_name'],
                    'email_prefix': record['email_prefix']
                })
        
        self.logger.info(f"Raw data saved to {raw_file}")
        return raw_file

    def save_processed_data(self, developer_records: List[Dict]) -> str:
        """
        Save processed developer data to CSV file.
        
        Args:
            developer_records: List of developer records
            
        Returns:
            Path to the saved CSV file
        """
        processed_file = os.path.join(self.__processed_data_dir, f"{self.repo_name}_processed.csv")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(developer_records)
        
        # Remove duplicates based on normalized name and email prefix
        df_clean = df.drop_duplicates(subset=['normalized_name', 'email_prefix'])
        
        # Save to CSV
        df_clean.to_csv(processed_file, index=False)
        
        self.logger.info(f"Processed data saved to {processed_file}")
        return processed_file

    def get_repository_stats(self) -> Dict:
        """
        Get repository statistics.
        
        Returns:
            Dictionary with repository statistics
        """
        return {
            'repository_url': self.repo_url,
            'repository_name': self.repo_name,
            'total_commits': self.stats['total_commits'],
            'total_contributors': self.stats['total_contributors'],
            'valid_records': self.stats['valid_records'],
            'invalid_records': self.stats['invalid_records']
        }

    def run_extraction(self) -> Tuple[List[Dict], str, str]:
        """
        Run the complete extraction process.
        
        Returns:
            Tuple of (developer_records, raw_file_path, processed_file_path)
        """
        self.logger.info(f"Starting extraction for repository: {self.repo_url}")
        
        # Extract developer data
        developer_records = self.extract_developer_data()
        
        if not developer_records:
            self.logger.warning("No valid developer records found")
            return [], "", ""
        
        # Save data
        raw_file = self.save_raw_data(developer_records)
        processed_file = self.save_processed_data(developer_records)
        
        return developer_records, raw_file, processed_file
