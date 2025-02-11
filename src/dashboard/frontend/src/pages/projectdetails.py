# src/dashboard/frontend/src/pages/projectdetails.py
import streamlit as st

def main():
    st.title("Project Details & Core Agent Interaction")

    # We can store logs or agent responses in session state to persist across reruns
    if "agent_logs" not in st.session_state:
        st.session_state.agent_logs = "No logs yet."

    if "agent_response" not in st.session_state:
        st.session_state.agent_response = "Awaiting Core Agent response..."

    st.write("Use this page to interact with the Core Agent for a specific project.")
    
    # Text input for user to send messages to the Core Agent
    user_input = st.text_area("Enter your message to the Core Agent:", "", height=100)

    if st.button("Send to Core Agent"):
        # In a real app, you'd call your Celery or orchestrator endpoint here
        # For demonstration, let's simulate an AI response
        fake_ai_response = f"Core Agent processed your input: '{user_input}'"
        st.session_state.agent_response = fake_ai_response
        
        # Update logs
        new_log_entry = f"\nUser: {user_input}\nAgent: {fake_ai_response}\n---"
        st.session_state.agent_logs += new_log_entry

    # Display the agent response
    st.subheader("Core Agent Response")
    st.write(st.session_state.agent_response)

    # Display logs
    st.subheader("Agent Logs")
    st.text(st.session_state.agent_logs)

if __name__ == "__main__":
    main()
