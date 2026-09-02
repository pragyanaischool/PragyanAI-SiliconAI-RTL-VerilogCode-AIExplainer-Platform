import streamlit as st
import re
import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Page Configuration
st.set_page_config(
    page_title="PragyanAI - Multi-Agent Variant Studio",
    page_icon="⚡",
    layout="wide"
)

try:
    st.image("PragyanAI_Transperent.png", width=300)
except Exception:
    pass

st.title("PragyanAI - Multi-Agent Variant Generation & Specialized Testbench Studio")
st.markdown(
    "Instead of a single linear pipeline, this module dispatches **three specialized design agents** in parallel: "
    "a *Performance Architect*, an *Area Optimizer*, and a *Robustness Engineer*. "
    "Each agent generates a custom Verilog RTL design **plus a specialized testbench**, "
    "along with trade-off explanations and comparative analyses below."
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

# Helper function to parse LLM response into code blocks and explanation
def parse_agent_response(content: str) -> tuple:
    code_blocks = re.findall(r"```verilog\s*(.*?)\s*```", content, re.DOTALL)
    code = code_blocks[0].strip() if len(code_blocks) > 0 else "// No RTL code block found."
    tb = code_blocks[1].strip() if len(code_blocks) > 1 else "// No specialized testbench block found."
    
    # Everything outside code blocks is treated as explanation/analysis
    explanation = re.sub(r"```verilog.*?```", "", content, flags=re.DOTALL).strip()
    return code, tb, explanation

# -----------------------------------------------------------------------------
# User Input Layout
# -----------------------------------------------------------------------------
user_prompt = st.text_area(
    "Describe your hardware specification:",
    value="Design a 4-bit synchronous up-counter in Verilog with an active-low asynchronous reset (rst_n) and an enable signal (en)."
)

spawn_variants = st.button("🚀 Spawn Multi-Agent Variant Generation & Testbenches", type="primary")

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
            time.sleep(2)
            perf_res = llm.invoke([
                SystemMessage(content=(
                    "You are a High-Performance ASIC Architect. Focus on unrolling, pipelining, speed, "
                    "and maximizing clock frequency. "
                    "Provide TWO markdown verilog code blocks: "
                    "1) The Verilog RTL design inside ```verilog ... ``` "
                    "2) A self-checking testbench module inside a second ```verilog ... ``` "
                    "Followed by a detailed architectural explanation of why this layout is faster."
                )),
                HumanMessage(content=f"Design for maximum performance: {user_prompt}")
            ])
            perf_rtl, perf_tb, perf_exp = parse_agent_response(perf_res.content)

            # 2. Area-Optimized Agent
            time.sleep(2)
            area_res = llm.invoke([
                SystemMessage(content=(
                    "You are an Area-Optimization Expert. Focus on minimizing LUT counts, register footprint, "
                    "and sharing logical components. "
                    "Provide TWO markdown verilog code blocks: "
                    "1) The Verilog RTL design inside ```verilog ... ``` "
                    "2) A self-checking testbench module inside a second ```verilog ... ``` "
                    "Followed by a detailed breakdown of gate-count and area savings."
                )),
                HumanMessage(content=f"Design for minimum gate/area utilization: {user_prompt}")
            ])
            area_rtl, area_tb, area_exp = parse_agent_response(area_res.content)

            # 3. Robustness & Clean Code Agent
            time.sleep(2)
            robust_res = llm.invoke([
                SystemMessage(content=(
                    "You are a Senior Verification and Clean Code Engineer. Focus on clean readability, robust "
                    "edge-case handling, and safe synchronization logic. "
                    "Provide TWO markdown verilog code blocks: "
                    "1) The Verilog RTL design inside ```verilog ... ``` "
                    "2) A self-checking testbench module inside a second ```verilog ... ``` "
                    "Followed by an explanation of its maintainability features."
                )),
                HumanMessage(content=f"Design for maximum robustness and defensive coding: {user_prompt}")
            ])
            robust_rtl, robust_tb, robust_exp = parse_agent_response(robust_res.content)

            # Store variants and testbenches safely in session state
            st.session_state["variant_perf"] = perf_rtl
            st.session_state["variant_perf_tb"] = perf_tb
            st.session_state["exp_perf"] = perf_exp

            st.session_state["variant_area"] = area_rtl
            st.session_state["variant_area_tb"] = area_tb
            st.session_state["exp_area"] = area_exp

            st.session_state["variant_robust"] = robust_rtl
            st.session_state["variant_robust_tb"] = robust_tb
            st.session_state["exp_robust"] = robust_exp

            st.success("✨ All parallel variant agents and specialized testbenches completed successfully!")

        except Exception as e:
            st.error(f"Error during multi-agent variant generation: {e}")
            st.stop()

# -----------------------------------------------------------------------------
# Render Variants & Explanations if Available in Session State
# -----------------------------------------------------------------------------
if st.session_state.get("variant_perf"):
    st.markdown("---")
    st.subheader("🔍 Comparative Architectural Variants & Specialized Testbenches")
    
    tab_p, tab_a, tab_r = st.tabs([
        "⚡ Performance Optimized", 
        "📉 Area Optimized", 
        "🛡️ Robust & Clean"
    ])

    with tab_p:
        st.markdown("### 🚀 High-Performance Architecture")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("**RTL Design (`design.v`)**")
            st.code(st.session_state.get("variant_perf", ""), language="verilog")
        with col_p2:
            st.markdown("**Specialized Testbench (`test_bench.v`)**")
            st.code(st.session_state.get("variant_perf_tb", "// No testbench generated yet."), language="verilog")
            
        st.markdown("#### Architectural Trade-off Analysis & Explanation")
        st.markdown(st.session_state.get("exp_perf", ""))
        
        if st.button("📌 Select Performance RTL & Testbench for Studio", key="btn_perf"):
            st.session_state["rtl_final"] = st.session_state.get("variant_perf", "")
            st.session_state["testbench_code"] = st.session_state.get("variant_perf_tb", "")
            st.success("✅ Locked Performance design and testbench into active session state! Head over to the **Interactive Editor** or **Advanced Testbench Evaluator**.")

    with tab_a:
        st.markdown("### 📉 Low-Area / Resource-Optimized Architecture")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.markdown("**RTL Design (`design.v`)**")
            st.code(st.session_state.get("variant_area", ""), language="verilog")
        with col_a2:
            st.markdown("**Specialized Testbench (`test_bench.v`)**")
            st.code(st.session_state.get("variant_area_tb", "// No testbench generated yet."), language="verilog")
            
        st.markdown("#### Architectural Trade-off Analysis & Explanation")
        st.markdown(st.session_state.get("exp_area", ""))
        
        if st.button("📌 Select Area RTL & Testbench for Studio", key="btn_area"):
            st.session_state["rtl_final"] = st.session_state.get("variant_area", "")
            st.session_state["testbench_code"] = st.session_state.get("variant_area_tb", "")
            st.success("✅ Locked Area design and testbench into active session state! Head over to the **Interactive Editor** or **Advanced Testbench Evaluator**.")

    with tab_r:
        st.markdown("### 🛡️ Robust & Defensive Coding Architecture")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("**RTL Design (`design.v`)**")
            st.code(st.session_state.get("variant_robust", ""), language="verilog")
        with col_r2:
            st.markdown("**Specialized Testbench (`test_bench.v`)**")
            st.code(st.session_state.get("variant_robust_tb", "// No testbench generated yet."), language="verilog")
            
        st.markdown("#### Architectural Trade-off Analysis & Explanation")
        st.markdown(st.session_state.get("exp_robust", ""))
        
        if st.button("📌 Select Robust RTL & Testbench for Studio", key="btn_robust"):
            st.session_state["rtl_final"] = st.session_state.get("variant_robust", "")
            st.session_state["testbench_code"] = st.session_state.get("variant_robust_tb", "")
            st.success("✅ Locked Robust design and testbench into active session state! Head over to the **Interactive Editor** or **Advanced Testbench Evaluator**.")
