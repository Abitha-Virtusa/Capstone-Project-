"""
Final optimized Amazon scraper with detailed HTML inspection
"""

import requests
from bs4 import BeautifulSoup
import json
import sys
from urllib.parse import urlencode
import re
import time
from fake_useragent import UserAgent


class AmazonScraperFinal:
    """Final optimized Amazon scraper"""
    
    def __init__(self):
        self.base_url = "https://www.amazon.com/s?"
        ua = UserAgent()
        self.headers = {
            'User-Agent': ua.chrome,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def search_products(self, product_name, max_results=20, max_retries=5, retry_delay=8):
        """Search for products with retry mechanism"""
        params = {
            'k': product_name,
            'ref': 'nb_sb_noss'
        }
        
        search_url = self.base_url + urlencode(params)
        print(f"[*] Searching Amazon for: {product_name}")
        print(f"[*] URL: {search_url}\n")
        
        for attempt in range(max_retries):
            try:
                print(f"[*] Attempt {attempt + 1}/{max_retries}...")
                response = requests.get(search_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                products = self._extract_products(soup, max_results)
                
                return products
                
            except requests.exceptions.RequestException as e:
                print(f"[!] Error: {e}")
                
                if attempt < max_retries - 1:
                    print(f"[*] Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    print(f"[!] Max retries ({max_retries}) reached. Giving up.")
                    return []
        
        return []
    
    def _extract_products(self, soup, max_results):
        """Extract products"""
        products = []
        
        containers = soup.select('div[data-component-type="s-search-result"]')
        
        if not containers:
            print("[!] No products found")
            return []
        
        print(f"[+] Found {len(containers)} products\n")
        
        for idx, container in enumerate(containers[:max_results]):
            try:
                product = self._parse_product(container)
                if product and product.get('name') != 'N/A':
                    product['rank'] = idx + 1
                    products.append(product)
                    print(f"[+] [{idx + 1}] {product['name'][:60]}...")
            except Exception as e:
                print(f"[!] Error parsing product {idx + 1}: {e}")
                continue
        
        print(f"\n[+] Extracted {len(products)} products\n")
        return products
    
    def _parse_product(self, container):
        """Parse product with all available data"""
        product = {}
        
        # ASIN
        product['asin'] = container.get('data-asin', 'N/A')
        
        # Name
        name_elem = container.select_one('h2 a span')
        if not name_elem:
            name_elem = container.select_one('h2 span')
        product['name'] = name_elem.get_text(strip=True) if name_elem else 'N/A'
        
        # URL - Enhanced extraction with multiple methods
        url = self._get_url(container)
        product['url'] = url
        
        # Price - comprehensive extraction
        price = self._get_price(container)
        product['price'] = price
        
        # Original price
        orig_elem = container.select_one('span.a-price.a-text-price span.a-offscreen')
        product['original_price'] = orig_elem.get_text(strip=True) if orig_elem else 'N/A'
        
        # Discount
        discount_elem = container.select_one('span.a-badge-label-inner')
        discount = discount_elem.get_text(strip=True) if discount_elem else 'N/A'
        product['discount'] = discount if '%' in str(discount) else 'N/A'
        
        # Rating - multiple attempts
        rating = self._get_rating(container)
        product['rating'] = rating
        
        # Reviews count - multiple attempts  
        reviews = self._get_reviews(container)
        product['num_reviews'] = reviews
        
        # Prime
        prime = container.select_one('i.a-icon-prime')
        product['prime_available'] = 'Yes' if prime else 'No'
        
        # Delivery
        delivery = self._get_delivery(container)
        product['delivery'] = delivery
        
        # Sponsored
        sponsored = container.select_one('span.puis-label-popover-default')
        product['sponsored'] = 'Yes' if sponsored and 'Sponsored' in sponsored.get_text() else 'No'
        
        # Badges
        badges = self._get_badges(container)
        product['badges'] = badges
        
        # Image
        img = container.select_one('img.s-image')
        product['image_url'] = img.get('src', 'N/A') if img else 'N/A'
        
        # Brand - comprehensive extraction
        brand = self._get_brand(container)
        product['brand'] = brand
        
        # Availability
        avail_elem = container.select_one('span.a-color-price, span.a-color-success')
        product['availability'] = avail_elem.get_text(strip=True) if avail_elem else 'In Stock'
        
        # Specifications
        specs = self._get_specs(container)
        product['specifications'] = specs
        
        # Additional
        product['small_business'] = 'Yes' if 'Small Business' in container.get_text() else 'No'
        product['climate_pledge'] = 'Yes' if 'Climate Pledge' in container.get_text() else 'No'
        
        return product
    
    def _get_url(self, container):
        """Extract product URL with multiple methods"""
        # Method 1: h2 a tag (most common)
        url_elem = container.select_one('h2 a')
        if url_elem and url_elem.get('href'):
            href = url_elem['href']
            # Clean up the URL - remove tracking parameters if too long
            if len(href) > 500:
                # Try to extract the basic product URL
                match = re.search(r'(/[^/]+/dp/[A-Z0-9]{10})', href)
                if match:
                    return f"https://www.amazon.com{match.group(1)}"
            return f"https://www.amazon.com{href}" if href.startswith('/') else href
        
        # Method 2: Any a tag with the product link
        link_elem = container.select_one('a.a-link-normal.s-no-outline')
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            return f"https://www.amazon.com{href}" if href.startswith('/') else href
        
        # Method 3: Find any link containing /dp/ (product detail page)
        all_links = container.select('a[href*="/dp/"]')
        if all_links:
            href = all_links[0]['href']
            return f"https://www.amazon.com{href}" if href.startswith('/') else href
        
        # Method 4: Construct URL from ASIN if available
        asin = container.get('data-asin')
        if asin and asin != 'N/A':
            return f"https://www.amazon.com/dp/{asin}"
        
        return 'N/A'
    
    def _get_price(self, container):
        """Extract price with fallbacks"""
        # Method 1: Whole + fraction
        whole = container.select_one('span.a-price-whole')
        if whole:
            price = whole.get_text(strip=True)
            fraction = container.select_one('span.a-price-fraction')
            if fraction:
                price += fraction.get_text(strip=True)
            return f"${price.replace(',', '')}"
        
        # Method 2: Offscreen
        offscreen = container.select_one('span.a-price span.a-offscreen')
        if offscreen:
            return offscreen.get_text(strip=True)
        
        # Method 3: Direct text search
        price_text = container.get_text()
        match = re.search(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', price_text)
        if match:
            return f"${match.group(1)}"
        
        return 'N/A'
    
    def _get_rating(self, container):
        """Extract rating"""
        # Method 1: Icon alt text
        rating_elem = container.select_one('span.a-icon-alt')
        if rating_elem:
            return rating_elem.get_text(strip=True)
        
        # Method 2: Aria label
        rating_elem = container.select_one('i[class*="a-star"]')
        if rating_elem:
            aria = rating_elem.get('aria-label', '')
            if 'out of' in aria:
                return aria
        
        # Method 3: Direct text search
        text = container.get_text()
        match = re.search(r'(\d+\.?\d*)\s+out\s+of\s+5\s+stars', text)
        if match:
            return f"{match.group(1)} out of 5 stars"
        
        return 'N/A'
    
    def _get_reviews(self, container):
        """Extract review count"""
        # Method 1: Direct element
        reviews_elem = container.select_one('span.a-size-base.s-underline-text')
        if reviews_elem:
            text = reviews_elem.get_text(strip=True)
            # Clean up - should be just a number
            text = text.replace(',', '')
            if text.isdigit() or (text.replace('.', '').replace('K', '').isdigit()):
                return reviews_elem.get_text(strip=True)  # Return original with commas
        
        # Method 2: Look in aria-label of rating
        rating_elem = container.select_one('span[aria-label]')
        if rating_elem:
            aria = rating_elem.get('aria-label', '')
            # Look for pattern like "18,721" in the aria label
            match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)', aria)
            if match:
                num = match.group(1).replace(',', '')
                if num.isdigit() and int(num) > 10:  # Likely review count
                    return match.group(1)
        
        # Method 3: Search all text for review count pattern
        text = container.get_text()
        # Look for patterns like "18,721 ratings" or "(1,234)"
        patterns = [
            r'(\d{1,3}(?:,\d{3})+)\s*(?:ratings?|reviews?)',
            r'\((\d{1,3}(?:,\d{3})+)\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'N/A'
    
    def _get_delivery(self, container):
        """Extract delivery info"""
        # Method 1: Direct element
        delivery_elem = container.select_one('span.a-color-base.a-text-bold')
        if delivery_elem:
            text = delivery_elem.get_text(strip=True)
            if any(word in text.lower() for word in ['delivery', 'arrives', 'get it', 'tomorrow', 'today']):
                return text
        
        # Method 2: Aria-label search
        delivery_elem = container.select_one('span[aria-label*="delivery"], span[aria-label*="Delivery"]')
        if delivery_elem:
            return delivery_elem.get('aria-label', 'N/A')
        
        # Method 3: Look for date patterns in text
        text = container.get_text()
        # Look for patterns like "Get it by Monday, Nov 27" or "FREE delivery Tomorrow"
        match = re.search(r'(?:FREE|Get it|Arrives?)\s+(?:by\s+)?([A-Z][a-z]+,?\s+[A-Z][a-z]+\s+\d+|[Tt]omorrow|[Tt]oday)', text)
        if match:
            return match.group(0)
        
        return 'N/A'
    
    def _get_badges(self, container):
        """Extract badges"""
        badges = []
        
        # Badge spans
        badge_elements = container.select('span.a-badge-text')
        for badge in badge_elements:
            text = badge.get_text(strip=True)
            # Filter out discount percentages
            if text and '%' not in text and len(text) < 50:
                badges.append(text)
        
        # Amazon's Choice
        choice = container.select_one('span[data-a-badge-color*="sx"]')
        if choice:
            text = choice.get_text(strip=True)
            if text and text not in badges:
                badges.append(text)
        
        # Best Seller
        if 'Best Seller' in container.get_text():
            if 'Best Seller' not in badges:
                badges.append('Best Seller')
        
        return ', '.join(badges) if badges else 'None'
    
    def _get_brand(self, container):
        """Extract brand"""
        # Method 1: Direct brand span
        brand_elem = container.select_one('h5 span.a-size-base')
        if brand_elem:
            text = brand_elem.get_text(strip=True)
            if text and len(text) < 50:
                return text
        
        # Method 2: Byline
        byline = container.select_one('div.a-row.a-size-base.a-color-secondary span.a-size-base')
        if byline:
            text = byline.get_text(strip=True)
            # Avoid "Visit the X Store" type text
            if text and len(text) < 50 and not any(word in text.lower() for word in ['visit', 'store', 'shop']):
                return text
        
        # Method 3: Extract from title (brand usually comes first)
        name = container.select_one('h2')
        if name:
            name_text = name.get_text(strip=True)
            # Take first 1-3 words as potential brand
            words = name_text.split()
            if words:
                potential_brand = ' '.join(words[:min(2, len(words))])
                if len(potential_brand) < 30:
                    return potential_brand
        
        return 'N/A'
    
    def _get_specs(self, container):
        """Extract specifications"""
        specs = []
        
        # Look for spec-like text
        all_spans = container.select('span.a-size-base')
        for span in all_spans:
            text = span.get_text(strip=True)
            # Filter: meaningful length, no prices, not too long
            if 20 < len(text) < 200 and '$' not in text:
                # Avoid common non-spec text
                if not any(x in text.lower() for x in ['sponsored', 'visit', 'shop', 'store', 'see more', 'amazon']):
                    specs.append(text)
        
        return ' | '.join(specs[:3]) if specs else 'N/A'
    
    def print_products(self, products):
        """Print products nicely"""
        if not products:
            print("[!] No products found")
            return
        
        print(f"\n{'='*100}")
        print(f"FOUND {len(products)} PRODUCTS")
        print(f"{'='*100}\n")
        
        for p in products:
            print(f"Rank: {p.get('rank')}")
            print(f"Name: {p.get('name')[:75]}")
            print(f"Brand: {p.get('brand')}")
            print(f"ASIN: {p.get('asin')}")
            
            price_line = f"Price: {p.get('price')}"
            if p.get('original_price') != 'N/A':
                price_line += f" (Was: {p.get('original_price')})"
            if p.get('discount') != 'N/A':
                price_line += f" [{p.get('discount')} OFF]"
            print(price_line)
            
            print(f"Rating: {p.get('rating')}")
            print(f"Reviews: {p.get('num_reviews')}")
            print(f"Prime: {p.get('prime_available')}")
            print(f"Delivery: {p.get('delivery')}")
            print(f"Badges: {p.get('badges')}")
            print(f"URL: {p.get('url')[:70]}...")
            print(f"{'-'*100}\n")
        
        # Stats
        total_fields = len(products[0])
        avg_filled = sum(
            sum(1 for v in p.values() if v and v != 'N/A' and v != 'None')
            for p in products
        ) / len(products)
        percentage = (avg_filled / total_fields * 100)
        
        print(f"[STATS] Data Completeness: {avg_filled:.1f}/{total_fields} fields ({percentage:.1f}%)")
        print(f"{'='*100}\n")
    
    def save_to_json(self, products, filename='amazon_products.json'):
        """Save to JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            print(f"[+] Saved to {filename}")
        except Exception as e:
            print(f"[!] Error: {e}")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        product_name = ' '.join(sys.argv[1:])
    else:
        product_name = input("Enter product name: ").strip()
    
    if not product_name:
        print("[!] Please provide a product name")
        return
    
    scraper = AmazonScraperFinal()
    products = scraper.search_products(product_name, max_results=20)
    
    scraper.print_products(products)
    
    if products:
        save = input("Save to JSON? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("Filename (default: amazon_products.json): ").strip()
            filename = filename if filename else 'amazon_products.json'
            if not filename.endswith('.json'):
                filename += '.json'
            scraper.save_to_json(products, filename)


if __name__ == "__main__":
    main()
