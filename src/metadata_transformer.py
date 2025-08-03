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
        "duration": 3,
        "avatar": "/placeholders/Sarah.webp"
    }
    
    Our Format:
    {
        "agent_type": "interview",
        "description": "Enhanced description with all context",
        "gender": "female",
        "duration_minutes": 30
    }
    """
    
    # Extract base fields
    agent_type = ui_metadata.get("type", "general")
    gender = ui_metadata.get("gender", "female")
    duration_multiplier = ui_metadata.get("duration", 2)  # Default 2 units
    
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
    
    # Calculate duration in minutes based on type and multiplier
    # Assuming each "duration unit" represents different times based on type
    duration_mapping = {
        "interview": 15,      # 15 minutes per unit
        "presentation": 10,   # 10 minutes per unit
        "english_speaking": 10,  # 10 minutes per unit
        "general": 10         # 10 minutes per unit
    }
    
    base_duration = duration_mapping.get(agent_type, 10)
    duration_minutes = base_duration * duration_multiplier
    
    # Return transformed metadata
    return {
        "agent_type": agent_type,
        "description": enhanced_description,
        "gender": gender,
        "duration_minutes": duration_minutes,
        # Keep original data for reference if needed
        "_original": ui_metadata
    }


