# Lazy imports to avoid mini-swe-agent startup messages
# Import these directly from mini_agent when needed

__all__ = []


def __getattr__(name):
    """Lazy load exports to avoid importing mini-swe-agent unnecessarily."""
    if name == "BCAgent":
        from bcbench.agent.mini_agent import _create_bc_agent_class
        return _create_bc_agent_class()
    elif name == "load_entry_from_dataset":
        from bcbench.agent.mini_agent import load_entry_from_dataset
        return load_entry_from_dataset
    elif name == "build_task_description":
        from bcbench.agent.mini_agent import build_task_description
        return build_task_description
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
