from google.adk.tools.tool_context import ToolContext


def escalate_email_complete(tool_context: ToolContext):
    """Call this tool only when the email meets professional standards and is ready for final approval."""
    tool_context.actions.escalate = True
    return "Email optimization complete."
