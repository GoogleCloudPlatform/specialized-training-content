# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Part,
    Image
)
import streamlit as st
import re
import argparse
import PIL

parser = argparse.ArgumentParser(description='')
parser.add_argument('--project',required=True, help='Specify Google Cloud project')
parser.add_argument('--debug', action='store_true') # TODO: Add debug mode
parser.set_defaults(debug=False)

args = parser.parse_args()

# Function to initialize session state
def initialize_session_state():
    return vertexai.init(project=args.project)

# def _fix_streamlit_space(text: str) -> str:
#     """Fix silly streamlit issue where a newline needs 2 spaces before it.

#     See https://github.com/streamlit/streamlit/issues/868
#     """

#     def _replacement(match: re.Match):
#         # Check if the match is preceded by a space
#         if match.group(0).startswith(" "):
#             # If preceded by one space, add one more space
#             return " \n"
#         else:
#             # If not preceded by any space, add two spaces
#             return "  \n"

#     return re.sub(r"( ?)\n", _replacement, text)

# Main Streamlit app
def home():

    st.set_page_config(page_title="CoopBot - Powered by Gemini Pro", page_icon=":dog:")

    st.markdown("<h1 style='text-align: center;'>CoopBot - Powered by Gemini Pro</h1>", unsafe_allow_html=True)
    
    st.markdown("""**About me**: I am a virtual assistant, powered by Gemini and Streamlit, with the goal of help people learn the fundamentals of prompt design. I am named after the author's dog, who has all knowledge known to dogs about prompt design.""", unsafe_allow_html=False)

    # Initialize session state
    initialize_session_state()
    if 'uploader_key' not in st.session_state:
            st.session_state['uploader_key'] = 0 

    st.session_state['uploaded_files'] = st.file_uploader("Upload Image",
                                                          type=["jpg", "jpeg", "png"],
                                                          accept_multiple_files=True,
                                                          key=st.session_state['uploader_key'])    
    
    model = 'gemini-pro-vision' 
    
    text_input = st.text_input("Enter your Prompt:", value="Describe this image.")
    prompt = f"Please return all responses in Markdown. \n\n {text_input}"

    col1, col2, _= st.columns([1.5,1.5,2])
    with col1:
        submit_button = st.button("Submit Prompt", key="submit")
    with col2:
        clear_button = st.button("Clear Uploaded Images", key="clear")

    if clear_button:
        st.session_state['uploader_key'] += 1
        st.rerun()

    # Set up the model configuration options
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
    top_p = st.sidebar.number_input("Top P", 0.0, 1.0, 1.0, 0.1)
    top_k = st.sidebar.number_input("Top K", 1, 100, 1)
    max_output_tokens = st.sidebar.number_input("Max Output Tokens", 1, 5000, 2048)

    # Set up the model
    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_output_tokens": max_output_tokens,
    }
        
    gemini = GenerativeModel(model_name=model)

    if len(st.session_state['uploaded_files']) > 0:
        if (prompt is not None) and (submit_button):

            content = []
            
            for uploaded_file in st.session_state['uploaded_files']:

                bytes_data = uploaded_file.getvalue()
                content.append(Part.from_image(Image.from_bytes(bytes_data)))


            content.append(prompt)  

            response = gemini.generate_content(
                content,
                generation_config=generation_config,
                stream=False)
                   
            st.subheader("Response:")
            data_str = str(response.candidates[0])
                    
            # Use regular expressions to extract the text part
            match = re.search(r'text: "(.*?)"', data_str)
            if match:
                extracted_text = match.group(1)
                for item in extracted_text.split("\\n"):
                    st.write(item)


            st.subheader("Image:")

            for uploaded_file in st.session_state['uploaded_files']:
                st.image(PIL.Image.open(uploaded_file),
                        caption="Uploaded Image.",
                        width=800)            
   
# Run the Streamlit app
if __name__ == "__main__":
    home()