# ==============================================================================
# FILE: utils/subject_normalizer.py
# ==============================================================================
"""
Subject name normalization utility.
Handles variations in subject names across the dataset.
"""

import polars as pl
import re
from difflib import SequenceMatcher


class SubjectNormalizer:
    """Normalize subject names by handling common variations."""
    
    def __init__(self):
        # Common abbreviations and their full forms
        self.abbreviations = {
            'MGMT': 'MANAGEMENT',
            'MNGMT': 'MANAGEMENT',
            'COMM': 'COMMUNICATION',
            'TECH': 'TECHNOLOGY',
            'SYS': 'SYSTEMS',
            'PROG': 'PROGRAMMING',
            'COMP': 'COMPUTER',
            'INFO': 'INFORMATION',
            'ACCT': 'ACCOUNTING',
            'ECON': 'ECONOMICS',
            'BUS': 'BUSINESS',
            'ADMIN': 'ADMINISTRATION',
            'ORG': 'ORGANIZATIONAL',
            'HR': 'HUMAN RESOURCE',
            'HRM': 'HUMAN RESOURCE MANAGEMENT',
            'OB': 'ORGANIZATIONAL BEHAVIOUR',
            'STATS': 'STATISTICS',
            'MKTG': 'MARKETING',
            'FIN': 'FINANCE',
            'ACC': 'ACCOUNTING',
            'ADV': 'ADVANCED',
            'INTRO': 'INTRODUCTION',
            'FUND': 'FUNDAMENTALS',
            'PRIN': 'PRINCIPLES',
            'INTL': 'INTERNATIONAL',
            'CORP': 'CORPORATE',
            'IND': 'INDUSTRIAL',
            'ENV': 'ENVIRONMENTAL',
            'LAB': 'LABORATORY',
        }
        
        # Known subject mappings (add more as needed)
        self.subject_mappings = {
            '.NET': 'DOT NET TECHNOLOGY',
            'DOT NET': 'DOT NET TECHNOLOGY',
            '.NET TECHNOLOGY': 'DOT NET TECHNOLOGY',
            '.NET TECHNOLOGIES': 'DOT NET TECHNOLOGY',
            'NET TECHNOLOGIES': 'DOT NET TECHNOLOGY',
            '.NET LAB': 'DOT NET TECHNOLOGY',
            
            'DATA STRUCTURE': 'DATA STRUCTURES',
            'DATA STRUCTURES AND ALGORITHMS': 'DATA STRUCTURES',
            'DS': 'DATA STRUCTURES',
            
            'DATABASE': 'DATABASE MANAGEMENT SYSTEM',
            'DBMS': 'DATABASE MANAGEMENT SYSTEM',
            'DATABASE MANAGEMENT': 'DATABASE MANAGEMENT SYSTEM',
            'DATABASE SYSTEMS': 'DATABASE MANAGEMENT SYSTEM',
            
            'OPERATING SYSTEM': 'OPERATING SYSTEMS',
            'OS': 'OPERATING SYSTEMS',
            
            'COMPUTER NETWORK': 'COMPUTER NETWORKS',
            'COMPUTER NETWORKING': 'COMPUTER NETWORKS',
            'NETWORKS': 'COMPUTER NETWORKS',
            
            'OOP': 'OBJECT ORIENTED PROGRAMMING',
            'OOPS': 'OBJECT ORIENTED PROGRAMMING',
            'OBJECT ORIENTED PROGRAMMING CONCEPTS': 'OBJECT ORIENTED PROGRAMMING',
            
            'AI': 'ARTIFICIAL INTELLIGENCE',
            'ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING': 'ARTIFICIAL INTELLIGENCE',
            
            'ML': 'MACHINE LEARNING',
            'MACHINE LEARNING AND AI': 'MACHINE LEARNING',
            
            'WEB TECH': 'WEB TECHNOLOGY',
            'WEB TECHNOLOGIES': 'WEB TECHNOLOGY',
            'WEB PROGRAMMING': 'WEB TECHNOLOGY',
            
            'SOFT SKILL': 'SOFT SKILLS',
            'SOFT SKILLS DEVELOPMENT': 'SOFT SKILLS',
            'COMMUNICATION SKILLS': 'SOFT SKILLS',
            
            'BUSINESS COMM': 'BUSINESS COMMUNICATION',
            'BUSINESS COMMUNICATIONS': 'BUSINESS COMMUNICATION',
            
            'FINANCIAL MANAGEMENT': 'FINANCE',
            'FINANCIAL MGMT': 'FINANCE',
            'CORPORATE FINANCE': 'FINANCE',
            
            'MARKETING MANAGEMENT': 'MARKETING',
            'PRINCIPLES OF MARKETING': 'MARKETING',
            
            'HUMAN RESOURCE': 'HUMAN RESOURCE MANAGEMENT',
            'HR MANAGEMENT': 'HUMAN RESOURCE MANAGEMENT',
            'HRM': 'HUMAN RESOURCE MANAGEMENT',
        }
    
    def normalize_single(self, subject_name):
        """Normalize a single subject name."""
        if not subject_name or pd.isna(subject_name):
            return subject_name
        
        # Convert to string and uppercase
        normalized = str(subject_name).upper().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove leading/trailing special characters
        normalized = re.sub(r'^[\.\-\s]+|[\.\-\s]+$', '', normalized)
        
        # Handle special characters with spaces
        normalized = re.sub(r'([\.\-/])\s+', r'\1', normalized)
        normalized = re.sub(r'\s+([\.\-/])', r'\1', normalized)
        
        # Check direct mappings first
        if normalized in self.subject_mappings:
            return self.subject_mappings[normalized]
        
        # Replace common abbreviations
        words = normalized.split()
        replaced_words = [self.abbreviations.get(w, w) for w in words]
        normalized = ' '.join(replaced_words)
        
        # Check mappings again after abbreviation replacement
        if normalized in self.subject_mappings:
            return self.subject_mappings[normalized]
        
        return normalized
    
    def normalize_dataframe(self, df, subject_column='subject'):
        """Normalize subject names in a Polars DataFrame."""
        # Apply normalization
        df = df.with_columns(
            pl.col(subject_column)
            .map_elements(self.normalize_single, return_dtype=pl.Utf8)
            .alias(subject_column + '_normalized')
        )
        
        return df
    
    def find_similar_subjects(self, df, subject_column='subject_normalized', threshold=0.85):
        """
        Find similar subject names that might be duplicates.
        Returns a dictionary mapping similar subjects to a canonical name.
        """
        subjects = df[subject_column].unique().to_list()
        subject_groups = {}
        
        for i, subj1 in enumerate(subjects):
            if not subj1:
                continue
            
            # Skip if already grouped
            if any(subj1 in group for group in subject_groups.values()):
                continue
            
            similar = [subj1]
            
            for subj2 in subjects[i+1:]:
                if not subj2:
                    continue
                
                # Calculate similarity
                ratio = SequenceMatcher(None, subj1, subj2).ratio()
                
                if ratio >= threshold:
                    similar.append(subj2)
            
            if len(similar) > 1:
                # Use the shortest name as canonical
                canonical = min(similar, key=len)
                subject_groups[canonical] = similar
        
        return subject_groups
    
    def apply_similarity_mapping(self, df, subject_column='subject_normalized'):
        """Apply similarity-based subject grouping."""
        # Find similar subjects
        groups = self.find_similar_subjects(df, subject_column)
        
        # Create reverse mapping
        mapping = {}
        for canonical, similar_list in groups.items():
            for similar in similar_list:
                mapping[similar] = canonical
        
        # Apply mapping
        if mapping:
            df = df.with_columns(
                pl.col(subject_column)
                .map_elements(lambda x: mapping.get(x, x), return_dtype=pl.Utf8)
                .alias(subject_column + '_final')
            )
        else:
            df = df.with_columns(
                pl.col(subject_column).alias(subject_column + '_final')
            )
        
        return df, mapping


