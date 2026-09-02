import streamlit as st

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Multi-Agent RTL & RAG Studio",
    page_icon="⚡",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Landing Page Header & Overview
# -----------------------------------------------------------------------------
try:
    st.image("PragyanAI_Transperent.png", width=300)
except Exception:
    pass

st.title("PragyanAI - Multi-Agent RTL Design, Verification & RAG Intelligence Studio")
st.markdown(
    "Welcome to the enterprise-grade hardware engineering and automated verification platform. "
    "This application coordinates specialized AI agents via **LangGraph**, high-performance LLMs (**Groq `openai/gpt-oss-120b`**), "
    "and native **Icarus Verilog** simulation binaries to build, debug, and verify digital hardware designs."
)

st.markdown("---")

# -----------------------------------------------------------------------------
# Modular Architecture Breakdown Cards (Ordered 1 to 7)
# -----------------------------------------------------------------------------
st.subheader("📌 Available Studio Modules & Navigation")
st.markdown("Use the **left sidebar** to switch seamlessly between the following modular workspaces:")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🤖 1. Multi-Agent Pipeline")
    st.markdown(
        "Automates the end-to-end design cycle. "
        "Routes your prompt through a **Generator Agent**, a strict **Critic Agent**, an automated **Testbench Creator**, "
        "and a simulation **Runner Agent** with recursive self-correction loops."
    )
    
    st.markdown("### ⚡ 2. Multi-Variant Studio")
    st.markdown(
        "Dispatches parallel architectural agents to generate **Performance-Optimized**, **Area-Optimized**, "
        "and **Robust** variants with deep trade-off breakdowns and comparative explanations."
    )
    
    st.markdown("### 🔀 3. Version Comparison")
    st.markdown(
        "Evaluates code progression side-by-side. "
        "Compare raw initial drafts against critic audit logs and final production-ready Verilog code."
    )

with col2:
    st.markdown("### ✏️ 4. Interactive Editor & Save Studio")
    st.markdown(
        "Provides a live dual-pane code editor for Verilog RTL files and testbenches. "
        "Run on-demand compilation checks (`iverilog` & `vvp`), save session states, and download files directly."
    )
    
    st.markdown("### 📖 5. Explain Code in Detail")
    st.markdown(
        "Offers customized deep-dive walkthroughs tailored for **Beginners** or **Experts**, "
        "featuring preset technical questions and comprehensive test case coverage analysis."
    )
    
    st.markdown("### 💬 6. RAG AI Assistant Bot")
    st.markdown(
        "An intelligent conversational chatbot tied directly to your active design context. "
        "Ask questions, request line-by-line code walk-throughs, or query specific architectural states."
    )
    
    st.markdown("### 📊 7. Advanced Testbench Evaluator")
    st.markdown(
        "Dispatches batch evaluations across all generated code versions using comprehensive testbench vectors, "
        "compares simulation outcomes side-by-side, and exports formatted engineering PDF reports."
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# Call to Action / Quick Start Guidance
# -----------------------------------------------------------------------------
st.success(
    "💡 **Getting Started:** Open the sidebar navigation menu on the left and select "
    "**1_🤖_Multi_Agent_Pipeline** to generate your first verified hardware module!"
)
