import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Page Configuration
st.set_page_config(
    page_title="PragyanAI - RAG Code Assistant Bot",
    page_icon="💬",
    layout="wide"
)

st.title("PragyanAI - RAG AI Code Intelligence Bot")
st.markdown(
    "Ask detailed questions, request line-by-line code walkthroughs, or query specific architectural behaviors "
    "of your active Verilog design and testbench context."
)

# -----------------------------------------------------------------------------
# API Key Setup
# -----------------------------------------------------------------------------
api_key = None
try:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = st.session_state.get("GROQ_API_KEY", "")

if not api_key:
    api_key = st.text_input("Enter your Groq API Key:", type="password")
    if api_key:
        st.session_state["GROQ_API_KEY"] = api_key
    else:
        st.warning("⚠️ Please provide a Groq API key in Streamlit secrets or input it above to proceed.")
        st.stop()

# Initialize LLM
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=api_key)

# -----------------------------------------------------------------------------
# Retrieve Current Code Context (RTL + Testbench)
# -----------------------------------------------------------------------------
rtl_context = st.session_state.get(
    "rtl_final", 
    "// No active Verilog design found. Please run the Multi-Agent Pipeline first."
)
tb_context = st.session_state.get(
    "testbench_code", 
    "// No active testbench found."
)

combined_code_context = f"--- VERILOG RTL DESIGN (design.v) ---\n{rtl_context}\n\n--- VERILOG TESTBENCH (test_bench.v) ---\n{tb_context}"

with st.expander("🔍 View Active Verilog Code Context (RAG Knowledge Base)"):
    st.code(combined_code_context, language="verilog")

# -----------------------------------------------------------------------------
# Chat History Management
# -----------------------------------------------------------------------------
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant", 
            "content": "Hello! I am your PragyanAI RAG Verilog Assistant. Ask me anything about your current code architecture, logic blocks, testbench scenarios, or how to optimize it."
        }
    ]

# Render chat messages
for msg in st.session_state["chat_messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------------------------------------------------------
# User Input & RAG Generation Loop
# -----------------------------------------------------------------------------
user_query = st.chat_input("Ask a question about your Verilog code...")

if user_query:
    # Append user message
    st.session_state["chat_messages"].append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.spinner("Analyzing code context and formulating explanation..."):
        rag_system_prompt = (
            "You are an expert Verilog RAG Assistant and Hardware Architect. Use the provided Verilog code context "
            "as your ground truth source to answer user questions accurately. Explain syntax, state machines, timing, "
            "test coverage, and logic flows thoroughly.\n\n"
            f"Verilog Code Context:\n{combined_code_context}"
        )
        
        # Build message payload for LLM invocation keeping context secure
        try:
            response = llm.invoke([SystemMessage(content=rag_system_prompt)] + [HumanMessage(content=user_query)])
            bot_reply = response.content
        except Exception as e:
            bot_reply = f"❌ Error communicating with LLM service: {e}"

        # Append assistant reply
        st.session_state["chat_messages"].append({"role": "assistant", "content": bot_reply})
        st.chat_message("assistant").write(bot_reply)
