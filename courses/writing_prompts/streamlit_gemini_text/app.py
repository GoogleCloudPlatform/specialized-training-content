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

import streamlit as st
import vertexai
import argparse
from vertexai.generative_models import GenerativeModel
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts.prompt import PromptTemplate
from typing import Any, List, Mapping, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM
from vertexai.preview.generative_models import GenerativeModel

class GeminiProLLM(LLM):
    @property
    def _llm_type(self) -> str:
        return "gemini-pro"

    def _call(self,
              prompt: str,
              stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] = None,
              **kwargs: Any,) -> str:

        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")
        
        gemini_pro_model = GenerativeModel("gemini-1.5-pro")
        
        model_response = gemini_pro_model.generate_content(
            prompt, 
            generation_config={"temperature": temperature,
                               "top_p": top_p,
                               "top_k": top_k,
                               "max_output_tokens": max_output_tokens}
        )
        print(model_response)

        if len(model_response.candidates[0].content.parts) > 0:
            return model_response.candidates[0].content.parts[0].text
        else:
            return "<No answer given by Gemini Pro>"

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"model_id": "gemini-1.5-pro", "temperature": 0.0}
    

parser = argparse.ArgumentParser(description='')
parser.add_argument('--project',required=True, help='Specify Google Cloud project')
parser.add_argument('--debug', action='store_true') # TODO: Add debug mode
parser.set_defaults(debug=False)

args = parser.parse_args()

# Initialize Vertex AI
vertexai.init(project=args.project)

# Setting page title and header
st.set_page_config(page_title="CoopBot - Powered by Gemini Pro", page_icon=":dog:",
                   initial_sidebar_state="collapsed")

st.markdown("<h1 style='text-align: center;'>CoopBot - Powered by Gemini Pro</h1>", unsafe_allow_html=True)

template = """
    You are a chatbot named CoopBot whose role is to help students understand principles of prompt design when working with Gemini Pro. You should keep a friendly and light tone, and not use complex language when it can be avoided. Keep responses brief and to the point.

    If you are not asked to analyze a prompt, then please return just the output for the prompt. Do not analyze the prompt unless you are specfially asked to.

    A well-written prompt should contain three main components: The *task* to be performed, *context* to give contextual information for completing the task. Finally there should be *examples* to show how the task should be accomplished.

    If you are asked to analyze a prompt, break the prompt into the components discussed above and the return the output at the end. If any of the components are missing, then please inform the user of this. You should also give suggestions on how to improve the prompt based on best practices of prompt design for Gemini. This response should be less than 300 words.
    
    \n\nCurrent conversation:\n{history}\nHuman: {input} \nAI:
"""


st.sidebar.title("Options")
clear_button = st.sidebar.button("Clear Conversation", key="clear")

temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
top_p = st.sidebar.slider("Top P", 0.0, 1.0, 0.95, 0.05)
top_k = st.sidebar.number_input("Top K", 1, 100, 20)
max_output_tokens = st.sidebar.number_input("Max Output Tokens", 1, 2048, 100)

# Load chat model
@st.cache_resource
def load_chain():
    llm = GeminiProLLM()
    memory = ConversationBufferMemory()
    chain = ConversationChain(llm=llm, memory=memory,
                               prompt=PromptTemplate(input_variables=['history', 'input'],      
                                                     template=template))
    return chain

chatchain = load_chain()

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.markdown("""**About me**: I am a virtual assistant, powered by Gemini and Streamlit, with the goal of help people learn the fundamentals of prompt design. I am named after the author's dog, who has all knowledge known to dogs about prompt design.""", unsafe_allow_html=False)

# Reset conversation
if clear_button:
    st.session_state['messages'] = []
    chatchain = load_chain()

# Display previous messages
for message in st.session_state['messages']:
    role = message["role"]
    content = message["content"]
    with st.chat_message(role):
        st.markdown(content)

# Chat input
prompt = st.chat_input("You:")
if prompt:
    # For these exercises, we do not want to use previous inputs for context.
    st.session_state['messages'] = [{"role": "user", "content": prompt}]
    with st.chat_message("user"):
        st.markdown(prompt)

    response = chatchain(prompt)["response"]
    st.session_state['messages'].append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)