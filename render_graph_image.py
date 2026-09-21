from app.agents.coordinator_agent import CoordinatorAgent

coordinator = CoordinatorAgent()

# 1. Save PNG with xray=True (expands all subgraphs like planner and execute_task)
try:
    png_bytes = coordinator.graph.get_graph(xray=True).draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png_bytes)
    print("SUCCESS: Saved full X-Ray visual PNG image (with subgraphs) to graph.png")
except Exception as e:
    print(f"PNG render note: {e}")