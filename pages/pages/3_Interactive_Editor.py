import streamlit as st
import subprocess
from pathlib import Path
# Page Configuration
st.set_page_config(
    page_title="Interactive Editor & Save Studio",
    page_icon="✏️",
    layout="wide"
)
st.title("PragyanAI - Interactive Code Editor, Compilation & Save Studio")
st.markdown(
    "Modify any part of the generated Verilog design or testbench code directly, "
    "run on-demand compilation checks, save your edits to the session, and download files."
)
# -----------------------------------------------------------------------------
# Check Session State Data Availability
# -----------------------------------------------------------------------------
if "rtl_final" not in st.session_state:
    st.session_state["rtl_final"] = "// Enter or generate your Verilog RTL code here\n"
if "testbench_code" not in st.session_state:
    st.session_state["testbench_code"] = "// Enter or generate your testbench code here\n"
# -----------------------------------------------------------------------------
# Editor Layout
# -----------------------------------------------------------------------------
col_edit1, col_edit2 = st.columns(2)
with col_edit1:
    st.subheader(" Verilog RTL Design (`design.v`)")
    edited_rtl = st.text_area(
        "Edit RTL Code:",
        value=st.session_state["rtl_final"],
        height=350,
        key="rtl_editor_text"
    )
with col_edit2:
    st.subheader(" Testbench Module (`test_bench.v`)")
    edited_tb = st.text_area(
        "Edit Testbench Code:",
        value=st.session_state["testbench_code"],
        height=350,
        key="tb_editor_text"
    )
st.markdown("---")
# -----------------------------------------------------------------------------
# Action Buttons (Save, Test Compile, Download)
# -----------------------------------------------------------------------------
col_btn1, col_btn2, col_btn3 = st.columns(3)
with col_btn1:
    if st.button(" Save Edits to Session", type="primary"):
        st.session_state["rtl_final"] = edited_rtl
        st.session_state["testbench_code"] = edited_tb
        st.success("✅ Changes successfully saved to active session state!")
with col_btn2:
    compile_test_btn = st.button("⚡ Test Compile & Simulate")
with col_btn3:
    st.download_button(
        label=" Download RTL File (`design.v`)",
        data=edited_rtl,
        file_name="design.v",
        mime="text/plain"
    )
# -----------------------------------------------------------------------------
# On-Demand Test Compilation Feature
# -----------------------------------------------------------------------------
if compile_test_btn:
    st.markdown("###  Live Compilation & Simulation Output")
    with st.spinner("Compiling with Icarus Verilog..."):
        # Write files locally for compilation
        with open("design.v", "w") as f:
            f.write(edited_rtl)
        with open("test_bench.v", "w") as f:
            f.write(edited_tb)
        try:
            compile_res = subprocess.run(
                ["iverilog", "-g2012", "-o", "sim_out", "design.v", "test_bench.v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if compile_res.returncode != 0:
                st.error("❌ Compilation Failed:")
                st.code(compile_res.stderr)
            else:
                st.success(" Compilation Successful! Running simulation via `vvp`...")
                sim_res = subprocess.run(
                    ["vvp", "sim_out"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                output = sim_res.stdout + "\n" + sim_res.stderr
                st.code(output)
                
                if sim_res.returncode == 0 and "ERROR" not in output.upper() and "FAILED" not in output.upper():
                    st.balloons()
                    st.success("🎉 Simulation passed all checks successfully!")
                else:
                    st.warning("⚠️ Simulation completed with warnings, assertion failures, or error logs.")    
        except Exception as e:
            st.error(f"Execution error while running simulation subprocess: {e}")
