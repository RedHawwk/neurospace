from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import base64
import re
from PIL import Image
import io

load_dotenv()

app = Flask(__name__)

# 👇 Add your real Vercel URL here
CORS(app)


app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(image_bytes, max_size_mb=4):
    """Compress image if it's too large for the API"""
    max_size_bytes = max_size_mb * 1024 * 1024

    if len(image_bytes) <= max_size_bytes:
        return image_bytes

    print(f"⚠️ Image too large ({len(image_bytes)/1024/1024:.1f}MB), compressing...")

    img = Image.open(io.BytesIO(image_bytes))

    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background

    max_dimension = 1920
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    quality = 85

    while quality > 20:
        output.seek(0)
        output.truncate()
        img.save(output, format='JPEG', quality=quality, optimize=True)

        if output.tell() <= max_size_bytes:
            print(f"✅ Compressed to {output.tell()/1024/1024:.1f}MB (quality: {quality})")
            return output.getvalue()

        quality -= 10

    return output.getvalue()


NEURO_ANALYSIS_PROMPT = """You are Dr. Maya Chen, a neuro-aesthetic consultant who has worked with 200+ restaurants generating $50M+ in revenue optimization through design psychology.

Analyze this restaurant interior with surgical precision. Focus on SPECIFIC visual elements you can see, not generic statements.

CRITICAL INSTRUCTIONS:
- BE BRUTALLY SPECIFIC about what you see in the image (exact colors, materials, layout)
- QUANTIFY business impact with realistic dollar amounts and percentages
- IDENTIFY 3-5 specific objects/areas in the image with their approximate positions
- AVOID generic statements like "warm atmosphere"
- Every score must be justified by something VISIBLE in the image

Return ONLY valid JSON (no markdown, no explanations outside JSON):

{ ... SAME JSON SCHEMA AS BEFORE ... }
"""  # keep your full JSON schema here – I’m shortening for brevity


def analyze_image_with_openai(image_bytes):
    """Call OpenAI vision model and return parsed JSON"""
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4o" if you want max quality
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a neuro-aesthetic scoring engine. Return ONLY valid JSON matching the provided schema.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": NEURO_ANALYSIS_PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            },
        ],
        temperature=0.8,
        max_tokens=6000,
    )

    response_text = completion.choices[0].message.content.strip()

    # Safety: strip code fences if the model ever adds them
    if response_text.startswith("`"):
        response_text = re.sub(r"^```(?:json)?", "", response_text)
        response_text = re.sub(r"\n?```\s*$", "", response_text)

    return json.loads(response_text)


def transform_for_frontend(analysis_data):
    """Transform OpenAI response to match frontend expectations"""
    icon_map = {
        1: "Utensils", 2: "Heart", 3: "Sparkles", 4: "Armchair",
        5: "Zap", 6: "Target", 7: "Users", 8: "Award", 9: "Share2"
    }

    color_map = {
        1: "bg-orange-500", 2: "bg-teal-500", 3: "bg-amber-500",
        4: "bg-indigo-500", 5: "bg-blue-500", 6: "bg-purple-500",
        7: "bg-rose-500", 8: "bg-emerald-500", 9: "bg-pink-500"
    }

    if 'neuroMetrics' in analysis_data:
        for metric in analysis_data['neuroMetrics']:
            metric['icon'] = icon_map.get(metric.get('id'), "Sparkles")
            metric['color'] = color_map.get(metric.get('id'), "bg-slate-500")

    analysis_data['idealImage'] = "https://images.unsplash.com/photo-1559339352-11d035aa65de?q=80&w=1000&auto=format&fit=crop"

    return analysis_data


@app.route('/analyze', methods=['POST'])
def analyze():
    print("🧠 NeuroSpace: Received image for analysis...")

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    try:
        image_bytes = file.read()
        print(f"📊 Original image size: {len(image_bytes)/1024/1024:.2f}MB")

        image_bytes = compress_image(image_bytes, max_size_mb=4)

        print("🔬 Analyzing with OpenAI Vision...")

        analysis = analyze_image_with_openai(image_bytes)
        result = transform_for_frontend(analysis)

        print("✅ Analysis complete!")
        return jsonify(result)

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return jsonify({"error": "Failed to parse AI response"}), 500
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "model": "gpt-4o-mini"})


if __name__ == '__main__':
    print("🚀 NeuroSpace AI Server running on port 5000...")
    app.run(debug=True, port=5000)
