"""
Flipkart Product Scraper
"""

import requests
from bs4 import BeautifulSoup
import json
import sys
from urllib.parse import urlencode, quote_plus
import re
import time
from fake_useragent import UserAgent


class FlipkartScraper:
    """Flipkart product scraper with enhanced data extraction"""
    
    def __init__(self):
        self.base_url = "https://www.flipkart.com/search?"
        ua = UserAgent()
        self.headers = {
            'User-Agent': ua.chrome,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        }
    
    def search_products(self, product_name, max_results=20, max_retries=5, retry_delay=8):
        """Search for products on Flipkart with retry mechanism"""
        params = {
            'q': product_name,
            'otracker': 'search',
            'otracker1': 'search',
            'marketplace': 'FLIPKART',
            'as-show': 'on',
            'as': 'off'
        }
        
        search_url = self.base_url + urlencode(params)
        print(f"[*] Searching Flipkart for: {product_name}")
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
                print(f"[!] Error fetching data from Flipkart: {e}")
                
                if attempt < max_retries - 1:
                    print(f"[*] Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                else:
                    print(f"[!] Max retries ({max_retries}) reached. Giving up.")
                    return []
        
        return []
    
    def _extract_products(self, soup, max_results):
        """Extract product information from search results"""
        products = []
        
        # Flipkart uses different div structures for products
        # Try multiple selectors
        product_containers = []
        
        # Method 1: Common product card selector
        product_containers = soup.select('div[data-id]')
        
        # Method 2: Alternative selector
        if not product_containers:
            product_containers = soup.select('div._1AtVbE')
        
        # Method 3: Look for product links
        if not product_containers:
            product_containers = soup.select('div._13oc-S')
        
        # Method 4: Find by class patterns
        if not product_containers:
            product_containers = soup.find_all('div', class_=re.compile(r'_1AtVbE|_2kHMtA|_13oc-S|cPHDOP'))
        
        if not product_containers:
            print("[!] No products found. Flipkart may have blocked the request or changed HTML structure.")
            return []
        
        print(f"[+] Found {len(product_containers)} product containers\n")
        
        for idx, container in enumerate(product_containers[:max_results]):
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
        """Parse individual product container"""
        product = {}
        
        # Product ID (Flipkart's data-id attribute)
        product['product_id'] = container.get('data-id', 'N/A')
        
        # Product Name/Title
        name = self._get_name(container)
        product['name'] = name
        
        # URL
        url = self._get_url(container)
        product['url'] = url
        
        # Price
        price = self._get_price(container)
        product['price'] = price
        
        # Original price (MRP)
        original_price = self._get_original_price(container)
        product['original_price'] = original_price
        
        # Discount percentage
        discount = self._get_discount(container)
        product['discount'] = discount
        
        # Rating
        rating = self._get_rating(container)
        product['rating'] = rating
        
        # Number of ratings/reviews
        reviews = self._get_reviews(container)
        product['num_reviews'] = reviews
        
        # Brand
        brand = self._get_brand(container)
        product['brand'] = brand
        
        # Image URL
        image = self._get_image(container)
        product['image_url'] = image
        
        # Assured (Flipkart Assured badge)
        assured = container.find('div', class_=re.compile(r'_2Ix7k|_3l_jm'))
        product['flipkart_assured'] = 'Yes' if assured or 'Assured' in container.get_text() else 'No'
        
        # Plus (Flipkart Plus)
        plus = container.find('div', class_=re.compile(r'_3Djpdu'))
        product['flipkart_plus'] = 'Yes' if plus or 'Plus' in container.get_text() else 'No'
        
        # Delivery info
        delivery = self._get_delivery(container)
        product['delivery'] = delivery
        
        # Highlights/Specifications
        highlights = self._get_highlights(container)
        product['highlights'] = highlights
        
        # EMI available
        emi = 'EMI' in container.get_text() or 'No Cost EMI' in container.get_text()
        product['emi_available'] = 'Yes' if emi else 'No'
        
        # Exchange offer
        exchange = 'Exchange' in container.get_text()
        product['exchange_offer'] = 'Yes' if exchange else 'No'
        
        # Bank offers
        bank_offer = self._get_bank_offer(container)
        product['bank_offer'] = bank_offer
        
        # Availability
        product['availability'] = self._get_availability(container)
        
        return product
    
    def _get_name(self, container):
        """Extract product name"""
        # Method 1: Title attribute on link
        title_elem = container.find('a', {'title': True})
        if title_elem and title_elem.get('title'):
            return title_elem['title'].strip()
        
        # Method 2: Common class for product name
        name_selectors = [
            'div._4rR01T',
            'a._1fQZEK',
            'div.s1Q9rs',
            'a.IRpwTa',
            'div._2WkVRV',
            'a.wjcEIp',
            'div.KzDlHZ'
        ]
        
        for selector in name_selectors:
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    return text
        
        # Method 3: Find any link with substantial text
        links = container.find_all('a')
        for link in links:
            text = link.get_text(strip=True)
            if text and len(text) > 20:
                return text
        
        return 'N/A'
    
    def _get_url(self, container):
        """Extract product URL"""
        # Method 1: Find link with title
        link = container.find('a', {'title': True, 'href': True})
        if link:
            href = link['href']
            if href.startswith('/'):
                return f"https://www.flipkart.com{href}"
            elif href.startswith('http'):
                return href
        
        # Method 2: Find any product link
        link = container.find('a', {'href': re.compile(r'/p/')})
        if link:
            href = link['href']
            return f"https://www.flipkart.com{href}" if href.startswith('/') else href
        
        # Method 3: Any link in container
        link = container.find('a', {'href': True})
        if link:
            href = link['href']
            if '/p/' in href or '/product' in href:
                return f"https://www.flipkart.com{href}" if href.startswith('/') else href
        
        # Method 4: Construct from product ID
        product_id = container.get('data-id')
        if product_id and product_id != 'N/A':
            return f"https://www.flipkart.com/product/p/{product_id}"
        
        return 'N/A'
    
    def _get_price(self, container):
        """Extract current price"""
        # Method 1: Price class selectors
        price_selectors = [
            'div._30jeq3',
            'div._25b18c',
            'div._1vC4OE',
            'div._3I9_wc',
            'div._2rQ-NK'
        ]
        
        for selector in price_selectors:
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if '₹' in text:
                    return text
        
        # Method 2: Look for rupee symbol
        text = container.get_text()
        match = re.search(r'₹[\s]*([0-9,]+)', text)
        if match:
            return f"₹{match.group(1)}"
        
        return 'N/A'
    
    def _get_original_price(self, container):
        """Extract original price (MRP)"""
        # Look for strikethrough price
        price_selectors = [
            'div._3I9_wc._27UcVY',
            'div._3auQ3N._1POkHg',
            'span._2Tpdn3'
        ]
        
        for selector in price_selectors:
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if '₹' in text:
                    return text
        
        return 'N/A'
    
    def _get_discount(self, container):
        """Extract discount percentage"""
        # Method 1: Discount class selectors
        discount_selectors = [
            'div._3Ay6sb',
            'div._3xFhiH',
            'span._1uv9Cb'
        ]
        
        for selector in discount_selectors:
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if '%' in text and 'off' in text.lower():
                    return text
        
        # Method 2: Search for discount pattern
        text = container.get_text()
        match = re.search(r'(\d+%\s+off)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return 'N/A'
    
    def _get_rating(self, container):
        """Extract product rating"""
        # Method 1: Rating div selectors
        rating_selectors = [
            'div._3LWZlK',
            'div._1lRcqv',
            'span._1lRcqv',
            'div.gUuXy-'
        ]
        
        for selector in rating_selectors:
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # Extract rating number
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    rating_val = float(match.group(1))
                    if 0 <= rating_val <= 5:
                        return f"{rating_val} ★"
        
        # Method 2: Look for rating pattern in text
        text = container.get_text()
        match = re.search(r'(\d+\.?\d*)\s*★', text)
        if match:
            return f"{match.group(1)} ★"
        
        return 'N/A'
    
    def _get_reviews(self, container):
        """Extract number of ratings/reviews"""
        # Method 1: Review count selectors
        review_selectors = [
            'span._2_R_DZ',
            'span._13vcmD',
            'span.Wphh3N'
        ]
        
        for selector in review_selectors:
            elem = container.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # Extract numbers and commas
                match = re.search(r'([\d,]+)', text)
                if match:
                    return match.group(1)
        
        # Method 2: Look for patterns like "1,234 Ratings"
        text = container.get_text()
        patterns = [
            r'([\d,]+)\s*(?:Ratings?|Reviews?)',
            r'\(([\d,]+)\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num_str = match.group(1).replace(',', '')
                if num_str.isdigit() and int(num_str) > 5:
                    return match.group(1)
        
        return 'N/A'
    
    def _get_brand(self, container):
        """Extract brand name"""
        # Method 1: From product name (usually first word)
        name = self._get_name(container)
        if name != 'N/A':
            words = name.split()
            if words:
                # Common brands that might be first word
                potential_brand = words[0].strip()
                if len(potential_brand) < 30:
                    return potential_brand
        
        # Method 2: Look for "Brand:" label
        text = container.get_text()
        match = re.search(r'Brand:\s*([A-Za-z0-9\s]+)', text)
        if match:
            return match.group(1).strip()
        
        return 'N/A'
    
    def _get_image(self, container):
        """Extract product image URL"""
        # Method 1: Find img tag
        img = container.find('img', {'src': True})
        if img:
            src = img['src']
            if src and 'http' in src:
                return src
        
        # Method 2: data-src attribute (lazy loading)
        img = container.find('img', {'data-src': True})
        if img:
            return img['data-src']
        
        return 'N/A'
    
    def _get_delivery(self, container):
        """Extract delivery information"""
        text = container.get_text()
        
        # Look for delivery patterns
        patterns = [
            r'(Free Delivery)',
            r'(Delivery by [A-Za-z]+,?\s+[A-Za-z]+\s+\d+)',
            r'(Get it by [^.]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        if 'Free Delivery' in text:
            return 'Free Delivery'
        elif 'Delivery' in text:
            return 'Available'
        
        return 'N/A'
    
    def _get_highlights(self, container):
        """Extract product highlights/specifications"""
        highlights = []
        
        # Method 1: Look for ul li structure
        ul_elem = container.find('ul')
        if ul_elem:
            li_elems = ul_elem.find_all('li')
            for li in li_elems[:5]:
                text = li.get_text(strip=True)
                if text and len(text) > 10:
                    highlights.append(text)
        
        # Method 2: Look for highlight divs
        highlight_divs = container.find_all('div', class_=re.compile(r'_21Ahn-|fMghBO'))
        for div in highlight_divs[:5]:
            text = div.get_text(strip=True)
            if text and 20 < len(text) < 200:
                highlights.append(text)
        
        return ' | '.join(highlights[:3]) if highlights else 'N/A'
    
    def _get_bank_offer(self, container):
        """Extract bank offer information"""
        text = container.get_text()
        
        # Look for bank offer patterns
        patterns = [
            r'((?:Extra\s+)?₹[\d,]+\s+off\s+on\s+[A-Za-z\s]+Bank)',
            r'(\d+%\s+[Cc]ashback.*?[Bb]ank)',
            r'(Bank Offer[^.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)[:80]
        
        if 'Bank Offer' in text:
            return 'Available'
        
        return 'N/A'
    
    def _get_availability(self, container):
        """Check product availability"""
        text = container.get_text()
        
        if 'Out of Stock' in text or 'Sold Out' in text:
            return 'Out of Stock'
        elif 'Currently Unavailable' in text:
            return 'Currently Unavailable'
        elif 'Coming Soon' in text:
            return 'Coming Soon'
        else:
            return 'In Stock'
    
    def print_products(self, products):
        """Print products in formatted way"""
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
            print(f"ID: {p.get('product_id')}")
            
            price_line = f"Price: {p.get('price')}"
            if p.get('original_price') != 'N/A':
                price_line += f" (MRP: {p.get('original_price')})"
            if p.get('discount') != 'N/A':
                price_line += f" [{p.get('discount')}]"
            print(price_line)
            
            print(f"Rating: {p.get('rating')}")
            print(f"Reviews: {p.get('num_reviews')}")
            print(f"Flipkart Assured: {p.get('flipkart_assured')}")
            print(f"Flipkart Plus: {p.get('flipkart_plus')}")
            print(f"Delivery: {p.get('delivery')}")
            print(f"EMI: {p.get('emi_available')}")
            print(f"Exchange: {p.get('exchange_offer')}")
            
            if p.get('bank_offer') != 'N/A':
                print(f"Bank Offer: {p.get('bank_offer')[:60]}...")
            
            highlights = p.get('highlights', 'N/A')
            if len(highlights) > 80:
                highlights = highlights[:77] + '...'
            print(f"Highlights: {highlights}")
            
            print(f"URL: {p.get('url')[:70]}...")
            print(f"{'-'*100}\n")
        
        # Stats
        if products:
            total_fields = len(products[0])
            avg_filled = sum(
                sum(1 for v in p.values() if v and v != 'N/A' and v != 'None')
                for p in products
            ) / len(products)
            percentage = (avg_filled / total_fields * 100)
            
            print(f"[STATS] Data Completeness: {avg_filled:.1f}/{total_fields} fields ({percentage:.1f}%)")
            print(f"{'='*100}\n")
    
    def save_to_json(self, products, filename='flipkart_products.json'):
        """Save products to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            print(f"[+] Products saved to {filename}")
        except Exception as e:
            print(f"[!] Error saving to JSON: {e}")


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        product_name = ' '.join(sys.argv[1:])
    else:
        product_name = input("Enter product name to search: ").strip()
    
    if not product_name:
        print("[!] Please provide a product name")
        return
    
    scraper = FlipkartScraper()
    products = scraper.search_products(product_name, max_results=20)
    
    scraper.print_products(products)
    
    if products:
        save = input("Save to JSON? (y/n): ").strip().lower()
        if save == 'y':
            filename = input("Filename (default: flipkart_products.json): ").strip()
            filename = filename if filename else 'flipkart_products.json'
            if not filename.endswith('.json'):
                filename += '.json'
            scraper.save_to_json(products, filename)


if __name__ == "__main__":
    main()

