import streamlit as st
import subprocess
import os
import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Page Configuration
st.set_page_config(
    page_title="PragyanAI - Batch Testbench Evaluator & Report Studio",
    page_icon="📊",
    layout="wide"
)

st.title("PragyanAI - Batch Testbench Evaluator & Comparative PDF Report Studio")
st.markdown(
    "Automatically test **all available code versions** in your session against comprehensive AI-generated test vectors, "
    "compare simulation outcomes side-by-side, determine which implementations pass successfully, and export a professional PDF report."
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
# Gather All Available Versions from Session State
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
    st.warning("⚠️ No execution history or code variants found in session state. Please run the **Multi-Agent Pipeline** or **Multi-Variant Studio** first.")
    if st.button("👉 Go to Multi-Agent Pipeline"):
        st.switch_page("pages/1_🤖_Multi_Agent_Pipeline.py")
    st.stop()

st.markdown(f"**Detected {len(available_versions)} active code version(s) in session state for evaluation.**")

# Test Strategy Configuration
test_strategy = st.selectbox(
    "Select Comprehensive Test Generation Strategy:",
    [
        "Exhaustive Edge Case & Corner State Testing",
        "High-Speed Burst Stimulus & Random Toggle Testing",
        "Reset Recovery & Asynchronous Glitch Verification"
    ]
)

custom_stimulus_notes = st.text_area("Additional test vector conditions (optional):", placeholder="e.g., test enable toggling and asynchronous reset recovery.")

if "batch_evaluation_results" not in st.session_state:
    st.session_state["batch_evaluation_results"] = {}
if "batch_testbench" not in st.session_state:
    st.session_state["batch_testbench"] = ""

# -----------------------------------------------------------------------------
# Batch Execution & Simulation Loop
# -----------------------------------------------------------------------------
if st.button("🚀 Run Batch Test Across All Versions", type="primary"):
    with st.spinner("Step 1/2: AI Agent generating comprehensive unified testbench..."):
        try:
            time.sleep(2)
            sample_code_snippet = list(available_versions.values())[0]
            tb_prompt = (
                f"You are a Senior ASIC Verification Engineer. Write a comprehensive, self-checking Verilog testbench "
                f"module suitable for testing digital designs like counters/fsm based on strategy: {test_strategy}.\n"
                f"Additional notes: {custom_stimulus_notes}\n"
                f"Reference RTL Design Structure:\n{sample_code_snippet}\n\n"
                "Return ONLY raw Verilog testbench code inside ```verilog ... ``` code blocks."
            )
            
            res = llm.invoke([
                SystemMessage(content="Output ONLY valid Verilog testbench code inside markdown code blocks."),
                HumanMessage(content=tb_prompt)
            ])
            
            content = res.content
            if "```verilog" in content:
                generated_tb = content.split("```verilog")[1].split("```")[0].strip()
            elif "```" in content:
                generated_tb = content.split("```")[1].split("```")[0].strip()
            else:
                generated_tb = content.strip()
                
            st.session_state["batch_testbench"] = generated_tb

        except Exception as e:
            st.error(f"Failed to generate testbench: {e}")
            st.stop()

    # Step 2: Run simulation on each version
    evaluation_results = {}
    progress_bar = st.progress(0)
    total_versions = len(available_versions)

    for idx, (ver_name, ver_code) in enumerate(available_versions.items()):
        with st.spinner(f"Step 2/2: Simulating [{ver_name}] via Icarus Verilog..."):
            time.sleep(3) # Rate limit safeguard
            
            with open("design.v", "w") as f:
                f.write(ver_code)
            with open("test_bench.v", "w") as f:
                f.write(st.session_state["batch_testbench"])

            try:
                compile_res = subprocess.run(
                    ["iverilog", "-g2012", "-o", "sim_batch", "design.v", "test_bench.v"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if compile_res.returncode != 0:
                    sim_output = f"COMPILATION ERROR:\n{compile_res.stderr}"
                    status = "FAILED"
                else:
                    sim_res = subprocess.run(
                        ["vvp", "sim_batch"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    sim_output = sim_res.stdout + "\n" + sim_res.stderr
                    if sim_res.returncode == 0 and "ERROR" not in sim_output.upper() and "FAILED" not in sim_output.upper():
                        status = "PASSED"
                    else:
                        status = "FAILED"
                        
                evaluation_results[ver_name] = {
                    "code": ver_code,
                    "status": status,
                    "output": sim_output
                }

            except Exception as sub_err:
                evaluation_results[ver_name] = {
                    "code": ver_code,
                    "status": "ERROR",
                    "output": str(sub_err)
                }

        progress_bar.progress((idx + 1) / total_versions)

    st.session_state["batch_evaluation_results"] = evaluation_results
    st.success("✨ Batch evaluation completed across all versions successfully!")

# -----------------------------------------------------------------------------
# Display Results & Comparison Table
# -----------------------------------------------------------------------------
if st.session_state["batch_evaluation_results"]:
    st.markdown("---")
    st.subheader("📊 Comparative Batch Evaluation Summary")

    results_data = st.session_state["batch_evaluation_results"]
    
    # Summary Table / Metrics
    cols = st.columns(len(results_data))
    for idx, (ver_name, data) in enumerate(results_data.items()):
        with cols[idx]:
            st.markdown(f"**{ver_name}**")
            if data["status"] == "PASSED":
                st.success("✅ PASSED")
            else:
                st.error(f"❌ {data['status']}")

    st.markdown("---")
    st.subheader("🔍 Detailed Version Breakdown & Execution Logs")

    for ver_name, data in results_data.items():
        with st.expander(f"📂 {ver_name} — Status: {data['status']}", expanded=True):
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.markdown("**Source Code:**")
                st.code(data["code"], language="verilog")
            with col_v2:
                st.markdown("**Simulation Output Log:**")
                st.text(data["output"])

    with st.expander("🧪 View Unified Comprehensive Testbench Used", expanded=False):
        st.code(st.session_state["batch_testbench"], language="verilog")

    # -----------------------------------------------------------------------------
    # PDF Report Generator Function
    # -----------------------------------------------------------------------------
    def generate_batch_pdf_report(results, testbench_code):
        pdf_filename = "PragyanAI_Batch_Verification_Report.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=10,
            spaceAfter=6
        )
        code_style = ParagraphStyle(
            'CodeStyle',
            fontName='Courier',
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#2D3748")
        )

        story.append(Paragraph("PragyanAI - Comprehensive Batch Verification Report", title_style))
        story.append(Paragraph("<b>Studio Module:</b> Advanced Testbench Evaluator & Comparative Analysis", styles['Normal']))
        story.append(Spacer(1, 10))

        story.append(Paragraph("1. Unified Testbench Stimulus (`test_bench.v`)", heading_style))
        story.append(Preformatted(testbench_code, code_style))
        story.append(Spacer(1, 10))

        story.append(Paragraph("2. Evaluated Versions & Simulation Results", heading_style))
        for ver_name, data in results.items():
            story.append(Paragraph(f"<b>Version:</b> {ver_name} | <b>Status:</b> {data['status']}", styles['Normal']))
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>RTL Code:</b>", styles['Normal']))
            story.append(Preformatted(data["code"], code_style))
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Simulation Output:</b>", styles['Normal']))
            story.append(Preformatted(data["output"], code_style))
            story.append(Spacer(1, 10))

        doc.build(story)
        return pdf_filename

    st.markdown("---")
    if st.button("📥 Download Formatted PDF Engineering Report", type="primary"):
        pdf_file = generate_batch_pdf_report(results_data, st.session_state["batch_testbench"])
        with open(pdf_file, "rb") as pdf_data:
            st.download_button(
                label="Click here to download PragyanAI_Batch_Verification_Report.pdf",
                data=pdf_data,
                file_name="PragyanAI_Batch_Verification_Report.pdf",
                mime="application/pdf"
            )
