import streamlit as st
from modules.agents import build_rtl_graph

# Page Configuration
st.set_page_config(
    page_title="PragyanAI - Multi-Agent RTL Pipeline",
    page_icon="🤖",
    layout="wide"
)
st.image("")
st.title("PragyanAI - Multi-Agent RTL Generation & Verification Pipeline")
st.markdown(
    "This pipeline coordinates specialized AI agents: the **Generator Agent** drafts synthesizable Verilog code, "
    "the **Critic Agent** audits it for synthesis and timing risks, and the **Runner Agent** compiles and simulates "
    "it using Icarus Verilog."
)

# -----------------------------------------------------------------------------
# API Key Retrieval
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

# -----------------------------------------------------------------------------
# User Input Layout
# -----------------------------------------------------------------------------
user_prompt = st.text_area(
    "Describe your hardware specification:",
    value="Design a 4-bit synchronous up-counter in Verilog with an active-low asynchronous reset (rst_n) and an enable signal (en)."
)

col1, col2 = st.columns(2)
max_iter = col1.slider("Max Agent Correction Loops", 1, 5, 3)
run_pipeline = col2.button("🚀 Run Multi-Agent Pipeline", type="primary")

# -----------------------------------------------------------------------------
# Execution Workflow
# -----------------------------------------------------------------------------
if run_pipeline:
    if not user_prompt.strip():
        st.error("Please enter a valid hardware specification prompt.")
        st.stop()

    # Compile the LangGraph graph using the modular agent builder
    try:
        app = build_rtl_graph(api_key)
    except Exception as e:
        st.error(f"Failed to initialize multi-agent workflow graph: {e}")
        st.stop()

    initial_state = {
        "prompt": user_prompt,
        "rtl_code": "",
        "critic_review": "",
        "test_code": "",
        "run_output": "",
        "error_log": "",
        "iteration": 0,
        "max_iterations": max_iter,
        "status": "PENDING"
    }

    first_version_captured = False
    progress_container = st.container()

    with progress_container:
        with st.status("Running Multi-Agent Coordination Loop...", expanded=True) as status_box:
            st.write("🤖 Initializing LangGraph agents (Generator, Critic, Testbench, Runner)...")
            
            # Execute graph stream
            current_state = initial_state
            try:
                for step in app.stream(initial_state):
                    node_name = list(step.keys())[0]
                    node_update = step[node_name]
                    
                    if node_update:
                        current_state.update(node_update)
                    
                    # Capture the very first generated RTL draft before any correction loops
                    if not first_version_captured and current_state.get("rtl_code"):
                        st.session_state["rtl_v1"] = current_state["rtl_code"]
                        first_version_captured = True
                        
                    st.write(f"-> Executed Agent Node: **{node_name.upper()}** (Attempt: {current_state['iteration']})")
                    
                    if current_state.get("status") == "PASSED":
                        status_box.update(label="✅ Verification Completed Successfully!", state="complete", expanded=False)
                    elif current_state.get("error_log") and node_name == "runner":
                        st.warning(f"⚠️ Simulation or compilation failed on attempt {current_state['iteration']}. Routing back to Generator for fixes...")

                if current_state["status"] != "PASSED":
                    status_box.update(label="❌ Verification Loop Finished with Errors or Max Iterations Reached", state="error", expanded=False)

            except Exception as graph_err:
                status_box.update(label="❌ Execution crashed during graph evaluation.", state="error", expanded=False)
                st.error(f"Error details: {graph_err}")
                st.stop()

    # Save artifacts into global session state for downstream pages
    if "rtl_v1" not in st.session_state or not st.session_state["rtl_v1"]:
        st.session_state["rtl_v1"] = current_state.get("rtl_code", "")
    st.session_state["rtl_critic_notes"] = current_state.get("critic_review", "")
    st.session_state["rtl_final"] = current_state.get("rtl_code", "")
    st.session_state["testbench_code"] = current_state.get("test_code", "")
    st.session_state["simulation_log"] = current_state.get("run_output", "")

    # -----------------------------------------------------------------------------
    # Enhanced Results Display (Expanded Views: v1, Test Cases, Final Fixed Code, Logs)
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📊 Pipeline Execution Results & Expanded Version Breakdown")

    with st.expander("📝 1. First Version Code (Initial Generator Draft - v1)", expanded=True):
        st.code(st.session_state.get("rtl_v1", "// No initial draft available."), language="verilog")

    with st.expander("🧪 2. Test Case / Testbench Code Tested", expanded=True):
        st.code(st.session_state.get("testbench_code", "// No testbench generated."), language="verilog")

    with st.expander("✅ 3. Final Fixed & Verified Version Code (Working Version)", expanded=True):
        st.code(st.session_state.get("rtl_final", "// No final code available."), language="verilog")

    with st.expander("📈 4. Simulation Execution Log & Critic Notes", expanded=True):
        st.markdown("**Critic Audit Feedback:**")
        st.markdown(st.session_state.get("rtl_critic_notes", "*No critic feedback recorded.*"))
        st.markdown("---")
        st.markdown("**Simulation Terminal Output / Test Result Log:**")
        st.text(st.session_state.get("simulation_log", "No execution log available."))

    # Final Status Callout
    if current_state["status"] == "PASSED":
        st.success("🎉 **Success:** All automated test benches and verification vectors passed successfully! You can now review code versions or open the editor in the sidebar navigation.")
    else:
        st.error("⚠️ **Warning:** The pipeline finished without a fully passing simulation status. Check the audit notes and simulation logs to tweak your prompt or code manually.")
