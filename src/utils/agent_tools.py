from langchain.callbacks.base import BaseCallbackHandler

class ToolExecutionTracker(BaseCallbackHandler):
    def __init__(self):
        self.last_tool_name = None

    def on_tool_start(self, serialized, input_str, **kwargs):
        """Triggered when a tool starts execution."""        
        print(f"ToolExecutionTracker > on_tool_start() serialized value is {serialized} ")
        if "name" in serialized:
            self.last_tool_name = serialized["name"]
            print(f"ToolExecutionTracker > on_tool_start() last_tool_name value is {self.last_tool_name} ")

    def get_last_tool_name(self):
        return self.last_tool_name or "CoreAgent"
