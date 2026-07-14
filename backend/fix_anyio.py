import os
for root, _, files in os.walk("tests"):
    for file in files:
        if file.startswith("test_") and file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            if "pytest.mark.asyncio" in content:
                content = content.replace("pytest.mark.asyncio", "pytest.mark.anyio")
                with open(path, "w") as f:
                    f.write(content)
