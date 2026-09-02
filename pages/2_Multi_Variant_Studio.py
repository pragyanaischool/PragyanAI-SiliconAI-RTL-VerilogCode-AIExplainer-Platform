import streamlit as st
import re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Page Configuration
st.set_page_config(
    page_title="PragyanAI - Multi-Agent Variant Studio",
    page_icon="⚡",
    layout="wide"
)

st.title("PragyanAI - Multi-Agent Variant Generation & Explanation Studio")
st.markdown(
    "Instead of a single linear pipeline, this module dispatches **three specialized design agents** in parallel: "
    "a *Performance Architect*, an *Area Optimizer*, and a *Robustness Engineer*. "
    "Review their unique implementations, code differences, and trade-off explanations below."
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

# Initialize LLM with the specified model
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2, api_key=api_key)

# Helper function to parse LLM response into code and explanation blocks
def parse_agent_response(content: str) -> tuple:
    match_code = re.search(r"```verilog\s*(.*?)\s*```", content, re.DOTALL)
    if match_code:
        code = match_code.group(1).strip()
        # Everything outside or after the code block is treated as explanation/analysis
        explanation = re.sub(r"```verilog.*?```", "", content, flags=re.DOTALL).strip()
    else:
        code = "// Parsing failed or no verilog block found."
        explanation = content.strip()
    return code, explanation

# -----------------------------------------------------------------------------
# User Input Layout
# -----------------------------------------------------------------------------
user_prompt = st.text_area(
    "Describe your hardware specification:",
    value="Design a 4-bit synchronous up-counter in Verilog with an active-low asynchronous reset (rst_n) and an enable signal (en)."
)

spawn_variants = st.button("🚀 Spawn Multi-Agent Variant Generation", type="primary")

# -----------------------------------------------------------------------------
# Parallel Variant Execution Workflow
# -----------------------------------------------------------------------------
if spawn_variants:
    if not user_prompt.strip():
        st.error("Please enter a valid hardware specification prompt.")
        st.stop()

    with st.spinner("Dispatching parallel agents (Performance Architect, Area Optimizer, Robustness Engineer)..."):
        try:
            # 1. Performance-Optimized Agent
            perf_res = llm.invoke([
                SystemMessage(content=(
                    "You are a High-Performance ASIC Architect. Focus on unrolling, pipelining, speed, "
                    "and maximizing clock frequency. Return raw Verilog code inside ```verilog ... ``` "
                    "followed by a detailed architectural explanation of why this layout is faster."
                )),
                HumanMessage(content=f"Design for maximum performance: {user_prompt}")
            ])
            perf_rtl, perf_exp = parse_agent_response(perf_res.content)

            # 2. Area-Optimized Agent
            area_res = llm.invoke([
                SystemMessage(content=(
                    "You are an Area-Optimization Expert. Focus on minimizing LUT counts, register footprint, "
                    "and sharing logical components. Return raw Verilog code inside ```verilog ... ``` "
                    "followed by a detailed breakdown of gate-count and area savings."
                )),
                HumanMessage(content=f"Design for minimum gate/area utilization: {user_prompt}")
            ])
            area_rtl, area_exp = parse_agent_response(area_res.content)

            # 3. Robustness & Clean Code Agent
            robust_res = llm.invoke([
                SystemMessage(content=(
                    "You are a Senior Verification and Clean Code Engineer. Focus on clean readability, robust "
                    "edge-case handling, and safe synchronization logic. Return raw Verilog code inside ```verilog ... ``` "
                    "followed by an explanation of its maintainability features."
                )),
                HumanMessage(content=f"Design for maximum robustness and defensive coding: {user_prompt}")
            ])
            robust_rtl, robust_exp = parse_agent_response(robust_res.content)

            # Store variants in session state
            st.session_state["variant_perf"] = perf_rtl
            st.session_state["exp_perf"] = perf_exp
            st.session_state["variant_area"] = area_rtl
            st.session_state["exp_area"] = area_exp
            st.session_state["variant_robust"] = robust_rtl
            st.session_state["exp_robust"] = robust_exp

            st.success("✨ All parallel variant agents completed successfully!")

        except Exception as e:
            st.error(f"Error during multi-agent variant generation: {e}")
            st.stop()

# -----------------------------------------------------------------------------
# Render Variants & Explanations if Available in Session State
# -----------------------------------------------------------------------------
if "variant_perf" in st.session_state:
    st.markdown("---")
    st.subheader("🔍 Comparative Architectural Variants")
    
    tab_p, tab_a, tab_r = st.tabs([
        "⚡ Performance Optimized", 
        "📉 Area Optimized", 
        "🛡️ Robust & Clean"
    ])

    with tab_p:
        st.markdown("### 🚀 High-Performance Architecture")
        st.code(st.session_state["variant_perf"], language="verilog")
        st.markdown("#### Architectural Trade-off Analysis & Explanation")
        st.markdown(st.session_state["exp_perf"])
        
        if st.button("📌 Select Performance Version for Interactive Editor", key="btn_perf"):
            st.session_state["rtl_final"] = st.session_state["variant_perf"]
            st.success("✅ Locked Performance version into active session state! Head over to the **Interactive Editor** page.")

    with tab_a:
        st.markdown("### 📉 Low-Area / Resource-Optimized Architecture")
        st.code(st.session_state["variant_area"], language="verilog")
        st.markdown("#### Architectural Trade-off Analysis & Explanation")
        st.markdown(st.session_state["exp_area"])
        
        if st.button("📌 Select Area Version for Interactive Editor", key="btn_area"):
            st.session_state["rtl_final"] = st.session_state["variant_area"]
            st.success("✅ Locked Area version into active session state! Head over to the **Interactive Editor** page.")

    with tab_r:
        st.markdown("### 🛡️ Robust & Defensive Coding Architecture")
        st.code(st.session_state["variant_robust"], language="verilog")
        st.markdown("#### Architectural Trade-off Analysis & Explanation")
        st.markdown(st.session_state["exp_robust"])
        
        if st.button("📌 Select Robust Version for Interactive Editor", key="btn_robust"):
            st.session_state["rtl_final"] = st.session_state["variant_robust"]
            st.success("✅ Locked Robust version into active session state! Head over to the **Interactive Editor** page.")
