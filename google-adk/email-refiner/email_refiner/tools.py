from google.adk.tools.tool_context import ToolContext


def escalate_email_complete(tool_context: ToolContext):
    """Use this too only when the email is good to go"""
    tool_context.actions.escalate = True
