"""
Mode 2 Category Mappings
Contains predefined headers for different ITSM categories
"""

MODE2_CATEGORY_HEADERS = {
    "tickets": "Enhance the given ticket description for an ITSM solution. Make it more descriptive, correct grammatical errors, and improve clarity, technical accuracy, and professional tone for IT support tickets.",
    
    "assets": "Enhance the given asset description for IT infrastructure management. Make it more descriptive, correct grammatical errors, and improve technical specifications, condition reporting, and asset documentation details.",
    
    "problems": "Enhance the given problem description for ITSM. Make it more descriptive, correct grammatical errors, and improve root cause analysis, impact assessment, and technical problem documentation.",
    
    "incidents": "Enhance the given incident description for IT service management. Make it more descriptive, correct grammatical errors, and improve incident reporting, urgency classification, and resolution documentation.",
    
    "service-requests": "Enhance the given service request description for ITSM. Make it more descriptive, correct grammatical errors, and improve service requirement clarity, business justification, and fulfillment specifications.",
    
    "knowledge-base": "Enhance the given knowledge base article for IT documentation. Make it more descriptive, correct grammatical errors, and improve technical accuracy, step-by-step clarity, and searchable content structure.",
    
    "vendors": "Enhance the given vendor description for procurement and partnerships. Make it more descriptive, correct grammatical errors, and improve contract terms, service level descriptions, and vendor evaluation criteria.",
    
    "workbench": "Enhance the given workbench task description for IT operations. Make it more descriptive, correct grammatical errors, and improve task clarity, priority assessment, and work assignment details.",
    
    "audit-log": "Enhance the given audit log entry for compliance and security. Make it more descriptive, correct grammatical errors, and improve event description clarity, compliance context, and audit trail documentation.",
    
    "dashboard": "Enhance the given dashboard description for business intelligence. Make it more descriptive, correct grammatical errors, and improve metric definitions, KPI explanations, and dashboard functionality descriptions.",
    
    "events": "Enhance the given event description for IT operations. Make it more descriptive, correct grammatical errors, and improve event categorization, impact assessment, and operational event documentation.",
    
    "service-catalogue": "Enhance the given service description for IT service catalogue. Make it more descriptive, correct grammatical errors, and improve service definitions, delivery specifications, and customer-facing service descriptions.",
    
    "service-configuration": "Enhance the given service configuration description for ITSM. Make it more descriptive, correct grammatical errors, and improve configuration documentation, service parameters, and technical specifications.",
    
    "access-management": "Enhance the given access management description for security and permissions. Make it more descriptive, correct grammatical errors, and improve access requirement definitions, security policies, and permission documentation.",
    
    "admin-settings": "Enhance the given system administration description for configuration management. Make it more descriptive, correct grammatical errors, and improve system setting explanations, configuration procedures, and administrative documentation.",
    
    "default": "Enhance the given description for business applications. Make it more descriptive, correct grammatical errors, and improve clarity, professionalism, and technical accuracy of the content."
}

def get_available_categories():
    """Get list of available categories"""
    return list(MODE2_CATEGORY_HEADERS.keys())

def get_category_header(category: str) ->str:
    """Get header text for a specific category"""
    if category not in MODE2_CATEGORY_HEADERS:
        raise ValueError(f"category '{category}' does not exist.")
    return MODE2_CATEGORY_HEADERS[category]

def is_valid_category(category: str) ->bool:
    """Check if a category is valid"""
    return category in MODE2_CATEGORY_HEADERS