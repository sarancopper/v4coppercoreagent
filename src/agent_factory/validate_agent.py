import subprocess

class ValidateAgent:
    def run(self, code_snippet: str) -> bool:
        # if you have an actual file, or you can store snippet in a temp file
        with open("temp_snippet.py", "w") as f:
            f.write(code_snippet)
        result = subprocess.run(["python", "-m", "py_compile", "temp_snippet.py"])
        return (result.returncode == 0)
