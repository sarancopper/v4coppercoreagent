from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish
from langchain.schema import OutputParserException

class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str):
        try:
            # Look for structured "Action" and "Action Input"
            if "Action:" in llm_output and "Action Input:" in llm_output:
                action = llm_output.split("Action:")[1].split("\n")[0].strip()
                action_input = llm_output.split("Action Input:")[1].strip()
                return AgentAction(tool=action, tool_input=action_input, log=llm_output)
            else:
                raise OutputParserException(f"Could not parse output: {llm_output}")
        except Exception as e:
            raise OutputParserException(f"Could not parse output: {llm_output}")
