"""
Real Estate Website-Specific Scraping Adapters
Specialized scrapers for major real estate platforms with robust fallback strategies
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime

class ZillowScraper:
    """Specialized scraper for Zillow.com with robust selectors"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        self.domain = "zillow.com"
        
        # Zillow-specific selectors with fallbacks
        self.selectors = {
            "price": [
                "[data-testid='price']",
                ".ds-price .ds-value",
                ".price-range-summary",
                "[class*='price'] [class*='value']",
                ".hdp-fact-ataglance-price"
            ],
            "address": [
                "[data-testid='bdp-building-address']",
                "h1[data-testid='bdp-building-name']",
                ".ds-address-container",
                ".hdp-fact-ataglance-address"
            ],
            "bedrooms": [
                "[data-testid='bed-bath-item']:contains('bed')",
                ".ds-bed-bath-living-area [class*='bed']",
                "[class*='bed-bath'] span:first-child"
            ],
            "bathrooms": [
                "[data-testid='bed-bath-item']:contains('bath')",
                ".ds-bed-bath-living-area [class*='bath']",
                "[class*='bed-bath'] span:nth-child(2)"
            ],
            "sqft": [
                "[data-testid='bed-bath-item']:contains('sqft')",
                ".ds-bed-bath-living-area [class*='sqft']",
                "[class*='sqft']"
            ],
            "description": [
                "[data-testid='description-text']",
                ".ds-overview-section",
                ".property-description"
            ]
        }
    
    async def extract_data(self, url: str) -> Dict[str, Any]:
        """Extract data using Zillow-specific patterns"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await self.page.wait_for_timeout(2000)  # Let dynamic content load
            
            # Close any modals
            await self._close_zillow_modals()
            
            data = {}
            
            # Extract each field with multiple fallback attempts
            for field, selectors in self.selectors.items():
                value = await self._extract_field_with_fallbacks(field, selectors)
                if value:
                    data[field] = value
            
            # Extract photos specifically for Zillow
            photos = await self._extract_zillow_photos()
            if photos:
                data["images"] = photos
            
            # Try to extract structured data
            structured_data = await self._extract_zillow_structured_data()
            data.update(structured_data)
            
            return data
            
        except Exception as e:
            self.logger.error("Zillow extraction failed", url=url, error=str(e))
            return {"error": str(e)}
    
    async def _close_zillow_modals(self):
        """Close Zillow-specific modals and popups"""
        modal_selectors = [
            "[aria-label='Close Modal']",
            "[data-testid='modal-close-button']",
            ".modal-close-button",
            "[class*='close']:visible"
        ]
        
        for selector in modal_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await self.page.wait_for_timeout(500)
            except:
                continue
    
    async def _extract_field_with_fallbacks(self, field: str, selectors: List[str]) -> Optional[str]:
        """Extract field value with multiple selector fallbacks"""
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and text.strip():
                        return self._clean_field_value(field, text.strip())
            except:
                continue
        return None
    
    async def _extract_zillow_photos(self) -> List[str]:
        """Extract photo URLs from Zillow gallery"""
        photos = []
        try:
            # Zillow photo selectors
            photo_selectors = [
                ".media-carousel img",
                ".photo-carousel img", 
                "[data-testid='photo-carousel'] img"
            ]
            
            for selector in photo_selectors:
                elements = await self.page.query_selector_all(selector)
                for element in elements[:10]:  # Limit to 10 photos
                    src = await element.get_attribute("src")
                    if src and not src.startswith("data:"):
                        photos.append(urljoin(self.page.url, src))
                if photos:
                    break
                    
        except Exception as e:
            self.logger.debug("Photo extraction failed", error=str(e))
        
        return photos
    
    async def _extract_zillow_structured_data(self) -> Dict[str, Any]:
        """Extract Zillow-specific structured data"""
        data = {}
        try:
            # Look for Zillow's JSON data
            script_elements = await self.page.query_selector_all('script:contains("hdpData")')
            for element in script_elements:
                try:
                    content = await element.inner_text()
                    if "hdpData" in content:
                        # Extract relevant data from Zillow's data structure
                        # This would need to be adapted based on actual Zillow structure
                        pass
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug("Structured data extraction failed", error=str(e))
        
        return data
    
    def _clean_field_value(self, field: str, value: str) -> str:
        """Clean and normalize field values"""
        if field == "price":
            # Extract price numbers and format consistently
            price_match = re.search(r'\$[\d,]+', value)
            return price_match.group() if price_match else value
        elif field in ["bedrooms", "bathrooms"]:
            # Extract just the number
            number_match = re.search(r'\d+', value)
            return number_match.group() if number_match else value
        elif field == "sqft":
            # Extract square footage number
            sqft_match = re.search(r'([\d,]+)', value)
            return sqft_match.group().replace(',', '') if sqft_match else value
        
        return value


class RealtorComScraper:
    """Specialized scraper for Realtor.com"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        self.domain = "realtor.com"
        
        self.selectors = {
            "price": [
                "[data-testid='price-display']",
                ".price-display",
                ".listing-price",
                "[class*='price']"
            ],
            "address": [
                "[data-testid='street-address']",
                ".street-address",
                "h1",
                ".property-address"
            ],
            "bedrooms": [
                "[data-testid='property-beds']",
                ".property-beds",
                "[class*='bed']"
            ],
            "bathrooms": [
                "[data-testid='property-baths']", 
                ".property-baths",
                "[class*='bath']"
            ],
            "sqft": [
                "[data-testid='property-sqft']",
                ".property-sqft",
                "[class*='sqft']"
            ]
        }
    
    async def extract_data(self, url: str) -> Dict[str, Any]:
        """Extract data from Realtor.com"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            data = {}
            
            for field, selectors in self.selectors.items():
                for selector in selectors:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                            if text and text.strip():
                                data[field] = text.strip()
                                break
                    except:
                        continue
            
            return data
            
        except Exception as e:
            self.logger.error("Realtor.com extraction failed", url=url, error=str(e))
            return {"error": str(e)}


class RedfinScraper:
    """Specialized scraper for Redfin.com"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        self.domain = "redfin.com"
        
        self.selectors = {
            "price": [
                ".statsValue",
                ".price-section .price",
                "[class*='price-display']"
            ],
            "address": [
                ".street-address",
                ".address .value",
                "h1.address"
            ],
            "bedrooms": [
                ".stat-block:contains('Beds') .statsValue",
                ".bed-bath-sqft .value:first-child"
            ],
            "bathrooms": [
                ".stat-block:contains('Baths') .statsValue", 
                ".bed-bath-sqft .value:nth-child(2)"
            ],
            "sqft": [
                ".stat-block:contains('Sq. Ft.') .statsValue",
                ".bed-bath-sqft .value:last-child"
            ]
        }
    
    async def extract_data(self, url: str) -> Dict[str, Any]:
        """Extract data from Redfin"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            data = {}
            
            for field, selectors in self.selectors.items():
                for selector in selectors:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                            if text and text.strip():
                                data[field] = text.strip()
                                break
                    except:
                        continue
            
            return data
            
        except Exception as e:
            self.logger.error("Redfin extraction failed", url=url, error=str(e))
            return {"error": str(e)}


class GenericRealEstateScraper:
    """Generic scraper for unknown real estate sites"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        
        # Generic patterns that work across many sites
        self.patterns = {
            "price": [
                r'\$[\d,]+',
                r'Price:\s*\$[\d,]+',
                r'Listed\s*(?:at|for)?\s*\$[\d,]+'
            ],
            "bedrooms": [
                r'(\d+)\s*(?:bed|bedroom|br)s?',
                r'(\d+)\s*bed'
            ],
            "bathrooms": [
                r'(\d+)\s*(?:bath|bathroom|ba)s?',
                r'(\d+)\s*bath'
            ],
            "sqft": [
                r'([\d,]+)\s*(?:sqft|sq\.?\s*ft|square\s*feet)',
                r'([\d,]+)\s*sqft'
            ]
        }
    
    async def extract_data(self, url: str) -> Dict[str, Any]:
        """Extract data using generic patterns"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await self.page.wait_for_timeout(2000)
            
            # Get all page text
            page_text = await self.page.inner_text("body")
            
            data = {}
            
            # Extract using regex patterns
            for field, patterns in self.patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    if matches:
                        data[field] = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        break
            
            # Try to extract title as address
            title = await self.page.title()
            if title:
                data["title"] = title
                # Often addresses are in titles
                if any(indicator in title.lower() for indicator in [",", "st", "ave", "rd", "dr", "ln"]):
                    data["address"] = title
            
            return data
            
        except Exception as e:
            self.logger.error("Generic extraction failed", url=url, error=str(e))
            return {"error": str(e)}


class AdaptiveRealEstateScraper:
    """Adaptive scraper that chooses the best strategy based on domain"""
    
    def __init__(self, page, logger):
        self.page = page
        self.logger = logger
        
        # Domain-specific scrapers
        self.scrapers = {
            "zillow.com": ZillowScraper,
            "realtor.com": RealtorComScraper,
            "redfin.com": RedfinScraper
        }
    
    async def extract_data(self, url: str) -> Dict[str, Any]:
        """Choose and execute the best scraper for the domain"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Remove www prefix
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Find matching scraper
            scraper_class = None
            for domain_pattern, scraper in self.scrapers.items():
                if domain_pattern in domain:
                    scraper_class = scraper
                    break
            
            # Use domain-specific scraper or fall back to generic
            if scraper_class:
                scraper = scraper_class(self.page, self.logger)
                self.logger.info("Using specialized scraper", domain=domain, scraper=scraper_class.__name__)
            else:
                scraper = GenericRealEstateScraper(self.page, self.logger)
                self.logger.info("Using generic scraper", domain=domain)
            
            result = await scraper.extract_data(url)
            
            # Add metadata
            result.update({
                "scraper_used": scraper.__class__.__name__,
                "domain": domain,
                "extracted_at": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            self.logger.error("Adaptive scraping failed", url=url, error=str(e))
            return {"error": str(e), "url": url}


# Factory function
def create_adaptive_scraper(page, logger):
    """Create an adaptive scraper instance"""
    return AdaptiveRealEstateScraper(page, logger)
