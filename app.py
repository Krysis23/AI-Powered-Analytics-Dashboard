import os, uuid, json
from flask import Flask, request, jsonify, session, send_file, render_template
from dotenv import load_dotenv
import pandas as pd


from utils.loader import load_file,allowed_file
from utils.profiler import profile_dataframe,profile_to_dict
from utils.cleaner import clean
from utils.charts import render_chart_json
from utils.nl_query import nl_to_dataframe

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGHT"] = 50*1024*1024
os.makedirs("uploads", exist_ok=True)


def get_df(key="clean_df") -> pd.DataFrame | None:
    path = session.get(key)
    if path and os.path.exists(path):
        return pd.read_pickle(path)
    return None

def save_df(df: pd.DataFrame, key:str) -> str:
    path = f"uploads/{uuid.uuid4().hex}.pkl"
    df.to_pickle(path)
    session[key] = path
    return path

@app.route("/")

def index():
    return render_template("index.html")

@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file sent"}),400
    f =request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}),400
    try:
        df = load_file(f)
        save_df(df,"raw_df")
        session.pop("clean_df", None)
        return jsonify({
            "rows": len(df),
            "cols":len(df.columns),
            "columns": df.columns.tolist(),
            "preview": df.head(5).to_dict(orient="records")
        })
    except Exception as e:
        return jsonify({"error": str(e)}),400
    

@app.route("/api/profile")
def profile():
    df = get_df("raw_df")
    if df is None:
        return jsonify({"error": "No file uploaded"}),400
    profiles = profile_dataframe(df)
    return jsonify([{
        "name": p.name, "inferred_type": p.inferred_type,
        "missing_pct": p.missing_pct, "n_unique": p.n_unique,
        "sample_values": [str(v) for v in p.sample_values]
    } for p in profiles])


@app.route("/api/clean", methods=["POST"])
def clean_data():
    df = get_df("raw_df")
    if df is None:
        return jsonify({"error": "No file uploaded"}),400
    config = request.get_json(force=True)
    try:
        clean_df, report =clean(df,config)
        save_df(clean_df, "clean_df")
        return jsonify({
            "rows_before":report.rows_before,
            "rows_after": report.rows_after,
            "steps": report.steps,
            "cols_dropped": report.cols_dropped,
            "nulls_filled": report.nulls_filled,
            "preview": clean_df.head(5).to_dict(orient="records"),
            "columns": clean_df.columns.tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}),400
    
def get_activate_df():
    df = get_df("clean_df")
    if df is None:
        df = get_df("raw_df")
    return df

@app.route("/api/chart", methods=["POST"])
def chart():
    df = get_activate_df()
    if df is None:
        return jsonify({"error": "No data available"}),400
    body = request.get_json(force=True)
    try:
        fig_json = render_chart_json(
            df,
            chart_type=body["chart_type"],
            x=body["x"],
            y=body.get("y"),
            color=body.get("color"),
            title=body.get("title","")
        )
        return jsonify({"chart": fig_json})
    except Exception as e:
        return jsonify({"error": str(e)}),400
    
@app.route("/api/nl-query", methods=["POST"])
def nl_query():
    df = get_activate_df()
    if df is None:
        return jsonify({"error": "No data available"}),400
    body = request.get_json(force=True)
    question = body.get("question", "").strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400
    try:
        result_df = nl_to_dataframe(question, df)
        chart_json = None
        if result_df.shape[1] == 2:
           cols =result_df.columns.tolist()
           if pd.api.types.is_numeric_dtype(result_df[cols[1]]):
               chart_json =render_chart_json(
                   result_df, "bar", x=cols[0], y=cols[1],
                   title=question[:60]
               )
        return jsonify({
            "table": result_df.head(50).to_dict(orient="records"),
            "columns": result_df.columns.tolist(),
            "charts":chart_json
        }) 
    except Exception as e:
        return jsonify({"error": str(e)}),400
    
@app.route("/api/download")
def download():
    df = get_df("clean_df")
    if df is None:
        return jsonify({"error": "No cleaned data"}),400
    path = f"uploads/{uuid.uuid4().hex}_cleaned.csv"
    df.to_csv(path,index=False)
    return send_file(path, as_attachment=True, download_name="cleaned_data.csv")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
        
    
