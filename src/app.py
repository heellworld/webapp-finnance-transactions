import streamlit as st
from botocore.exceptions import ClientError
import boto3
import os
from dotenv import load_dotenv
import uuid

# Load biến môi trường từ file .env
load_dotenv()

# Cấu hình thông tin AWS
AWS_REGION = os.getenv('region')
AGENT_ID = os.getenv('agentId')
AGENT_ALIAS_ID = os.getenv('agentAliasId')

# Initialize Bedrock Agent client
agents_runtime_client = boto3.client(
    'bedrock-agent-runtime',
    region_name=AWS_REGION
)

def invoke_agent(agents_runtime_client, agent_id, agent_alias_id, session_id, prompt):
    try:
        # Gọi Bedrock Agent API
        response = agents_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=prompt,
        )

        completion = ""
        # Đọc kết quả từ EventStream
        for event in response["completion"]:
            chunk = event["chunk"]
            completion += chunk["bytes"].decode()

    except ClientError as e:
        st.error(f"Couldn't invoke agent. Error: {e}")
        raise

    return completion

# App title
st.set_page_config(
    page_title="VCB BotAI",
    page_icon="D:\projects\chatbot-vietcombank-AWS\images\VCB_bot_logo.png"  # Thay bằng đường dẫn đúng
)
# Hiển thị tiêu đề kết hợp với logo
st.markdown(
    f"""
    <div style="display: flex; align-items: center;">
        <img src="https://cdn.haitrieu.com/wp-content/uploads/2022/02/Icon-Vietcombank.png" alt="Vietcombank Logo" style="width: 50px; margin-right: 10px;">
        <h1 style="display: inline;">Chat cùng VCB Bot AI 💬</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "Xin chào! Bạn cần tôi hỗ trợ gì?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
if prompt := st.chat_input(placeholder="Nhập tin nhắn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Đợi một lát..."):
            session_id = str(uuid.uuid4())  # Tạo session_id duy nhất
            try:
                response = invoke_agent(
                    agents_runtime_client=agents_runtime_client,
                    agent_id=AGENT_ID,
                    agent_alias_id=AGENT_ALIAS_ID,
                    session_id=session_id,
                    prompt=st.session_state.messages[-1]["content"]
                )
                st.write(response)
            except Exception as e:
                st.error(f"Lỗi khi gọi Bedrock Agent: {e}")
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
