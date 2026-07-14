import re

with open("tests/test_mock_agent.py", "r") as f:
    content = f.read()

content = "import pytest\n" + content
content = re.sub(r'def test_', r'@pytest.mark.asyncio\nasync def test_', content)
content = re.sub(r'(scene = mock_agent.generate_scene)', r'scene = await mock_agent.generate_scene', content)
content = re.sub(r'(scene_before = mock_agent.generate_scene)', r'scene_before = await mock_agent.generate_scene', content)
content = re.sub(r'(result = mock_agent.evaluate_response)', r'result = await mock_agent.evaluate_response', content)
content = re.sub(r'(result_[a-c] = mock_agent.evaluate_response)', r'\1'.replace("result_", "result_X = await mock_agent.evaluate_response").replace("result_X", "result_"), content)
content = re.sub(r'(evaluation = mock_agent.evaluate_response)', r'evaluation = await mock_agent.evaluate_response', content)
content = re.sub(r'(result = mock_agent.generate_fit_report)', r'result = await mock_agent.generate_fit_report', content)
content = re.sub(r'(result = mock_agent.generate_mcqs)', r'result = await mock_agent.generate_mcqs', content)

# Handle the result_[a-c] properly
content = re.sub(r'(result_[a-c]) = mock_agent.evaluate_response', r'\1 = await mock_agent.evaluate_response', content)

with open("tests/test_mock_agent.py", "w") as f:
    f.write(content)

