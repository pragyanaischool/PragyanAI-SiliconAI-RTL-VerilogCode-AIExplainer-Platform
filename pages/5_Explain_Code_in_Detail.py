import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Page Configuration
st.set_page_config(
    page_title="PragyanAI - Explain Code in Detail",
    page_icon="📖",
    layout="wide"
)
try:
    st.image("PragyanAI_Transperent.png", width=300)
except Exception:
    pass
st.title("PragyanAI - Deep-Dive Code Explainer & Test Coverage Analyzer")
st.markdown(
    "Analyze your active Verilog design and testbench. Choose your target audience level, "
    "select from professional engineering prompts, and get a comprehensive architectural breakdown and verification coverage report."
)

# -----------------------------------------------------------------------------
# API Key Setup
# -----------------------------------------------------------------------------
api_key = st.secrets.get("GROQ_API_KEY", st.session_state.get("GROQ_API_KEY", ""))
if not api_key:
    api_key = st.text_input("Enter your Groq API Key:", type="password")
    if api_key:
        st.session_state["GROQ_API_KEY"] = api_key
    else:
        st.warning("⚠️ Please provide a Groq API key to proceed.")
        st.stop()

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=api_key)

# -----------------------------------------------------------------------------
# Retrieve Context
# -----------------------------------------------------------------------------
rtl_context = st.session_state.get(
    "rtl_final", 
    "// No active RTL code found. Please generate code in the pipeline or multi-variant studio first."
)
tb_context = st.session_state.get(
    "testbench_code", 
    "// No active testbench code found."
)

with st.expander("🔍 View Active Source Code Context"):
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("**Verilog RTL Design (`design.v`)**")
        st.code(rtl_context, language="verilog")
    with col_c2:
        st.markdown("**Testbench (`test_bench.v`)**")
        st.code(tb_context, language="verilog")

st.markdown("---")

# -----------------------------------------------------------------------------
# Configuration Controls (Audience & Prompt Presets)
# -----------------------------------------------------------------------------
col_opt1, col_opt2 = st.columns(2)

with col_opt1:
    audience_level = st.selectbox(
        "Select Target Audience Level:",
        [
            "Beginner / Student (Focus on fundamentals, syntax basics, and signal definitions)",
            "Expert / ASIC Engineer (Focus on timing constraints, clock domains, area/power metrics, and race conditions)"
        ]
    )

with col_opt2:
    analysis_mode = st.selectbox(
        "Select Question Preset / Focus Area:",
        [
            "Comprehensive Line-by-Line Code Walkthrough",
            "Testbench Scenario Coverage & Verification Scope Analysis",
            "Clock Domain, Reset Handling & Potential Hazard Analysis",
            "Custom Technical Question (Type below)"
        ]
    )

custom_question = ""
if analysis_mode == "Custom Technical Question (Type below)":
    custom_question = st.text_input("Enter your specific technical question about the code:")

analyze_btn = st.button("🔬 Generate Detailed Explanation & Coverage Report", type="primary")

# -----------------------------------------------------------------------------
# Explanation Generation Logic
# -----------------------------------------------------------------------------
if analyze_btn:
    with st.spinner("Analyzing code architecture and test scenarios..."):
        
        system_persona = (
            f"You are a Principal Hardware Architecture Professor and Senior Verification Lead. "
            f"Explain the provided Verilog RTL design and testbench tailored specifically for a **{audience_level}**. "
            "Structure your response clearly using markdown headings, bold terms, and code references."
        )
        
        user_prompt_content = (
            f"Focus Area / Objective: {analysis_mode}\n"
            f"Custom Details: {custom_question}\n\n"
            f"Verilog RTL Code:\n{rtl_context}\n\n"
            f"Testbench Code:\n{tb_context}\n\n"
            "Provide a rigorous, detailed breakdown covering:\n"
            "1. **Core Architectural Summary**\n"
            "2. **Line-by-Line Logic Breakdown**\n"
            "3. **Testbench Scenario Coverage & Verification Scope** (What states, stimulus edges, and edge cases are tested)"
        )

        try:
            response = llm.invoke([
                SystemMessage(content=system_persona),
                HumanMessage(content=user_prompt_content)
            ])
            
            st.markdown("---")
            st.subheader("📊 Detailed Explanation & Test Coverage Report")
            st.markdown(response.content)
            
        except Exception as e:
            st.error(f"Failed to generate explanation: {e}")
