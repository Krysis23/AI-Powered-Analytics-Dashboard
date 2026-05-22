import os
import pathlib
import pandas as pd
import google.generativeai as genai
from dotenv import find_dotenv, load_dotenv

project_root = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(find_dotenv(usecwd=True) or project_root / ".env")
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError(
        "No Gemini API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY, "
        "or call genai.configure(api_key=my_api_key) manually."
    )
genai.configure(api_key=api_key)
client = genai.GenerativeModel("models/gemini-2.5-flash")


def build_system_prompt(df: pd.DataFrame) -> str:
    lines = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        samples = df[col].dropna().unique()[:5].tolist()
        samples =[str(s) for s in samples]
        lines.append(f"  - {col!r} ({dtype}) - e.g. {samples}")

    schema_block = "\n".join(lines)

    return f"""You are senior data analyst. The user is working with a pandas Dataframe called 'df'.

Schema:
{schema_block}

Your job: convert the user's natural language question into valid Python/pandas code.

Rules:
1. Return ONLY executable Python code. No markdown, no explanation, no comments.
2. Store the final result in a variable called 'result'.
3. 'result' must be pandas DataFrame or Series. Never a scalar.
4. If result is a Series, reset_index() it so it becomes a DataFrame.
5. Do not import anything - pandas it already available as 'pd'.pd
6. Do not modify 'df' in place -work on a copy if needed.
7. Limit result to 200 rows maximum using. head(200).

Good output examples:
    result = df.groupby('Category')['Sales'].sum().reset_index().sort_values
    ('Sales', ascending=False).head(10)
    result = df[df['Region'] == 'West'][['Product', 'Sales','Profit']].head(50)
    result = df.corr(numeric_only=True)
    result = df.describe().reset_index()
"""

def nl_to_dataframe(question: str, df:pd.DataFrame) -> pd.DataFrame:
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    
    prompt = build_system_prompt(df) + f"\n\nUser Question:\n{question}"
    
    response = client.generate_content(prompt)

    raw_code = response.text.strip()

    if raw_code.startswith("```"):
        lines = raw_code.split("\n")

        raw_code = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    local_vars = {
        "df": df.copy(),
        "pd": pd
    }

    try:
        exec(raw_code, {"__builtins__":{}}, local_vars)

    except Exception as e:
        raise ValueError(
            f"Could not execute generated code:\n{e}\n\n"
            f"Generated code:\n{raw_code}"
        )
    
    result = local_vars.get("result")

    if result is None:
        raise ValueError(
            "Model did not create a variable called 'result'."
        )
    
    if isinstance(result, pd.Series):
        result = result.reset_index()

    if not isinstance(result, pd.DataFrame):
        raise ValueError(
            f"Excepted DataFrame, got {type(result).__name__}"
        )
    
    return result.head(200)

