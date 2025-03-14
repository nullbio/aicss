"""
AI CSS Framework - Converting natural language to CSS with AI.
"""

# Don't import ML components here to allow for faster help command execution

__version__ = "0.1.0"

# Provide function stubs for backward compatibility
def nl_to_css(*args, **kwargs):
    """Lazy import for nl_to_css_fast function."""
    from .ml.engine import nl_to_css_fast
    return nl_to_css_fast(*args, **kwargs)

def initialize_engine(*args, **kwargs):
    """Lazy import for initialize_engine function."""
    from .ml.engine import initialize_engine as _initialize_engine
    return _initialize_engine(*args, **kwargs)