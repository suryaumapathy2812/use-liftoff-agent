from typing import Dict, Any


def transform_ui_metadata(ui_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform UI team's detailed metadata structure to our simplified format.
    
    UI Format:
    {
        "name": "Sarah_Tech_L5",
        "display_name": "Sarah - Senior Engineer", 
        "description": "Technical interview for L5 backend engineer...",
        "type": "interview",
        "level": "L5",
        "specialty": "Backend Engineering",
        "gender": "female",
        "duration": 15,  # Duration in minutes directly
        "avatar": "/placeholders/Sarah.webp"
    }
    
    Our Format:
    {
        "agent_type": "interview",
        "description": "Enhanced description with all context",
        "gender": "female",
        "duration_minutes": 15  # Uses duration directly from UI
    }
    """
    
    # Extract base fields
    agent_type = ui_metadata.get("type", "general")
    gender = ui_metadata.get("gender", "female")
    duration_minutes = ui_metadata.get("duration", 15)  # Duration in minutes directly from UI
    
    # Build enhanced description combining all relevant fields
    description_parts = []
    
    # Add the base description
    if "description" in ui_metadata:
        description_parts.append(ui_metadata["description"])
    
    # Add interviewer context if available
    if "display_name" in ui_metadata:
        description_parts.append(f"Interviewer: {ui_metadata['display_name']}")
    
    # Add level and specialty context
    if "level" in ui_metadata:
        description_parts.append(f"Level: {ui_metadata['level']}")
    
    if "specialty" in ui_metadata:
        description_parts.append(f"Specialty: {ui_metadata['specialty']}")
    
    # Join all parts into a comprehensive description
    enhanced_description = ". ".join(description_parts)
    
    # Return transformed metadata
    return {
        "agent_type": agent_type,
        "description": enhanced_description,
        "gender": gender,
        "duration_minutes": duration_minutes,  # Use duration directly from UI
        # Keep original data for reference if needed
        "_original": ui_metadata
    }


