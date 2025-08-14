"""
OpenReview API Client
====================

Client for interacting with the OpenReview API.
"""

import openreview
import openreview.tools
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Paper:
    """Represents a paper from OpenReview."""
    id: str
    title: str
    authors: List[str]
    abstract: str
    venue: str
    url: Optional[str] = None
    pdf_url: Optional[str] = None


@dataclass
class Profile:
    """Represents a user profile from OpenReview."""
    id: str
    emails: List[str]
    name: Optional[str]
    relations: List[Dict]
    publications: List[Paper]


class SingleBlindSubmissionError(Exception):
    """Exception raised when venue uses single-blind submission."""
    
    def __init__(self):
        self.message = "This venue uses single-blind submission. An attempt will be made to process as single-blind."
        super().__init__(self.message)


class OpenReviewClient:
    """Client for interacting with OpenReview API."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, 
                 base_url: str = "https://api2.openreview.net"):
        """Initialize OpenReview client."""
        self.base_url = base_url
        self.client = openreview.api.OpenReviewClient(
            baseurl=base_url,
            username=username,
            password=password
        )
    
    def find_user_by_email(self, email: str, with_publications: bool = True) -> Optional[Profile]:
        """Find a user profile by email address."""
        try:
            profiles = openreview.tools.get_profiles(
                self.client, 
                [email], 
                as_dict=True, 
                with_publications=with_publications
            )
            
            if not profiles:
                return None
            
            # Get the first (and typically only) profile
            profile_id = list(profiles.keys())[0]
            profile_data = profiles[profile_id]
            
            # Extract relations
            relations = []
            if 'relations' in profile_data.content:
                relations = profile_data.content['relations']
            
            # Extract publications
            publications = []
            if with_publications and 'publications' in profile_data.content:
                for pub in profile_data.content['publications']:
                    try:
                        paper = self._parse_publication(pub)
                        if paper:
                            publications.append(paper)
                    except Exception as e:
                        logger.warning(f"Failed to parse publication: {e}")
                        continue
            
            # Extract emails (profile ID is typically the primary email reference)
            emails = [email]
            
            return Profile(
                id=profile_id,
                emails=emails,
                name=profile_data.content.get('name', {}).get('value') if isinstance(profile_data.content.get('name'), dict) else profile_data.content.get('name'),
                relations=relations,
                publications=publications
            )
            
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None
    
    def get_user_papers(self, email: str) -> List[Paper]:
        """Get all papers by a user identified by email."""
        profile = self.find_user_by_email(email, with_publications=True)
        return profile.publications if profile else []
    
    def get_conference_papers(self, venue_id: str, year: Optional[str] = None) -> List[Paper]:
        """Get all papers from a specific conference venue and year."""
        try:
            # If year is provided, construct full venue ID
            if year:
                full_venue_id = f"{venue_id}/{year}/Conference"
            else:
                full_venue_id = venue_id
            
            # Determine API version
            api_v1 = self._is_api_v1(full_venue_id)
            
            # Get submissions
            submissions, accepted_submissions = self._get_submissions(full_venue_id, api_v1)
            
            papers = []
            for submission in accepted_submissions:
                try:
                    paper = self._parse_submission(submission, full_venue_id)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Failed to parse submission: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"Error getting conference papers for {venue_id}: {e}")
            return []
    
    def search_papers(self, query: str, papers: List[Paper], 
                     search_fields: List[str] = ['title', 'abstract', 'authors'],
                     match_mode: str = 'any') -> List[Dict]:
        """Search papers by keywords."""
        return self._search_submissions_dict(
            {p.id: self._paper_to_dict(p) for p in papers},
            query,
            search_fields,
            match_mode
        )
    
    def _is_api_v1(self, venue_id: str) -> bool:
        """Check if venue uses API v1 or v2."""
        try:
            venue_group = self.client.get_group(venue_id)
            return venue_group.domain is None
        except Exception:
            return True  # Default to v1 if uncertain
    
    def _get_submissions(self, venue_id: str, api_v1: bool = True):
        """Get submissions for a venue (adapted from notebook)."""
        if api_v1:
            logger.info("Using API V1 to get submissions")
            all_decision_notes = []
            accepted_submissions = []
            submissions = []
            
            try:
                # Try double-blind first
                submissions = self.client.get_all_notes(
                    invitation=f"{venue_id}/-/Blind_Submission", 
                    details='directReplies,original'
                )
                blind_notes = {note.id: note for note in submissions}
                for submission_id, submission in blind_notes.items():
                    all_decision_notes.extend([
                        reply for reply in submission.details["directReplies"] 
                        if reply["invitation"].endswith("Decision")
                    ])
                for decision_note in all_decision_notes:
                    if 'Accept' in decision_note["content"]['decision']:
                        accepted_submissions.append(blind_notes[decision_note['forum']].details['original'])
                        
                if len(accepted_submissions) == 0:
                    raise SingleBlindSubmissionError()
                    
            except (SingleBlindSubmissionError, Exception):
                # Try single-blind
                all_decision_notes = []
                accepted_submissions = []
                submissions = self.client.get_all_notes(
                    invitation=f'{venue_id}/-/Submission', 
                    details='directReplies'
                )
                notes = {note.id: note for note in submissions}
                for submission_id, submission in notes.items():
                    all_decision_notes.extend([
                        reply for reply in submission.details["directReplies"] 
                        if reply["invitation"].endswith("Decision")
                    ])
                for decision_note in all_decision_notes:
                    if 'Accept' in decision_note["content"]['decision']:
                        accepted_submissions.append(notes[decision_note['forum']])
        else:
            # API V2
            logger.info("Using API V2 to get submissions")
            venue_group = self.client.get_group(venue_id)
            submission_name = venue_group.content['submission_name']['value']
            submissions = self.client.get_all_notes(invitation=f'{venue_id}/-/{submission_name}')
            accepted_submissions = self.client.get_all_notes(content={'venueid': venue_id})
        
        return submissions, accepted_submissions
    
    def _parse_publication(self, publication) -> Optional[Paper]:
        """Parse a publication from user profile."""
        try:
            if not all(field in publication.content for field in ['title', 'authors', 'abstract']):
                return None
            
            # Handle different data formats
            venue = getattr(publication, 'invitation', publication.content.get('venueid', {}).get('value', 'Unknown'))
            
            title = self._extract_value(publication.content['title'])
            authors = self._extract_value(publication.content['authors'])
            abstract = self._extract_value(publication.content['abstract'])
            
            # Ensure authors is a list
            if isinstance(authors, str):
                authors = [authors]
            
            return Paper(
                id=publication.id,
                title=title,
                authors=authors,
                abstract=abstract,
                venue=venue,
                url=f"https://openreview.net/forum?id={publication.id}",
                pdf_url=f"https://openreview.net/pdf?id={publication.id}"
            )
        except Exception as e:
            logger.warning(f"Failed to parse publication: {e}")
            return None
    
    def _parse_submission(self, submission, venue_id: str) -> Optional[Paper]:
        """Parse a submission from conference."""
        try:
            if not all(field in submission.content for field in ['title', 'authors', 'abstract']):
                return None
            
            title = self._extract_value(submission.content['title'])
            authors = self._extract_value(submission.content['authors'])
            abstract = self._extract_value(submission.content['abstract'])
            
            # Ensure authors is a list
            if isinstance(authors, str):
                authors = [authors]
            
            return Paper(
                id=submission.id,
                title=title,
                authors=authors,
                abstract=abstract,
                venue=venue_id,
                url=f"https://openreview.net/forum?id={submission.id}",
                pdf_url=f"https://openreview.net/pdf?id={submission.id}"
            )
        except Exception as e:
            logger.warning(f"Failed to parse submission: {e}")
            return None
    
    def _extract_value(self, field):
        """Extract value from field that might be a dict or direct value."""
        if isinstance(field, dict):
            return field.get('value', field)
        return field
    
    def _paper_to_dict(self, paper: Paper) -> Dict:
        """Convert Paper object to dict format for search."""
        return {
            'title': paper.title,
            'authors': paper.authors,
            'abstract': paper.abstract,
            'venue': paper.venue
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching."""
        if not isinstance(text, str):
            return str(text).lower()
        return re.sub(r'[^\w\s]', ' ', text.lower())
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text."""
        normalized = self._normalize_text(text)
        return set(word.strip() for word in normalized.split() if len(word.strip()) > 2)
    
    def _search_submissions_dict(self, dict_submissions: Dict, keywords: Union[str, List[str]],
                                search_fields: List[str] = ['title', 'abstract', 'authors'],
                                match_mode: str = 'any', case_sensitive: bool = False) -> Dict:
        """Search through submissions (adapted from notebook search function)."""
        # Normalize keywords
        if isinstance(keywords, str):
            if match_mode == 'exact':
                search_terms = [keywords]
            else:
                search_terms = [kw.strip() for kw in keywords.split() if kw.strip()]
        else:
            search_terms = [str(kw).strip() for kw in keywords if str(kw).strip()]
        
        if not search_terms:
            return {}
        
        # Prepare search terms
        if not case_sensitive:
            search_terms = [term.lower() for term in search_terms]
        
        results = {}
        
        for submission_id, submission_data in dict_submissions.items():
            matches = defaultdict(list)
            found_terms = set()
            
            for field in search_fields:
                if field not in submission_data:
                    continue
                
                field_content = submission_data[field]
                
                # Handle authors field (could be a list)
                if field == 'authors' and isinstance(field_content, list):
                    field_text = ' '.join(str(author) for author in field_content)
                else:
                    field_text = str(field_content)
                
                # Prepare field text for searching
                search_text = field_text if case_sensitive else field_text.lower()
                
                # Search based on match mode
                if match_mode == 'exact':
                    # Exact phrase matching
                    for term in search_terms:
                        search_term = term if case_sensitive else term.lower()
                        if search_term in search_text:
                            matches[field].append(term)
                            found_terms.add(term)
                else:
                    # Word-based matching
                    field_words = self._extract_keywords(field_text)
                    if not case_sensitive:
                        field_words = {word.lower() for word in field_words}
                    
                    for term in search_terms:
                        search_term = term if case_sensitive else term.lower()
                        # Check for partial matches in words
                        for word in field_words:
                            if search_term in word or word in search_term:
                                matches[field].append(term)
                                found_terms.add(term)
                                break
            
            # Determine if submission matches based on match_mode
            is_match = False
            if match_mode == 'all':
                is_match = len(found_terms) == len(search_terms)
            elif match_mode in ['any', 'exact']:
                is_match = len(found_terms) > 0
            
            if is_match:
                results[submission_id] = {
                    **submission_data,
                    'matches': dict(matches),
                    'matched_terms': list(found_terms),
                    'match_score': len(found_terms) / len(search_terms)
                }
        
        return results