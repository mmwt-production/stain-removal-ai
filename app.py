import json
import os
from flask import Flask, request, render_template, redirect, url_for
from image_analysis import get_dominant_color, classify_color
from matcher import find_candidates
from db import init_db, save_record, save_feedback

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

with open("knowledge_base.json", encoding="utf-8") as f:
    KB = json.load(f)

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if request.method == "GET":
        return redirect(url_for("index"))

    file = request.files["photo"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    spread_answer = request.form.get("spread")
    texture_answer = request.form.get("texture")
    smell_answer = request.form.get("smell")
    age_answer = request.form.get("age")

    rgb = get_dominant_color(filepath)
    color_name = classify_color(rgb)

    candidates = find_candidates(KB, color_name, spread_answer, texture_answer, smell_answer)
    predicted_names = ", ".join(c["name"] for c in candidates)

    record_id = save_record(filepath, color_name, spread_answer, texture_answer, predicted_names)

    return render_template(
        "result.html",
        record_id=record_id,
        image_path=filepath,
        color_name=color_name,
        candidates=candidates,
        age_answer=age_answer,
    )

@app.route("/feedback/<int:record_id>", methods=["POST"])
def feedback(record_id):
    is_correct = request.form.get("is_correct") == "yes"
    actual_stain = request.form.get("actual_stain", "")
    actual_chemical = request.form.get("actual_chemical", "")
    save_feedback(record_id, is_correct, actual_stain, actual_chemical)
    return render_template("thanks.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)