import streamlit as st
import json
import requests
from typing import Optional
import warnings

try:
    from langflow.load import upload_file
except ImportError:
    warnings.warn("Langflow provides a function to help you upload files to the flow. Please install langflow to use it.")
    upload_file = None

# Constants
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "e889a07c-43c2-42ff-ab2a-375f6f7540b3"
FLOW_ID = "51a07a7b-d922-42c6-809f-4755f23d200d"
APPLICATION_TOKEN = "AstraCS:xsUNsdDvnURyQNmceRHQpJhG:1a244f2ba1c7ff76071f0a016ec73644190ec5d08c2ecd51eb3ba2900e692565"
DEFAULT_TWEAKS = {
    "ChatInput-SnYiF": {},
    "ChatOutput-o0NcW": {},
    "GroqModel-xbFdE": {}
}

def run_flow(
    message: str,
    endpoint: str,
    output_type: str = "chat",
    input_type: str = "chat",
    tweaks: Optional[dict] = None,
    application_token: Optional[str] = None
) -> dict:
    """Run a flow with a given message and optional tweaks."""
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{endpoint}"
    payload = {
        "input_value": message,
        "output_type": output_type,
        "input_type": input_type,
    }
    headers = None
    
    if tweaks:
        payload["tweaks"] = tweaks
    if application_token:
        headers = {"Authorization": "Bearer " + application_token, "Content-Type": "application/json"}
    
    with st.spinner("Processing your request..."):
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            st.error(f"Error: Failed to get a valid response. Status Code: {response.status_code}")
            st.code(response.text, language="json")
            return None
        
        return response.json()

def main():
    st.title("Langflow API Interface")
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # API Configuration
    with st.sidebar.expander("API Settings", expanded=False):
        custom_endpoint = st.text_input("Endpoint", value=FLOW_ID)
        custom_token = st.text_input("Application Token", value=APPLICATION_TOKEN, type="password")
        input_type = st.selectbox("Input Type", ["chat", "text"], index=0)
        output_type = st.selectbox("Output Type", ["chat", "text"], index=0)
    
    # Tweaks Configuration
    with st.sidebar.expander("Tweaks Configuration", expanded=False):
        tweaks_str = st.text_area("Tweaks (JSON)", value=json.dumps(DEFAULT_TWEAKS, indent=2))
        try:
            tweaks = json.loads(tweaks_str)
        except json.JSONDecodeError:
            st.sidebar.error("Invalid JSON format for tweaks")
            tweaks = DEFAULT_TWEAKS
    
    # File Upload
    with st.sidebar.expander("File Upload", expanded=False):
        uploaded_file = st.file_uploader("Upload File")
        components = st.text_input("Components (comma-separated)")
        
        if uploaded_file and components and upload_file:
            try:
                # Save uploaded file temporarily
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                tweaks = upload_file(
                    file_path=tmp_file_path,
                    host=BASE_API_URL,
                    flow_id=custom_endpoint,
                    components=components.split(","),
                    tweaks=tweaks
                )
                os.unlink(tmp_file_path)  # Clean up temporary file
                st.sidebar.success("File uploaded and tweaks updated!")
            except Exception as e:
                st.sidebar.error(f"Error uploading file: {str(e)}")
    
    # Main chat interface
    st.subheader("Chat Interface")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What's your message?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from API
        response = run_flow(
            message=prompt,
            endpoint=custom_endpoint,
            output_type=output_type,
            input_type=input_type,
            tweaks=tweaks,
            application_token=custom_token
        )
        
        if response and 'messages' in response and response['messages']:
            assistant_message = response['messages'][0].get('message', '')
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            with st.chat_message("assistant"):
                st.markdown(assistant_message)
        else:
            with st.chat_message("assistant"):
                st.error("No valid response received from the API")
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()