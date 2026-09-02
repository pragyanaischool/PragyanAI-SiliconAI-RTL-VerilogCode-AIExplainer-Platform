import subprocess
from typing import TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

class RTLState(TypedDict):
    prompt: str
    rtl_code: str
    critic_review: str
    test_code: str
    run_output: str
    error_log: str
    iteration: int
    max_iterations: int
    status: str

def compile_and_run_rtl(rtl_code: str, test_code: str) -> dict:
    """Writes design and testbench files locally and runs Icarus Verilog compilation and simulation."""
    with open("design.v", "w") as f:
        f.write(rtl_code)
    with open("test_bench.v", "w") as f:
        f.write(test_code)
        
    try:
        # Compile design and testbench using Icarus Verilog
        compile_res = subprocess.run(
            ["iverilog", "-g2012", "-o", "sim_out", "design.v", "test_bench.v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if compile_res.returncode != 0:
            error_msg = f"COMPILATION ERROR:\n{compile_res.stderr}"
            return {"run_output": error_msg, "error_log": error_msg, "status": "FAILED"}
        
        # Execute compiled binary via vvp
        sim_res = subprocess.run(
            ["vvp", "sim_out"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out = sim_res.stdout + "\n" + sim_res.stderr
        
        if sim_res.returncode == 0 and "ERROR" not in out.upper() and "FAILED" not in out.upper():
            return {"run_output": out, "error_log": "", "status": "PASSED"}
        else:
            return {"run_output": out, "error_log": out, "status": "FAILED"}
            
    except Exception as e:
        err_msg = str(e)
        return {"run_output": err_msg, "error_log": err_msg, "status": "FAILED"}

def build_rtl_graph(api_key: str):
    """Constructs and compiles the LangGraph multi-agent workflow graph."""
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.1, api_key=api_key)

    def agent_generator(state: RTLState) -> dict:
        if not state["error_log"]:
            prompt_text = f"Write initial clean Verilog code for: {state['prompt']}"
        else:
            prompt_text = (
                f"Fix bugs based on critic review and simulation errors:\n"
                f"Critic Feedback:\n{state['critic_review']}\n\n"
                f"Current Faulty RTL Code:\n{state['rtl_code']}\n\n"
                f"Simulation Error Log:\n{state['error_log']}"
            )
        
        res = llm.invoke([
            SystemMessage(content="You are an expert Verilog generator agent. Output ONLY raw verilog code inside standard markdown ```verilog ... ``` code blocks."),
            HumanMessage(content=prompt_text)
        ])
        content = res.content
        
        if "```verilog" in content:
            rtl = content.split("```verilog")[1].split("```")[0].strip()
        elif "```" in content:
            rtl = content.split("```")[1].split("```")[0].strip()
        else:
            rtl = content.strip()
            
        return {"rtl_code": rtl}

    def agent_critic(state: RTLState) -> dict:
        res = llm.invoke([
            SystemMessage(content="You are a strict hardware design critic. Review the provided Verilog code for synthesis flaws, latch inferences, missing reset controls, or timing violations. Provide concise bullet points of feedback."),
            HumanMessage(content=state["rtl_code"])
        ])
        return {"critic_review": res.content}

    def agent_testbench(state: RTLState) -> dict:
        # Generate testbench only on the first pass to keep testing stable
        if state["test_code"] and state["iteration"] > 0:
            return {}
            
        res = llm.invoke([
            SystemMessage(content="You are a hardware verification engineer. Write a self-checking Verilog testbench module using $display and $finish. Output ONLY raw verilog testbench code inside standard markdown ```verilog ... ``` code blocks."),
            HumanMessage(content=f"Write a self-checking testbench for this RTL design:\n{state['rtl_code']}")
        ])
        content = res.content
        
        if "```verilog" in content:
            tb = content.split("```verilog")[1].split("```")[0].strip()
        elif "```" in content:
            tb = content.split("```")[1].split("```")[0].strip()
        else:
            tb = content.strip()
            
        return {"test_code": tb}

    def agent_runner(state: RTLState) -> dict:
        res = compile_and_run_rtl(state["rtl_code"], state["test_code"])
        return {
            "run_output": res["run_output"],
            "error_log": res["error_log"],
            "status": res["status"],
            "iteration": state["iteration"] + 1
        }

    # Build StateGraph workflow topology
    workflow = StateGraph(RTLState)
    workflow.add_node("generator", agent_generator)
    workflow.add_node("critic", agent_critic)
    workflow.add_node("testbench", agent_testbench)
    workflow.add_node("runner", agent_runner)

    workflow.set_entry_point("generator")
    workflow.add_edge("generator", "critic")
    workflow.add_edge("critic", "testbench")
    workflow.add_edge("testbench", "runner")
    
    workflow.add_conditional_edges(
        "runner",
        lambda s: "end" if s["status"] == "PASSED" or s["iteration"] >= s["max_iterations"] else "fix",
        {
            "fix": "generator",
            "end": END
        }
    )
    
    return workflow.compile()
