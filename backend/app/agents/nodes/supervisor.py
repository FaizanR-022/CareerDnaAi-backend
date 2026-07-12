import logging

logger = logging.getLogger(__name__)

ALLOWED_DOMAINS = [
    "product_manager",
    "sqa_engineer",
    "data_analyst",
    "frontend_engineer",
    "backend_engineer",
    "pm",
    "sqa",
    "be",
    "fe",
    "da"
]

DEFAULT_DOMAIN = "product_manager"

def supervisor_node(state: dict) -> dict:
    """
    Supervisor node that validates the target domain.
    Reads the 'domain' string value from the SimulationState context dictionary.
    Returns an update dictionary explicitly mapping {'active_domain': domain}.
    """
    try:
        if not state or not isinstance(state, dict):
            logger.warning("State is null or not a dictionary. Falling back to default domain.")
            return {"active_domain": DEFAULT_DOMAIN}
            
        domain = state.get("domain")
        if not domain:
            logger.warning("Domain key is missing in state. Falling back to default domain.")
            return {"active_domain": DEFAULT_DOMAIN}
            
        if domain not in ALLOWED_DOMAINS:
            logger.warning(f"Invalid domain '{domain}' received. Falling back to default domain.")
            return {"active_domain": DEFAULT_DOMAIN}
            
        logger.info(f"Supervisor node successfully routed to domain: {domain}")
        return {"active_domain": domain}
    except Exception as e:
        logger.error(f"Error in supervisor_node execution: {str(e)}", exc_info=True)
        return {"active_domain": DEFAULT_DOMAIN}
