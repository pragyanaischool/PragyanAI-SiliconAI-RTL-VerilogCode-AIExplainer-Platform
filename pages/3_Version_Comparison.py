import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Page Configuration
st.set_page_config(
    page_title="PragyanAI - Version Comparison & Delta Analysis",
    page_icon="🔀",
    layout="wide"
)

st.title("PragyanAI - Multi-Agent Version Selector & Delta Analysis")
st.markdown(
    "Compare the evolution of your Verilog code across different stages of the pipeline or variants. "
    "Select any two versions to compare side-by-side and let the AI analyze the structural changes and their engineering significance."
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
        st.warning("⚠️ Please provide a Groq API key to enable LLM delta analysis.")
        st.stop()

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=api_key)

# -----------------------------------------------------------------------------
# Gather Available Versions from Session State
# -----------------------------------------------------------------------------
available_versions = {}
if st.session_state.get("rtl_v1"):
    available_versions["Initial Generator Draft (v1)"] = st.session_state["rtl_v1"]
if st.session_state.get("rtl_final"):
    available_versions["Final Verified Production Version"] = st.session_state["rtl_final"]
if st.session_state.get("variant_perf"):
    available_versions["Performance Optimized Variant"] = st.session_state["variant_perf"]
if st.session_state.get("variant_area"):
    available_versions["Area Optimized Variant"] = st.session_state["variant_area"]
if st.session_state.get("variant_robust"):
    available_versions["Robust & Clean Variant"] = st.session_state["variant_robust"]

if not available_versions:
    st.warning("⚠️ No execution history or variants found in session state. Please run the **Multi-Agent Pipeline** or **Multi-Variant Studio** first.")
    if st.button("👉 Go to Multi-Agent Pipeline"):
        st.switch_page("pages/1_🤖_Multi_Agent_Pipeline.py")
    st.stop()

# -----------------------------------------------------------------------------
# View Layout Selection
# -----------------------------------------------------------------------------
comparison_mode = st.radio(
    "Choose Comparison View Mode:",
    ["Single Version Inspector", "Side-by-Side Comparison & AI Delta Analysis"],
    horizontal=True
)

st.markdown("---")

# -----------------------------------------------------------------------------
# Mode 1: Single Version Inspector
# -----------------------------------------------------------------------------
if comparison_mode == "Single Version Inspector":
    version_choice = st.selectbox(
        "Select Agent Version to Review:",
        list(available_versions.keys()) + (["Critic Agent Audit Notes"] if st.session_state.get("rtl_critic_notes") else [])
    )
    
    if version_choice == "Critic Agent Audit Notes":
        st.subheader("🧐 Critic Agent Audit & Recommendations")
        st.markdown(st.session_state.get("rtl_critic_notes", "*No critic notes recorded.*"))
    else:
        st.subheader(f"📂 Code View: {version_choice}")
        st.code(available_versions[version_choice], language="verilog")

# -----------------------------------------------------------------------------
# Mode 2: Side-by-Side Comparison & AI Delta Analysis
# -----------------------------------------------------------------------------
else:
    st.subheader("⚖️ Side-by-Side Version Delta & Significance Analysis")
    
    version_keys = list(available_versions.keys())
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        version_a_name = st.selectbox("Select Version A (Baseline):", version_keys, index=0)
    with col_sel2:
        # Default index to 1 if available, otherwise 0
        default_idx = min(1, len(version_keys) - 1)
        version_b_name = st.selectbox("Select Version B (Comparison Target):", version_keys, index=default_idx)
        
    code_a = available_versions[version_a_name]
    code_b = available_versions[version_b_name]
    
    col_v1, col_v_final = st.columns(2)
    with col_v1:
        st.markdown(f"#### 📄 {version_a_name}")
        st.code(code_a, language="verilog")
        
    with col_v_final:
        st.markdown(f"#### 📄 {version_b_name}")
        st.code(code_b, language="verilog")
        
    st.markdown("---")
    
    # LLM Delta Explanation Trigger
    if st.button("🧠 Analyze Changes & Explain Significance via LLM", type="primary"):
        with st.spinner("Analyzing structural code diffs, logic alterations, and ASIC/FPGA trade-offs..."):
            
            system_prompt = (
                "You are an expert Senior ASIC Architect and Verilog Code Auditor. "
                "Analyze the provided Version A and Version B Verilog implementations. "
                "Explain precisely what has changed, why the changes were made, and the engineering significance "
                "regarding performance, area utilization, timing, or code robustness."
            )
            
            user_msg = (
                f"Version A Name: {version_a_name}\nCode A:\n{code_a}\n\n"
                f"Version B Name: {version_b_name}\nCode B:\n{code_b}\n\n"
                "Provide a detailed breakdown covering:\n"
                "1. **Summary of Code Modifications** (What changed structurally)\n"
                "2. **Logic & Syntactic Differences** (Signal changes, sensitivity lists, operator shifts)\n"
                "3. **Engineering Significance & Trade-offs** (Why Version B differs from Version A in terms of speed, area, or safety)"
            )
            
            try:
                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_msg)
                ])
                
                st.subheader("📊 AI Delta & Significance Report")
                st.markdown(response.content)
                
            except Exception as e:
                st.error(f"Failed to generate delta analysis: {e}")
