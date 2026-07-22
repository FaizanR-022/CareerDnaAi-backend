import asyncio
from app.agents.nodes.scenario import scenario_node
from app.schemas.agent_contracts import SceneContent
from app.agents.state import SimulationState

async def run():
    state = SimulationState(
        simulation_session_id="test",
        domain="data_analyst",
        difficulty="hard",
        scene_number=1,
        student_profile={},
        current_scene=None,
        current_evaluation=None,
        conversation_history=[],
        active_npc_id="",
        student_message=""
    )
    result = await scenario_node(state)
    print("RESULT:", result)

if __name__ == "__main__":
    asyncio.run(run())
