# Smart Product Scraper 
# Objective
The Smart Product Scraper is a Python and Streamlit-powered tool that automatically extracts rich product information from Amazon and Flipkart, including prices, discounts, ratings, reviews, brand details, images, specifications, and platform-specific tags. The interface offers a clear side-by-side comparison view, an organized table-based display, and interactive data visualizations to help users analyze differences effortlessly. It also provides flexible JSON and CSV download options, making it easy to save, compare, and reuse the collected product data.

# Available Scrapers
1. Amazon Scraper ('amazon.py')
Extracts product data from Amazon.com

2. Flipkart Scraper ('flipkart.py')
Extracts product data from Flipkart.com (India)

# Common Fields (19 fields):
- Product Name - Full product title
- Product ID/ASIN - Unique identifier
- URL - Direct product link (100% success rate)
- Price - Current price
- Original Price - MRP/Previous price
- Discount - Discount percentage
- Rating - Customer rating
- Number of Reviews - Review/rating count
- Brand - Product brand
- Image URL - Product image
- Delivery Info - Shipping details
- Availability - Stock status
- Highlights/Specifications - Key features

# Technical Details

Built With:
- **requests** - HTTP requests
- **BeautifulSoup4 + lxml** - HTML parsing
- **fake-useragent** - Rotating user agents for anti-bot evasion

# Extraction Techniques:
1. **Multiple CSS Selectors** - 3-4 fallback selectors per field
2. **Regex Pattern Matching** - Extracts data when selectors fail
3. **Text Analysis** - Searches full text for patterns
4. **Attribute Mining** - Extracts from HTML attributes (data-*, aria-*)

# Anti-Scraping Measures

Both platforms have bot detection. If blocked:

1. **Wait 10-15 minutes** before retrying
2. **Use a VPN** or different IP address
3. **Reduce request frequency** 
4. **Check robots.txt** to ensure compliance

# Project Structure
'''
Capstone project/
├── amazon.py              # Amazon scraper (16KB)
├── flipkart.py            # Flipkart scraper (24KB)
├── requirements.txt       # Dependencies
├── README.md              # This file
└── app1.py                # UI streamlit main file
'''
