import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "sruthi-agent-project"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

from flask import Flask, request, jsonify
from agent import run_pipeline, extract_pdf_text
import asyncio
import tempfile

app = Flask(__name__)

@app.route("/")
def index():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Grant Compliance Monitor</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #FFF5F0;
            color: #3D2B1F;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.4rem; color: #FF8C5A; margin-bottom: 8px; }
        .header p { color: #7A5C4F; font-size: 1.05rem; }
        .badge {
            display: inline-block;
            background: #FFD5BE;
            color: #FF8C5A;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 4px 20px rgba(255, 140, 90, 0.12);
            margin-bottom: 28px;
        }
        .card h2 { color: #FF8C5A; margin-bottom: 16px; font-size: 1.2rem; }
        .upload-area {
            border: 2px dashed #FFD5BE;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            background: #FFFAF8;
            cursor: pointer;
            transition: border 0.2s;
        }
        .upload-area:hover { border-color: #FF8C5A; }
        .upload-area input { display: none; }
        .upload-area label {
            cursor: pointer;
            color: #FF8C5A;
            font-weight: 600;
            font-size: 1rem;
        }
        .upload-area p { color: #7A5C4F; margin-top: 8px; font-size: 0.9rem; }
        .file-name {
            margin-top: 12px;
            color: #FF8C5A;
            font-weight: 600;
            font-size: 0.95rem;
        }
        button {
            margin-top: 16px;
            padding: 14px 32px;
            background: #FF8C5A;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            width: 100%;
        }
        button:hover { background: #e67440; }
        button:disabled { background: #FFB347; cursor: not-allowed; }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #FF8C5A;
            font-weight: 600;
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #FFD5BE;
            border-top: 3px solid #FF8C5A;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .results { display: none; }
        .result-section {
            background: white;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 4px 20px rgba(255, 140, 90, 0.12);
            margin-bottom: 20px;
            border-left: 5px solid #FF8C5A;
        }
        .result-section h2 { color: #FF8C5A; margin-bottom: 16px; font-size: 1.15rem; }
        .result-content {
            white-space: pre-wrap;
            line-height: 1.8;
            color: #3D2B1F;
            font-size: 0.95rem;
        }
        .risk-high { color: #C0392B; font-weight: bold; }
        .risk-medium { color: #E67E22; font-weight: bold; }
        .risk-low { color: #27AE60; font-weight: bold; }
        .download-btn {
            margin-top: 12px;
            padding: 10px 24px;
            background: #FFB347;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            width: auto;
            transition: background 0.2s;
        }
        .download-btn:hover { background: #e69b30; }
        .session-badge {
            background: #FFD5BE;
            color: #FF8C5A;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
            display: inline-block;
        }
        .error {
            display: none;
            background: #FFE5E5;
            color: #C0392B;
            padding: 16px;
            border-radius: 10px;
            margin-top: 16px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Grant Compliance Monitor</h1>
            <p>AI-powered grant compliance analysis powered by Google ADK & Vertex AI</p>
        </div>

        <div class="card">
            <h2>Upload Grant Document</h2>
            <div class="upload-area" onclick="document.getElementById('pdfInput').click()">
                <input type="file" id="pdfInput" accept=".pdf" onchange="handleFile(event)">
                <label>&#128196; Click to upload your grant PDF</label>
                <p>Supported format: PDF</p>
            </div>
            <div class="file-name" id="fileName"></div>
            <div class="error" id="errorMsg">&#9888; Please upload a PDF before submitting.</div>
            <button onclick="analyze()" id="submitBtn">Analyze Grant</button>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div> Agents are analyzing your grant... this may take 90 seconds
        </div>

        <div class="results" id="results">
            <div class="session-badge" id="sessionBadge"></div>

            <div class="result-section">
                <h2>&#128196; Grant Intake Summary</h2>
                <div class="result-content" id="intakeOut"></div>
                <button class="download-btn" onclick="downloadFile('intakeOut', 'grant_intake.txt')">&#11015; Download Intake Summary</button>
            </div>

            <div class="result-section">
                <h2>&#9888;&#65039; Compliance Analysis</h2>
                <div class="result-content" id="complianceOut"></div>
                <button class="download-btn" onclick="downloadFile('complianceOut', 'compliance_analysis.txt')">&#11015; Download Compliance Analysis</button>
            </div>

            <div class="result-section">
                <h2>&#128203; Progress Report Template</h2>
                <div class="result-content" id="reportOut"></div>
                <button class="download-btn" onclick="downloadFile('reportOut', 'progress_report.txt')">&#11015; Download Report Template</button>
            </div>

            <div class="result-section">
                <h2>&#127919; Recommendations</h2>
                <div class="result-content" id="recommendationsOut"></div>
                <button class="download-btn" onclick="downloadFile('recommendationsOut', 'recommendations.txt')">&#11015; Download Recommendations</button>
            </div>
        </div>
    </div>

    <script>
        var selectedFile = null;
        var lastIntake = "";
        var lastCompliance = "";
        var lastReport = "";
        var lastRecommendations = "";

        function handleFile(event) {
            selectedFile = event.target.files[0];
            if (selectedFile) {
                document.getElementById("fileName").innerText = "Selected: " + selectedFile.name;
            }
        }

        function cleanText(text) {
            text = text.split("**").join("");
            text = text.split("##").join("");
            text = text.split("# ").join("");
            text = text.split("* ").join("");
            return text.trim();
        }

        function analyze() {
            var errorMsg = document.getElementById("errorMsg");
            if (!selectedFile) {
                errorMsg.style.display = "block";
                return;
            }
            errorMsg.style.display = "none";

            var formData = new FormData();
            formData.append("pdf", selectedFile);

            document.getElementById("submitBtn").disabled = true;
            document.getElementById("loading").style.display = "block";
            document.getElementById("results").style.display = "none";

            fetch("/analyze", {
                method: "POST",
                body: formData
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                lastIntake = cleanText(data.intake || "");
                lastCompliance = cleanText(data.compliance || "");
                lastReport = cleanText(data.report || "");
                lastRecommendations = cleanText(data.recommendations || "");

                document.getElementById("intakeOut").innerText = lastIntake;
                document.getElementById("complianceOut").innerText = lastCompliance;
                document.getElementById("reportOut").innerText = lastReport;
                document.getElementById("recommendationsOut").innerText = lastRecommendations;
                document.getElementById("sessionBadge").innerText = "Session ID: " + data.session_id;
                document.getElementById("results").style.display = "block";
            })
            .catch(function(err) {
                alert("Something went wrong. Please try again.");
            })
            .finally(function() {
                document.getElementById("submitBtn").disabled = false;
                document.getElementById("loading").style.display = "none";
            });
        }

        function downloadFile(elementId, filename) {
            var textMap = {
                "intakeOut": lastIntake,
                "complianceOut": lastCompliance,
                "reportOut": lastReport,
                "recommendationsOut": lastRecommendations
            };
            var text = textMap[elementId] || "";
            if (!text.trim()) {
                alert("Nothing to download yet!");
                return;
            }
            var blob = new Blob([text], { type: "text/plain" });
            var url = URL.createObjectURL(blob);
            var a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
        }
    </script>
</body>
</html>"""


@app.route("/analyze", methods=["POST"])
def analyze():
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF uploaded"}), 400

    pdf_file = request.files["pdf"]
    if pdf_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf_file.save(tmp.name)
        tmp_path = tmp.name

    # Extract text from PDF
    grant_text = extract_pdf_text(tmp_path)

    if not grant_text.strip():
        return jsonify({"error": "Could not extract text from PDF"}), 400

    # Run the pipeline
    result = asyncio.run(run_pipeline(grant_text))
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))