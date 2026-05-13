from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from acosplatform.channels.contracts import MessageEnvelope
from acosplatform.orchestration.runtime import run_omnichannel_turn

if __name__ == "__main__":
    result = run_omnichannel_turn(MessageEnvelope(
        tenant_id="pilot",
        channel="web",
        channel_user_id="smoke-user",
        customer_id="cust_smoke",
        text="I need an outfit for a winter wedding under £200, available for pickup near Reading",
    ))
    print("ACOS north-star smoke status:", result["status"])
    print("Intent:", result["intent"]["intent"])
    print("Agent:", result["agent"]["name"])
    print("Tool calls:", len(result["tool_trace"]))
    print("Evidence events:", len(result["evidence"]))
    print("Response:", result["response_text"])
