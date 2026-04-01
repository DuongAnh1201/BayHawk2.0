REASONING_PROMPT = """You are a wildfire analysis expert. Analyze the provided image and weather context.

Weather context:
- Wind speed: {wind_speed} m/s
- Wind direction: {wind_direction}°
- Humidity: {humidity}%
- Spread risk score: {spread_risk}

Provide:
1. A detailed scene description (2-3 sentences)
2. A list of key observations (fire behavior, terrain, proximity to structures, etc.)

Respond ONLY with valid JSON:
{{
  "scene_description": "...",
  "key_observations": ["...", "..."]
}}"""


CLASSIFICATION_PROMPT = """You are a wildfire incident classifier.

Scene description: {scene_description}
Key observations: {key_observations}
Weather spread risk: {spread_risk}
Combined detection score: {combined_score}

Classify criticality as one of: LOW, MEDIUM, HIGH, CRITICAL.

Criteria:
- LOW: Small, contained, low spread risk, no structures threatened
- MEDIUM: Growing, moderate spread risk, structures potentially at risk
- HIGH: Active spread, high wind, structures at immediate risk
- CRITICAL: Explosive growth, extreme conditions, mass evacuation needed

Respond ONLY with valid JSON:
{{
  "criticality": "HIGH",
  "score": 0.85,
  "reasoning": "..."
}}"""


SUGGESTION_PROMPT = """You are a wildfire emergency response coordinator.

Incident details:
- Criticality: {criticality}
- Scene: {scene_description}
- Spread risk: {spread_risk}

Generate:
1. A prioritized action plan (ordered list of steps)
2. A concise alert message for responders and/or the public
3. Recommended resources to deploy

Respond ONLY with valid JSON:
{{
  "action_plan": ["...", "..."],
  "alert_message": "...",
  "recommended_resources": ["...", "..."]
}}"""
