import openai
import json
import os

# =============================================================================
# CONFIGURATION - Load API key from api_config.json or environment variable
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
V1_DIR = os.path.dirname(SCRIPT_DIR)
CONFIG_FILE = os.path.join(V1_DIR, "APIs", "api_config.json")

OPENAI_API_KEY = None

# Try loading from config file first
if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
        OPENAI_API_KEY = config.get("OPENAI_API_KEY", "").strip()

# Fall back to environment variable
if not OPENAI_API_KEY:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
    raise ValueError("Please set your OpenAI API key in api_config.json or OPENAI_API_KEY environment variable")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# =============================================================================
# SYSTEM PROMPT FOR THE AI AGENT
# =============================================================================
SYSTEM_PROMPT = """You are a parser that converts natural language requests about structural columns into a JSON format.

The columns have these properties:
- alpha_grid: Letters A through F (grid lines)
- numeric_grid: Numbers 1 through 5 (grid lines)
- base_level: Levels L0 through L8 (floor levels, referenced as 0-8 in queries)
- column_type: "RC sq" (reinforced concrete square) or "SC" (steel column)
- size: String with mm unit like "500mm", "400mm", "600mm" (for square columns)

You must output ONLY valid JSON with an "operations" array. Each operation has:
- "query": filters to select columns
- "change": values to change on selected columns (empty {} if no changes requested)

Query syntax:
- "level": ">5", "<3", ">=5", "<=3", "5", "2-5" (for ranges, use numbers only)
- "alpha": "B", "B-D" (single or range)
- "numeric": "2", "2-4" (single or range)
- "type": "RC sq" or "SC"
- "size": "500mm"

Change syntax:
- "size": "600mm" (string with mm unit)
- "type": "RC sq" or "SC"

Examples:

Input: "all columns above level 5"
Output: {"operations": [{"query": {"level": ">5"}, "change": {}}]}

Input: "all columns that are RC sq"
Output: {"operations": [{"query": {"type": "RC sq"}, "change": {}}]}

Input: "all columns between grids B and D, and above level 5 should change to 400mm RC sq"
Output: {"operations": [{"query": {"alpha": "B-D", "level": ">5"}, "change": {"size": "400mm", "type": "RC sq"}}]}

Input: "change all columns at level 3 to 600mm"
Output: {"operations": [{"query": {"level": "3"}, "change": {"size": "600mm"}}]}

Input: "columns C2 to E4, levels 0-3, change to SC 300mm"
Output: {"operations": [{"query": {"alpha": "C-E", "numeric": "2-4", "level": "0-3"}, "change": {"type": "SC", "size": "300mm"}}]}

Input: "for all columns B to E and 2 to 4, make those with base_level L0 to L4 600mm, base_level L5 to L7 450mm, and the levels above that should be 400mm"
Output: {"operations": [{"query": {"alpha": "B-E", "numeric": "2-4", "level": "0-4"}, "change": {"size": "600mm"}}, {"query": {"alpha": "B-E", "numeric": "2-4", "level": "5-7"}, "change": {"size": "450mm"}}, {"query": {"alpha": "B-E", "numeric": "2-4", "level": ">7"}, "change": {"size": "400mm"}}]}

IMPORTANT: Output ONLY the JSON object, no explanation or other text.
IMPORTANT: For multi-part requests with different conditions, return multiple operations in the array.
IMPORTANT: Size must be a STRING with mm unit, e.g. "600mm" not 600."""


def parse_request(user_input: str) -> dict:
    """
    Parse natural language into query and change dictionaries using OpenAI.

    Args:
        user_input: Natural language request about columns

    Returns:
        Dictionary with "query" and "change" keys
    """
    try:
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0
        )

        result_text = response.choices[0].message.content.strip()

        # Clean up if wrapped in markdown code block
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        return json.loads(result_text)

    except Exception as e:
        print(f"Error in AI parsing: {e}")
        return {"operations": [], "error": str(e)}


# =============================================================================
# MAIN - Test the parser
# =============================================================================
if __name__ == "__main__":
    test_inputs = [
        "all columns above level 5",
        "columns between B and D, above level 5, change to 400x400 RC",
        "change all RC columns at level 3 to 600x600 SC",
        "grids C to E, numeric 2-4, levels 0-3, set size to 300x300",
    ]

    for text in test_inputs:
        print(f"\nInput: {text}")
        try:
            result = parse_request(text)
            print(f"Output: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
