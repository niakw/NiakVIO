from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

start = workflow.index("  publish-learning:")
end = workflow.index("  publish-repair-proposal:", start)
publish = workflow[start:end]

required = [
    "actions: write",
    "id: publish-memory",
    'echo "published=false" >> "$GITHUB_OUTPUT"',
    'echo "published=true" >> "$GITHUB_OUTPUT"',
    "Resume canonical Repair after push-triggered Learning",
    "github.event_name == 'push' && steps.publish-memory.outputs.published == 'true'",
    "gh workflow run provider-recognition-repair-v6.yml",
    "--ref main",
    "-f mode=repair",
    "FIELD_BRAIN_REPAIR_RETURN",
]
for needle in required:
    assert needle in publish, needle

# Repair-triggered Learning uses workflow_dispatch. It must not recursively
# dispatch another Repair; only the explicit push-triggered handoff closes
# this return edge.
assert "github.event_name == 'workflow_dispatch'" not in publish[publish.index("Resume canonical Repair after push-triggered Learning"):]

print("brain_learning_repair_return_workflow_test: ok")
