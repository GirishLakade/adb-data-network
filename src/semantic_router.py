import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
from semantic_router import Route
from semantic_router.layer import RouteLayer
from semantic_router.encoders import HuggingFaceEncoder

# Setup logging for our AKS container logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Databricks API Models ---
class GenieSpace(BaseModel):
    space_id: str
    title: str
    description: Optional[str] = None
    warehouse_id: Optional[str] = None

class ListSpacesResponse(BaseModel):
    next_page_token: Optional[str] = None
    spaces: List[GenieSpace]

# --- Router Implementation ---
class BeaconRouter:
    def __init__(self):
        # Initialize the local CPU encoder once at startup
        logger.info("Initializing HuggingFaceEncoder...")
        self.encoder = HuggingFaceEncoder(name="BAAI/bge-small-en-v1.5")
        self.route_layer: Optional[RouteLayer] = None

    def build_routes(self, spaces_list: dict):
        """
        Parses the Databricks response and builds the semantic route layer.
        Call this during the FastAPI startup event or on a scheduled cache refresh.
        """
        try:
            parsed_response = ListSpacesResponse(**spaces_list)
        except ValidationError as e:
            logger.error(f"Failed to parse Databricks spaces list: {e}")
            raise ValueError("Invalid spaces_list format.")

        routes = []
        for space in parsed_response.spaces:
            # Construct utterances to map user prompts to this space
            utterances = [space.title]
            if space.description:
                utterances.append(space.description)
                utterances.append(f"questions related to {space.title}")
                utterances.append(f"query data about {space.description}")
            
            routes.append(
                Route(
                    name=space.space_id,
                    utterances=utterances
                )
            )
            
        # Compile the routing layer
        self.route_layer = RouteLayer(encoder=self.encoder, routes=routes)
        logger.info(f"Successfully loaded {len(routes)} Genie Spaces into the semantic router.")

    def route_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """
        Evaluates the prompt locally. Falls back to OpenAI if no confident match is found.
        """
        if not self.route_layer:
            raise RuntimeError("Route layer is not initialized. Call build_routes() first.")
            
        # Execute Level 1 local routing
        decision = self.route_layer(user_prompt)
        
        # decision.name is populated if similarity > threshold, otherwise None
        if decision.name:
            logger.info(f"Local routing successful for space: {decision.name}")
            return {
                "space_id": decision.name,
                "source": "aks_local_slm"
            }
            
        logger.info("Local routing ambiguous. Falling back to OpenAI...")
        return self._fallback_to_openai(user_prompt)

    def _fallback_to_openai(self, user_prompt: str) -> Dict[str, Any]:
        """
        Level 2 routing: Call GPT-4.1 Mini to reason through complex queries.
        """
        # TODO: Implement OpenAI function calling logic here
        # Return {"space_id": "...", "source": "openai"}
        pass

# --- Usage Example for FastAPI ---
# beacon_router = BeaconRouter()
# beacon_router.build_routes(databricks_api_response_dict)
# result = beacon_router.route_prompt("How is the gold ETF performing?")