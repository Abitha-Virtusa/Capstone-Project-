"""
Streamlit Web Interface for Smart Product Scraper!!!
Compare products from Amazon and Flipkart simultaneously and helps to analyse the differences via 
visualizations and u can able to download the data in JSON and CSV format, and 
u can also view it in tabular format.
"""

import streamlit as st
import pandas as pd
import json
import time
from amazon import AmazonScraperFinal
from flipkart import FlipkartScraper
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="Smart Product Scraper",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; text-align: center; color: #1f77b4; margin-bottom: 1rem; }
    .platform-header { font-size: 1.5rem; font-weight: bold; padding: 0.5rem; border-radius: 5px; margin-bottom: 1rem; }
    .amazon-header { background-color: #ff9900; color: white; }
    .flipkart-header { background-color: #2874f0; color: white; }
    .product-card { border: 2px solid #ddd; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background-color: #f9f9f9; }
    .product-box {
    display: flex;
    flex-direction: row;
    gap: 20px;
    padding: 15px;
    background: #f8f8f8;
    border-radius: 10px;
    border: 1px solid #ddd;
    margin-bottom: 20px;
}
    
    .product-img-box {
        width: 180px;
        height: 180px;
        border-radius: 10px;
        background: #fff;
        padding: 5px;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .product-img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    .details-box {
        flex: 1;
        padding: 10px;
        font-size: 15px;
        line-height: 1.5;
    }

</style>
""", unsafe_allow_html=True)

# --------------------------
# Helper parsing functions
# --------------------------
def robust_get_image(p: dict):
    """Return the first found image url from common keys or None."""
    if not isinstance(p, dict):
        return None
    for key in ("image", "image_url", "img", "thumbnail", "image_src", "imageLink"):
        v = p.get(key)
        if v and isinstance(v, str) and v.strip() and v.strip().lower() not in ("n/a", "none"):
            return v.strip()
    return None

def robust_get_url(p: dict):
    """Return the best product URL from common keys or None."""
    if not isinstance(p, dict):
        return None
    for key in ("url", "product_url", "link", "productLink", "product_link"):
        v = p.get(key)
        if v and isinstance(v, str) and v.strip() and v.strip().lower() not in ("n/a", "none"):
            return v.strip()
    return None

def parse_price_to_number(price_str):
    """Extract float price from common formats like '₹1,299', '$29.99' or '1,299'."""
    if not price_str:
        return None
    try:
        s = str(price_str)
        # remove currency words/symbols
        for sym in ("₹", "Rs.", "Rs", "INR", "$", "USD", "₹", "€", "£"):
            s = s.replace(sym, "")
        # remove commas and extra spaces
        s = s.replace(",", "").strip()
        # take first numeric token
        tokens = s.split()
        if not tokens:
            return None
        # tokens may contain things like '1,299' or '29.99' or 'From 299'
        for t in tokens:
            cleaned = "".join(ch for ch in t if ch.isdigit() or ch == "." or ch == "-")
            if cleaned and any(ch.isdigit() for ch in cleaned):
                try:
                    return float(cleaned)
                except:
                    continue
        # last fallback
        return float(''.join(ch for ch in s if ch.isdigit() or ch == ".")) if any(ch.isdigit() for ch in s) else None
    except Exception:
        return None

def parse_rating_to_number(rating_str):
    """Extract float rating from formats like '4.7 out of 5 stars' or '4.1'."""
    if not rating_str:
        return None
    try:
        s = str(rating_str).strip()
        # first try first token
        tokens = s.split()
        for t in tokens:
            cleaned = "".join(ch for ch in t if ch.isdigit() or ch == ".")
            if cleaned and any(ch.isdigit() for ch in cleaned):
                try:
                    return float(cleaned)
                except:
                    continue
        # fallback: scan characters
        cleaned = "".join(ch for ch in s if ch.isdigit() or ch == ".")
        if cleaned:
            return float(cleaned)
        return None
    except Exception:
        return None

# Session State
if 'amazon_products' not in st.session_state:
    st.session_state.amazon_products = None
if 'flipkart_products' not in st.session_state:
    st.session_state.flipkart_products = None
if 'search_done' not in st.session_state:
    st.session_state.search_done = False

# Header
st.markdown('<div class="main-header">🛒 SMART PRODUCT SCRAPER</div>', unsafe_allow_html=True)
st.markdown("### Easily analyze and compare products between Amazon and Flipkart")

# Sidebar
with st.sidebar:
    st.header("⚙️ Query Configuration")
    search_query = st.text_input("Product Name", placeholder="e.g., laptop, bottle, headphones")
    max_results = st.slider("Results per Platform", 1, 100, 5)

    st.markdown("---")
    st.subheader("🔧 Advanced Search Controls")

    max_retries = st.number_input("Max Retries", 1, 10, 5)
    retry_delay = st.number_input("Retry Delay (secs)", 1, 20, 5)

    st.markdown("---")
    search_button = st.button("🔍 Search Products", use_container_width=True)

    if search_button:
        if not search_query:
            st.error("Please enter a product name!")
        else:
            st.session_state.search_done = False
            st.session_state.amazon_products = None
            st.session_state.flipkart_products = None

# Run scraping
if search_button and search_query:
    st.markdown("---")
    col1, col2 = st.columns(2)

    # AMAZON SCRAPE
    with col1:
        st.markdown('<div class="platform-header amazon-header">AMAZON</div>', unsafe_allow_html=True)
        amazon_status = st.empty()
        amazon_progress = st.progress(0)
        try:
            amazon_status.info("Starting Amazon scraper...")
            amazon_progress.progress(20)
            scraper = AmazonScraperFinal()
            amazon_status.info("Searching Amazon...")
            amazon_products = scraper.search_products(
                search_query,
                max_results=max_results,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            amazon_progress.progress(100)
            st.session_state.amazon_products = amazon_products
            amazon_status.success(f"Found {len(amazon_products)} items")
        except Exception as e:
            amazon_status.error(str(e))
            st.session_state.amazon_products = []

    # FLIPKART SCRAPE
    with col2:
        st.markdown('<div class="platform-header flipkart-header">FLIPKART</div>', unsafe_allow_html=True)
        flip_status = st.empty()
        flip_progress = st.progress(0)
        try:
            flip_status.info("Starting Flipkart scraper...")
            flip_progress.progress(20)
            scraper = FlipkartScraper()
            flipkart_products = scraper.search_products(
                search_query,
                max_results=max_results,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            flip_progress.progress(100)
            st.session_state.flipkart_products = flipkart_products
            flip_status.success(f"Found {len(flipkart_products)} items")
        except Exception as e:
            flip_status.error(str(e))
            st.session_state.flipkart_products = []

    st.session_state.search_done = True

# RESULTS
if st.session_state.search_done:
    amazon_products = st.session_state.amazon_products or []
    flipkart_products = st.session_state.flipkart_products or []

    st.markdown("## 📊 Product Comparison Results")

    tab1, tab2, tab3, tab4 = st.tabs(["📱 Side-by-Side View", "📊 Table", "📈 Analytics", "💾 Download"])

    # ---------------------------------------------------------
    # TAB 1 → SIDE-BY-SIDE VIEW WITH IMAGES + DETAILS
    # ---------------------------------------------------------
    
    
    with tab1:
        max_items = max(len(amazon_products), len(flipkart_products))

        if max_items == 0:
            st.info("No results yet. Search for a product to see side-by-side comparison.")

        for i in range(max_items):

            st.markdown("## 🔍 Product #" + str(i+1))
            col_left, col_right = st.columns(2, gap="large")

            # ========================= AMAZON =========================
            with col_left:
                st.markdown('<div class="platform-header amazon-header">Amazon</div>', unsafe_allow_html=True)

                if i < len(amazon_products):
                    p = amazon_products[i] if isinstance(amazon_products, list) else amazon_products.iloc[i].to_dict()

                    # FIX: Extract image robustly
                    img_url = robust_get_image(p)

                    # Additional strict fallback for Amazon
                    if not img_url:
                        img_url = p.get("image_high_res") or p.get("img") or p.get("imageLinks")

                    if isinstance(img_url, list):
                        img_url = img_url[0]

                    # Normalize URL
                    if img_url:
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif not img_url.startswith("http"):
                            img_url = "https://" + img_url

                    # IMAGE
                    if img_url:
                        try:
                            st.image(img_url, width=180)
                        except:
                            st.image("https://via.placeholder.com/150?text=Image+Error", width=150)
                    else:
                        st.image("https://via.placeholder.com/150?text=No+Image", width=150)

                    # DETAILS
                    st.write(f"**Name:** {p.get('name')}")
                    st.write(f"**Price:** {p.get('price')}")
                    st.write(f"**Rating:** {p.get('rating')}")
                    st.write(f"**Brand:** {p.get('brand')}")

                    product_url = robust_get_url(p)
                    if product_url:
                        st.markdown(f"[🔗 View on Amazon]({product_url})")

                else:
                    st.info("No Amazon product found")

            # ========================= FLIPKART =========================
            with col_right:
                st.markdown('<div class="platform-header flipkart-header">Flipkart</div>', unsafe_allow_html=True)

                if i < len(flipkart_products):
                    p = flipkart_products[i] if isinstance(flipkart_products, list) else flipkart_products.iloc[i].to_dict()

                    img_url = robust_get_image(p)
                    if img_url:
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                    if img_url:
                        st.image(img_url, width=180)
                    else:
                        st.image("https://via.placeholder.com/150?text=No+Image", width=150)

                    st.write(f"**Name:** {p.get('name')}")
                    st.write(f"**Price:** {p.get('price')}")
                    st.write(f"**Rating:** {p.get('rating')}")
                    st.write(f"**Brand:** {p.get('brand')}")

                    product_url = robust_get_url(p)
                    if product_url:
                        st.markdown(f"[🔗 View on Flipkart]({product_url})")
                else:
                    st.info("No Flipkart product found")

            st.markdown("---")


    # ---------------------------------------------------------
    # TAB 2 → TABLE
    # ---------------------------------------------------------
    with tab2:
        if amazon_products:
            st.subheader("Amazon")
            try:
                st.dataframe(pd.DataFrame(amazon_products), use_container_width=True)
            except:
                st.write(amazon_products)
        else:
            st.info("No Amazon results")

        if flipkart_products:
            st.subheader("Flipkart")
            try:
                st.dataframe(pd.DataFrame(flipkart_products), use_container_width=True)
            except:
                st.write(flipkart_products)
        else:
            st.info("No Flipkart results")

    # ---------------------------------------------------------
    # TAB 3 → ANALYTICS (4 simple charts)
    # ---------------------------------------------------------
    with tab3:
        st.subheader("📈 Analytics & Charts")

        # Prepare price lists robustly
        def collect_prices(data):
            vals = []
            for p in data:
                # handle DataFrame rows
                if not isinstance(p, dict):
                    try:
                        p = dict(p)
                    except:
                        continue
                raw_price = p.get('price') or p.get('Price') or ""
                num = parse_price_to_number(raw_price)
                if num is not None:
                    vals.append(num)
            return vals

        amazon_prices = collect_prices(amazon_products)
        flipkart_prices = collect_prices(flipkart_products)

        # Chart 1: Average Price
        st.markdown("### 1️⃣ Average Price Comparison")
        avg_am = round(sum(amazon_prices)/len(amazon_prices), 2) if amazon_prices else 0
        avg_fk = round(sum(flipkart_prices)/len(flipkart_prices), 2) if flipkart_prices else 0
        df_avg = pd.DataFrame({"Platform": ["Amazon", "Flipkart"], "Avg Price": [avg_am, avg_fk]})
        st.plotly_chart(px.bar(df_avg, x="Platform", y="Avg Price", color="Platform", title="Average Price"), use_container_width=True)

        # Chart 2: Price Distribution (histogram)
        st.markdown("### 2️⃣ Price Distribution")
        df_dist = pd.DataFrame({
            "Price": amazon_prices + flipkart_prices,
            "Platform": ["Amazon"]*len(amazon_prices) + ["Flipkart"]*len(flipkart_prices)
        })
        if not df_dist.empty:
            st.plotly_chart(px.histogram(df_dist, x="Price", color="Platform", nbins=12, title="Price Distribution"), use_container_width=True)
        else:
            st.info("No price data available for distribution chart.")

        # Chart 3: Brand distribution (top brands)
        st.markdown("### 3️⃣ Brand Distribution")
        def brand_counts(products, top_n=10):
            brands = []
            for p in products:
                if not isinstance(p, dict):
                    try:
                        p = dict(p)
                    except:
                        continue
                brands.append((p.get('brand') or p.get('Brand') or "Unknown"))
            s = pd.Series(brands)
            if s.empty:
                return pd.DataFrame()
            top = s.value_counts().nlargest(top_n).reset_index()
            top.columns = ["Brand", "Count"]
            return top

        top_am = brand_counts(amazon_products, top_n=8)
        top_fk = brand_counts(flipkart_products, top_n=8)

        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown("#### Amazon - Top Brands")
            if not top_am.empty:
                st.plotly_chart(px.bar(top_am, x="Brand", y="Count", title="Amazon Top Brands"), use_container_width=True)
            else:
                st.info("No Amazon brand data")
        with bc2:
            st.markdown("#### Flipkart - Top Brands")
            if not top_fk.empty:
                st.plotly_chart(px.bar(top_fk, x="Brand", y="Count", title="Flipkart Top Brands"), use_container_width=True)
            else:
                st.info("No Flipkart brand data")

        # Chart 4: Ratings distribution (pie)
        st.markdown("### 4️⃣ Ratings Distribution")
        def rating_counts(products):
            labels = []
            for p in products:
                if not isinstance(p, dict):
                    try:
                        p = dict(p)
                    except:
                        continue
                raw = p.get('rating') or p.get('Rating') or ""
                num = parse_rating_to_number(raw)
                if num is not None:
                    # bucket to one decimal
                    labels.append(str(round(num, 1)))
            if not labels:
                return pd.DataFrame()
            s = pd.Series(labels)
            dfc = s.value_counts().reset_index()
            dfc.columns = ["Rating", "Count"]
            return dfc

        ar = rating_counts(amazon_products)
        fr = rating_counts(flipkart_products)

        r1, r2 = st.columns(2)
        with r1:
            st.markdown("#### Amazon Ratings")
            if not ar.empty:
                fig = px.pie(ar, names='Rating', values='Count', title='Amazon Ratings', hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No Amazon rating data")
        with r2:
            st.markdown("#### Flipkart Ratings")
            if not fr.empty:
                fig = px.pie(fr, names='Rating', values='Count', title='Flipkart Ratings', hole=0.3)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No Flipkart rating data")

    # ---------------------------------------------------------
    # TAB 4 → DOWNLOAD (page stays in same tab)
    # ---------------------------------------------------------
    with tab4:
        st.subheader("Export Results")
        amazon_products = st.session_state.get("amazon_products") or []
        flipkart_products = st.session_state.get("flipkart_products") or []

        def download_buttons(products, prefix):
            if not products:
                st.info(f"No {prefix} data to download.")
                return
            json_str = json.dumps(products, indent=2, ensure_ascii=False)
            st.download_button(label=f"Download {prefix} JSON",
                               data=json_str,
                               file_name=f"{prefix.lower()}_products.json",
                               mime="application/json",
                               key=f"{prefix}_json_dl")
            try:
                df = pd.DataFrame(products)
                csv = df.to_csv(index=False)
                st.download_button(label=f"Download {prefix} CSV",
                                   data=csv,
                                   file_name=f"{prefix.lower()}_products.csv",
                                   mime="text/csv",
                                   key=f"{prefix}_csv_dl")
            except Exception as e:
                st.error(f"Could not prepare CSV: {e}")

        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### Amazon")
            download_buttons(amazon_products, "Amazon")
        with colB:
            st.markdown("#### Flipkart")
            download_buttons(flipkart_products, "Flipkart")

st.markdown("---")
st.markdown("<center>Built for Professional E-Commerce Analysis</center>", unsafe_allow_html=True)
