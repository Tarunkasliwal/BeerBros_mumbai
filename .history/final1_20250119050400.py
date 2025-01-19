import streamlit as st
import json
import requests
from typing import Optional

# Constants
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "e889a07c-43c2-42ff-ab2a-375f6f7540b3"
FLOW_ID = "51a07a7b-d922-42c6-809f-4755f23d200d"
APPLICATION_TOKEN = "AstraCS:xsUNsdDvnURyQNmceRHQpJhG:1a244f2ba1c7ff76071f0a016ec73644190ec5d08c2ecd51eb3ba2900e692565"

def run_flow(
    message: str,
    endpoint: str,
    application_token: str
) -> dict:
    """Run the ad generation flow with the given message."""
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{endpoint}"
    
    # Construct the prompt for ad generation
    prompt = f"""Generate a compelling advertisement for the following product/service: {message}

Please include:
- Attention-grabbing headline
- Main benefits and features
- Call to action
- Tone: Professional and engaging"""

    payload = {
        "input_value": prompt,
        "input_type": "text",
        "output_type": "text"
    }
    
    headers = {
        "Authorization": f"Bearer {application_token}",
        "Content-Type": "application/json"
    }
    
    try:
        with st.spinner("Generating your ad..."):
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def main():
    st.set_page_config(
        page_title="AI Ad Generator",
        page_icon="🎯",
        layout="wide"
    )

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .output-container {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🎯 AI Ad Generator")
    st.markdown("Transform your product ideas into compelling advertisements!")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        custom_endpoint = st.text_input("API Endpoint", value=FLOW_ID)
        custom_token = st.text_input("API Token", value=APPLICATION_TOKEN, type="password")
        
        st.markdown("### 📝 Ad Preferences")
        target_audience = st.selectbox(
            "Target Audience",
            ["General", "Business Professionals", "Young Adults", "Parents", "Seniors"]
        )
        
        ad_tone = st.selectbox(
            "Tone of Voice",
            ["Professional", "Casual", "Humorous", "Luxury", "Educational"]
        )
        
        platform = st.selectbox(
            "Platform",
            ["Social Media", "Website", "Email", "Print", "Video Script"]
        )

    # Main content area
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("Product/Service Details")
        product_name = st.text_input("Product/Service Name")
        product_description = st.text_area(
            "Description",
            placeholder="Enter key features, benefits, and unique selling points..."
        )
        key_benefits = st.text_area(
            "Key Benefits",
            placeholder="List the main benefits, one per line..."
        )

    # Construct the detailed prompt
    if st.button("Generate Ad", type="primary"):
        if not product_name or not product_description:
            st.warning("Please fill in both the product name and description.")
            return

        detailed_prompt = f"""
Product: {product_name}
Description: {product_description}
Key Benefits: {key_benefits}
Target Audience: {target_audience}
Tone: {ad_tone}
Platform: {platform}

Generate a compelling advertisement that includes:
1. An attention-grabbing headline
2. Engaging body copy highlighting the benefits
3. A strong call to action
4. Appropriate tone and style for {platform}
"""

        response = run_flow(
            message=detailed_prompt,
            endpoint=custom_endpoint,
            application_token=custom_token
        )

        if response and 'messages' in response and response['messages']:
            ad_content = response['messages'][0].get('message', '')
            
            with col2:
                st.subheader("Generated Advertisement")
                with st.container():
                    st.markdown("""
                        <div class="output-container">
                            <h3>Your Advertisement</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown(ad_content)
                    
                    # Export options
                    st.download_button(
                        label="Download Ad Copy",
                        data=ad_content,
                        file_name=f"ad_{product_name.lower().replace(' ', '_')}.txt",
                        mime="text/plain"
                    )
        else:
            st.error("Could not generate ad. Please check your API configuration and try again.")

    # Usage tips
    with st.expander("📌 Tips for Better Results"):
        st.markdown("""
        - Be specific about your product's unique features
        - Include clear target audience demographics
        - Mention specific pain points your product solves
        - Add quantifiable benefits where possible
        - Consider including price points or special offers
        """)

if __name__ == "__main__":
    main()