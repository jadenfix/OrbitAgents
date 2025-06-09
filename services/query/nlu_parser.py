"""
Advanced NLU Parser for real estate queries using spaCy and regex patterns.
Handles comprehensive edge cases and provides confidence scoring.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

# Import spaCy with error handling
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available. Using regex-only parsing.")

from schemas import ParsedQuery, PropertyType

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Container for extraction results with confidence."""
    value: Any
    confidence: float
    source: str  # 'spacy', 'regex', 'heuristic'


class NLUParser:
    """Advanced NLU parser for real estate queries with comprehensive edge case handling."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize the NLU parser with spaCy model and regex patterns."""
        self.nlp = None
        
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(f"Failed to load spaCy model: {model_name}, using fallback")
                try:
                    self.nlp = spacy.blank("en")
                except:
                    logger.error("Failed to create blank spaCy model")
                    self.nlp = None
        
        self._compile_patterns()
        self._load_dictionaries()
    
    def _compile_patterns(self):
        """Compile all regex patterns for various extractions."""
        
        # Bedroom patterns with comprehensive edge cases
        self.bedroom_patterns = [
            # Exact matches
            (r'\b(\d+)\s*(?:bed(?:room)?s?|bdr?s?|br)\b', 1.0),
            (r'\b(?:bed(?:room)?s?|bdr?s?|br)\s*[:=]?\s*(\d+)\b', 0.9),
            
            # Range patterns
            (r'\b(\d+)\s*[-–to]\s*(\d+)\s*(?:bed(?:room)?s?|bdr?s?|br)\b', 0.85),
            (r'\b(?:bed(?:room)?s?|bdr?s?|br)\s*[:=]?\s*(\d+)\s*[-–to]\s*(\d+)\b', 0.8),
            
            # Minimum patterns
            (r'\b(\d+)\+\s*(?:bed(?:room)?s?|bdr?s?|br)\b', 0.9),
            (r'\b(?:at least|minimum|min)\s*(\d+)\s*(?:bed(?:room)?s?|bdr?s?|br)\b', 0.85),
            (r'\b(\d+)\s*or more\s*(?:bed(?:room)?s?|bdr?s?|br)\b', 0.8),
            
            # Maximum patterns  
            (r'\b(?:maximum|max|up to)\s*(\d+)\s*(?:bed(?:room)?s?|bdr?s?|br)\b', 0.85),
            (r'\b(?:no more than)\s*(\d+)\s*(?:bed(?:room)?s?|bdr?s?|br)\b', 0.8),
            
            # Studio patterns
            (r'\b(?:studio|efficiency)\b', 0.95),  # Special case for 0 bedrooms
        ]
        
        # Bathroom patterns
        self.bathroom_patterns = [
            # Exact matches with decimal support
            (r'\b(\d+(?:\.\d+)?)\s*(?:bath(?:room)?s?|ba)\b', 1.0),
            (r'\b(?:bath(?:room)?s?|ba)\s*[:=]?\s*(\d+(?:\.\d+)?)\b', 0.9),
            
            # Range patterns
            (r'\b(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)\s*(?:bath(?:room)?s?|ba)\b', 0.85),
            
            # Minimum/Maximum patterns
            (r'\b(\d+(?:\.\d+)?)\+\s*(?:bath(?:room)?s?|ba)\b', 0.9),
            (r'\b(?:at least|minimum|min)\s*(\d+(?:\.\d+)?)\s*(?:bath(?:room)?s?|ba)\b', 0.85),
        ]
        
        # Price patterns with comprehensive currency and formatting support
        self.price_patterns = [
            # Standard currency formats
            (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b', 1.0),
            (r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?\b', 0.9),
            
            # Maximum price patterns
            (r'\b(?:under|below|less than|max|maximum|up to)\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b', 0.95),
            (r'\b(?:under|below|less than|max|maximum|up to)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?\b', 0.9),
            
            # Minimum price patterns
            (r'\b(?:over|above|more than|at least|minimum|min)\s*\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b', 0.9),
            
            # Range patterns
            (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*[-–to]\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b', 0.85),
            
            # Abbreviated formats (k, K for thousands)
            (r'\$\s*(\d+(?:\.\d+)?)\s*k\b', 0.8),  # $2.5k
            (r'\b(\d+(?:\.\d+)?)\s*k\s*dollars?\b', 0.75),
        ]
        
        # Property type patterns
        self.property_type_patterns = {
            PropertyType.APARTMENT: [
                r'\b(?:apartment|apt|unit)\b',
                r'\b(?:flat|loft)\b',
            ],
            PropertyType.HOUSE: [
                r'\b(?:house|home|single family|detached)\b',
                r'\b(?:sfh|single-family)\b',
            ],
            PropertyType.CONDO: [
                r'\b(?:condo|condominium|townhome)\b',
                r'\b(?:co-op|cooperative)\b',
            ],
            PropertyType.TOWNHOUSE: [
                r'\b(?:townhouse|townhome|row house)\b',
                r'\b(?:duplex|triplex)\b',
            ],
            PropertyType.STUDIO: [
                r'\b(?:studio|efficiency|bachelor)\b',
            ],
        }
        
        # Amenity patterns
        self.amenity_patterns = {
            'parking': [
                r'\b(?:parking|garage|carport)\b',
                r'\b(?:car space|vehicle)\b',
            ],
            'pets': [
                r'\b(?:pet|dog|cat|animal)[-\s]?(?:friendly|allowed|ok|welcome)\b',
                r'\b(?:pets?\s*(?:ok|allowed|welcome))\b',
            ],
            'furnished': [
                r'\b(?:furnished|furniture included)\b',
                r'\b(?:unfurnished|no furniture)\b',
            ],
        }
        
        # Compile all patterns
        self._compiled_patterns = {}
        for pattern_name in ['bedroom_patterns', 'bathroom_patterns', 'price_patterns']:
            patterns = getattr(self, pattern_name)
            self._compiled_patterns[pattern_name] = [
                (re.compile(pattern, re.IGNORECASE), confidence) 
                for pattern, confidence in patterns
            ]
        
        # Compile property type patterns
        self._compiled_property_types = {}
        for prop_type, patterns in self.property_type_patterns.items():
            self._compiled_property_types[prop_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Compile amenity patterns
        self._compiled_amenities = {}
        for amenity, patterns in self.amenity_patterns.items():
            self._compiled_amenities[amenity] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def _load_dictionaries(self):
        """Load dictionaries for cities, neighborhoods, and keywords."""
        
        # Major US cities (expandable)
        self.major_cities = {
            'san francisco', 'san jose', 'oakland', 'berkeley', 'palo alto',
            'los angeles', 'san diego', 'sacramento', 'fresno',
            'new york', 'brooklyn', 'manhattan', 'queens', 'bronx',
            'chicago', 'boston', 'philadelphia', 'washington dc', 'dc',
            'seattle', 'portland', 'denver', 'austin', 'dallas', 'houston',
            'miami', 'atlanta', 'nashville', 'charlotte', 'raleigh',
            'phoenix', 'tucson', 'las vegas', 'salt lake city',
        }
        
        # Common neighborhood indicators
        self.neighborhood_indicators = {
            'downtown', 'uptown', 'midtown', 'north', 'south', 'east', 'west',
            'central', 'old town', 'new town', 'historic', 'district',
            'heights', 'hills', 'park', 'beach', 'bay', 'marina',
            'mission', 'castro', 'haight', 'richmond', 'sunset',
            'soma', 'nob hill', 'russian hill', 'pacific heights',
        }
        
        # Property keywords
        self.property_keywords = {
            'luxury', 'modern', 'updated', 'renovated', 'new', 'historic',
            'spacious', 'cozy', 'bright', 'quiet', 'convenient', 'walkable',
            'transit', 'transportation', 'shopping', 'dining', 'restaurants',
            'schools', 'parks', 'gym', 'fitness', 'pool', 'spa', 'balcony',
            'patio', 'garden', 'yard', 'view', 'bay view', 'city view',
            'washer', 'dryer', 'dishwasher', 'air conditioning', 'heating',
            'hardwood', 'carpet', 'tile', 'granite', 'marble', 'stainless',
        }
    
    def parse_query(self, query: str) -> ParsedQuery:
        """Parse a natural language query into structured data."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Normalize query
        normalized_query = self._normalize_query(query)
        
        # Process with spaCy for entity recognition if available
        doc = None
        if self.nlp:
            try:
                doc = self.nlp(normalized_query)
            except Exception as e:
                logger.warning(f"spaCy processing failed: {e}")
        
        # Extract all components
        results = {
            'beds': self._extract_bedrooms(normalized_query, doc),
            'baths': self._extract_bathrooms(normalized_query, doc),
            'price': self._extract_price(normalized_query, doc),
            'city': self._extract_city(normalized_query, doc),
            'neighborhoods': self._extract_neighborhoods(normalized_query, doc),
            'property_type': self._extract_property_type(normalized_query, doc),
            'amenities': self._extract_amenities(normalized_query, doc),
            'keywords': self._extract_keywords(normalized_query, doc),
        }
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(results, normalized_query)
        
        # Build ParsedQuery object
        parsed = self._build_parsed_query(results, confidence)
        
        logger.info(f"Parsed query '{query}' with confidence {confidence:.2f}")
        return parsed
    
    def _normalize_query(self, query: str) -> str:
        """Normalize the query for better parsing."""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Normalize common abbreviations
        replacements = {
            r'\bbr\b': 'bedroom',
            r'\bba\b': 'bathroom',
            r'\bbdr\b': 'bedroom',
            r'\bbdrm\b': 'bedroom',
            r'\bbth\b': 'bathroom',
            r'\bsf\b': 'san francisco',
            r'\bla\b': 'los angeles',
            r'\bnyc\b': 'new york',
            r'\bdc\b': 'washington dc',
        }
        
        for pattern, replacement in replacements.items():
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        
        return query
    
    def _extract_bedrooms(self, query: str, doc) -> Optional[ExtractionResult]:
        """Extract bedroom information from query."""
        best_result = None
        best_confidence = 0.0
        
        # Handle studio special case
        if re.search(r'\b(?:studio|efficiency)\b', query, re.IGNORECASE):
            return ExtractionResult(
                value={'beds': 0, 'beds_min': 0, 'beds_max': 0},
                confidence=0.95,
                source='regex'
            )
        
        # Try regex patterns
        for pattern, confidence in self._compiled_patterns['bedroom_patterns']:
            matches = pattern.findall(query)
            if matches:
                result = self._process_bedroom_matches(matches, confidence)
                if result and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
        
        return best_result
    
    def _extract_bathrooms(self, query: str, doc) -> Optional[ExtractionResult]:
        """Extract bathroom information from query."""
        best_result = None
        best_confidence = 0.0
        
        # Try regex patterns
        for pattern, confidence in self._compiled_patterns['bathroom_patterns']:
            matches = pattern.findall(query)
            if matches:
                result = self._process_bathroom_matches(matches, confidence)
                if result and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
        
        return best_result
    
    def _extract_price(self, query: str, doc) -> Optional[ExtractionResult]:
        """Extract price information from query."""
        best_result = None
        best_confidence = 0.0
        
        # Try regex patterns
        for pattern, confidence in self._compiled_patterns['price_patterns']:
            matches = pattern.findall(query)
            if matches:
                result = self._process_price_matches(matches, confidence, query, pattern)
                if result and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
        
        return best_result
    
    def _extract_city(self, query: str, doc) -> Optional[ExtractionResult]:
        """Extract city information from query."""
        best_result = None
        best_confidence = 0.0
        
        # Check for exact city matches
        query_lower = query.lower()
        for city in self.major_cities:
            if city in query_lower:
                # Check if it's a whole word match
                if re.search(rf'\b{re.escape(city)}\b', query_lower):
                    result = ExtractionResult(
                        value=city.title(),
                        confidence=0.9,
                        source='dictionary'
                    )
                    if result.confidence > best_confidence:
                        best_result = result
                        best_confidence = result.confidence
        
        return best_result
    
    def _extract_neighborhoods(self, query: str, doc) -> List[str]:
        """Extract neighborhood information from query."""
        neighborhoods = []
        query_lower = query.lower()
        
        # Check for neighborhood indicators
        for indicator in self.neighborhood_indicators:
            if re.search(rf'\b{re.escape(indicator)}\b', query_lower):
                neighborhoods.append(indicator.title())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_neighborhoods = []
        for neighborhood in neighborhoods:
            if neighborhood.lower() not in seen:
                seen.add(neighborhood.lower())
                unique_neighborhoods.append(neighborhood)
        
        return unique_neighborhoods[:10]  # Limit to 10
    
    def _extract_property_type(self, query: str, doc) -> Optional[ExtractionResult]:
        """Extract property type from query."""
        best_result = None
        best_confidence = 0.0
        
        for prop_type, patterns in self._compiled_property_types.items():
            for pattern in patterns:
                if pattern.search(query):
                    confidence = 0.8 if prop_type != PropertyType.OTHER else 0.5
                    result = ExtractionResult(
                        value=prop_type,
                        confidence=confidence,
                        source='regex'
                    )
                    if result.confidence > best_confidence:
                        best_result = result
                        best_confidence = result.confidence
        
        return best_result
    
    def _extract_amenities(self, query: str, doc) -> Dict[str, bool]:
        """Extract amenity requirements from query."""
        amenities = {}
        
        for amenity, patterns in self._compiled_amenities.items():
            for pattern in patterns:
                match = pattern.search(query)
                if match:
                    # Check for negation
                    context = query[max(0, match.start()-20):match.end()+20].lower()
                    is_negative = any(neg in context for neg in ['no', 'not', 'without', 'unfurnished'])
                    
                    if amenity == 'furnished' and 'unfurnished' in match.group().lower():
                        amenities['has_furnished'] = False
                    else:
                        amenities[f'has_{amenity}'] = not is_negative
        
        return amenities
    
    def _extract_keywords(self, query: str, doc) -> List[str]:
        """Extract relevant keywords from query."""
        keywords = []
        query_lower = query.lower()
        
        # Extract property keywords
        for keyword in self.property_keywords:
            if re.search(rf'\b{re.escape(keyword)}\b', query_lower):
                keywords.append(keyword)
        
        return keywords[:20]  # Limit to 20 keywords
    
    def _process_bedroom_matches(self, matches: List[str], base_confidence: float) -> Optional[ExtractionResult]:
        """Process bedroom regex matches."""
        if not matches:
            return None
        
        # Handle different match types
        try:
            if isinstance(matches[0], str):  # Single number
                num = int(matches[0])
                if 0 <= num <= 20:
                    return ExtractionResult(
                        value={'beds': num},
                        confidence=base_confidence,
                        source='regex'
                    )
            elif isinstance(matches[0], tuple) and len(matches[0]) == 2:  # Range
                min_beds, max_beds = int(matches[0][0]), int(matches[0][1])
                if 0 <= min_beds <= max_beds <= 20:
                    return ExtractionResult(
                        value={'beds_min': min_beds, 'beds_max': max_beds},
                        confidence=base_confidence,
                        source='regex'
                    )
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _process_bathroom_matches(self, matches: List[str], base_confidence: float) -> Optional[ExtractionResult]:
        """Process bathroom regex matches."""
        if not matches:
            return None
        
        try:
            if isinstance(matches[0], str):  # Single number
                num = float(matches[0])
                if 0 <= num <= 20:
                    return ExtractionResult(
                        value={'baths': num},
                        confidence=base_confidence,
                        source='regex'
                    )
            elif isinstance(matches[0], tuple) and len(matches[0]) == 2:  # Range
                min_baths, max_baths = float(matches[0][0]), float(matches[0][1])
                if 0 <= min_baths <= max_baths <= 20:
                    return ExtractionResult(
                        value={'baths_min': min_baths, 'baths_max': max_baths},
                        confidence=base_confidence,
                        source='regex'
                    )
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _process_price_matches(self, matches: List[str], base_confidence: float, 
                             query: str, pattern) -> Optional[ExtractionResult]:
        """Process price regex matches."""
        if not matches:
            return None
        
        try:
            # Clean and convert price
            if isinstance(matches[0], str):  # Single price
                price_str = matches[0].replace(',', '')
                price = float(price_str)
                
                # Handle thousands abbreviation
                if 'k' in pattern.pattern.lower():
                    price *= 1000
                
                # Determine if it's min or max based on context
                match_obj = pattern.search(query)
                if match_obj:
                    context = query[max(0, match_obj.start()-20):match_obj.end()+20].lower()
                    if any(word in context for word in ['under', 'below', 'less', 'max', 'maximum']):
                        return ExtractionResult(
                            value={'max_price': price},
                            confidence=base_confidence,
                            source='regex'
                        )
                    elif any(word in context for word in ['over', 'above', 'more', 'min', 'minimum']):
                        return ExtractionResult(
                            value={'min_price': price},
                            confidence=base_confidence,
                            source='regex'
                        )
                
                # Default to max price if no context
                return ExtractionResult(
                    value={'max_price': price},
                    confidence=base_confidence * 0.8,
                    source='regex'
                )
                
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _calculate_confidence(self, results: Dict, query: str) -> float:
        """Calculate overall parsing confidence."""
        confidences = []
        
        for key, result in results.items():
            if isinstance(result, ExtractionResult):
                confidences.append(result.confidence)
            elif isinstance(result, list) and result:
                confidences.append(0.7)  # Default confidence for lists
            elif isinstance(result, dict) and result:
                confidences.append(0.7)  # Default confidence for dicts
        
        if not confidences:
            return 0.1  # Minimum confidence for any parse
        
        # Weighted average with bonus for multiple extractions
        base_confidence = sum(confidences) / len(confidences)
        extraction_bonus = min(0.2, len(confidences) * 0.05)
        
        return min(1.0, base_confidence + extraction_bonus)
    
    def _build_parsed_query(self, results: Dict, confidence: float) -> ParsedQuery:
        """Build the final ParsedQuery object."""
        parsed_data = {'confidence': confidence}
        
        # Process bedroom results
        if results['beds']:
            parsed_data.update(results['beds'].value)
        
        # Process bathroom results
        if results['baths']:
            parsed_data.update(results['baths'].value)
        
        # Process price results
        if results['price']:
            parsed_data.update(results['price'].value)
        
        # Process city results
        if results['city']:
            parsed_data['city'] = results['city'].value
        
        # Process neighborhoods
        if results['neighborhoods']:
            parsed_data['neighborhoods'] = results['neighborhoods']
        
        # Process property type
        if results['property_type']:
            parsed_data['property_type'] = results['property_type'].value
        
        # Process amenities
        if results['amenities']:
            parsed_data.update(results['amenities'])
        
        # Process keywords
        if results['keywords']:
            parsed_data['keywords'] = results['keywords']
        
        return ParsedQuery(**parsed_data) 