def normalize_subjects(df, subject_column='subject'):
    """
    Main function to normalize subjects in a DataFrame.
    
    Args:
        df: Polars DataFrame
        subject_column: Name of the column containing subject names
    
    Returns:
        Normalized DataFrame with additional columns:
        - subject_normalized: After basic normalization
        - subject_final: After similarity grouping
    """
    normalizer = SubjectNormalizer()
    
    # Step 1: Basic normalization
    df = normalizer.normalize_dataframe(df, subject_column)
    
    # Step 2: Similarity-based grouping
    df, mapping = normalizer.apply_similarity_mapping(df, subject_column + '_normalized')
    
    print(f"\n{'='*60}")
    print("SUBJECT NORMALIZATION REPORT")
    print(f"{'='*60}")
    print(f"Original unique subjects: {df[subject_column].n_unique()}")
    print(f"After normalization: {df[subject_column + '_normalized'].n_unique()}")
    print(f"After similarity grouping: {df[subject_column + '_final'].n_unique()}")
    
    if mapping:
        print(f"\nSimilar subjects grouped: {len(mapping)}")
        print("\nSample groupings:")
        for i, (canonical, similar) in enumerate(list(mapping.items())[:5]):
            print(f"  {canonical} ← {similar}")
    
    print(f"{'='*60}\n")
    
    return df


# Example usage
if __name__ == '__main__':
    import polars as pl
    from data.loader import load_data
    
    # Load data
    df = load_data()
    
    # Normalize subjects
    df = normalize_subjects(df, 'subject')
    
    # Show some examples
    print("\nSample normalized subjects:")
    print(df.select(['subject', 'subject_normalized', 'subject_final']).head(10))