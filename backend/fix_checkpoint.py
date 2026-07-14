import re

with open("tests/test_checkpoint_recovery.py", "r") as f:
    content = f.read()

content = content.replace("def test_phase1", "@pytest.mark.anyio\nasync def test_phase1")
content = content.replace("def test_phase4", "@pytest.mark.anyio\nasync def test_phase4")
content = content.replace("graph_module.scene_graph.invoke", "await graph_module.scene_graph.ainvoke")
content = content.replace("graph_module.eval_graph.invoke", "await graph_module.eval_graph.ainvoke")

with open("tests/test_checkpoint_recovery.py", "w") as f:
    f.write(content)
