from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
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


# 🔥 ENHANCED CORS Configuration
CORS(app, 
     resources={r"/*": {"origins": "*"}},
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=False)


# Additional CORS headers for all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}



def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def compress_image(image_bytes: bytes, max_size_mb: int = 4) -> bytes:
    """Compress image if it's too large for the API"""
    max_size_bytes = max_size_mb * 1024 * 1024


    if len(image_bytes) <= max_size_bytes:
        return image_bytes


    print(f"⚠️ Image too large ({len(image_bytes)/1024/1024:.1f}MB), compressing...")


    img = Image.open(io.BytesIO(image_bytes))


    # Convert to RGB if image has alpha / palette
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background


    # Resize if very large
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



NEURO_ANALYSIS_PROMPT = """
You are Dr. Maya Chen, a neuro-aesthetic consultant who has worked with 200+ restaurants generating $50M+ in revenue optimization through design psychology.


Analyze this restaurant interior with surgical precision. Focus on SPECIFIC visual elements you can see, not generic statements.


CRITICAL INSTRUCTIONS:
- BE BRUTALLY SPECIFIC about what you see in the image (exact colors, materials, layout)
- QUANTIFY business impact with realistic dollar amounts and percentages
- IDENTIFY 3-5 specific objects/areas in the image with their approximate positions
- AVOID generic statements like "warm atmosphere" - instead say "2700K Edison bulbs creating amber glow reducing cortisol 18%"
- Every score must be justified by something VISIBLE in the image


Return ONLY valid JSON (no markdown, no explanations outside JSON):


{
  "scores": {
    "overall": <number 60-95, be critical - few restaurants score above 85>,
    "saliency": <number 50-100>,
    "biophilia": <number 10-90>,
    "warmth": <number 40-95>,
    "social": <number 50-90>,
    "clutter": <number 30-95 where higher = more cluttered>
  },
  "neuroMetrics": [
    {
      "id": 1,
      "title": "Dopamine & Appetite Stimulation",
      "score": <number 3.0-9.8 with one decimal - be honest, not all restaurants are 9+>,
      "drivers": [
        "<SPECIFIC element you see: 'Crimson velvet chairs' not 'red seating'>",
        "<Another SPECIFIC element with color/material/pattern>",
        "<Third SPECIFIC element>"
      ],
      "neuralImpact": "Activation of <specific brain region> via <specific mechanism>. <Scientific finding>.",
      "businessEffect": "Increases <specific metric> by <realistic %>. Estimated <dollar amount> per table or <conversion rate>%.",
      "tag": "<Only if exceptional: 'High upsell potential' / 'Critical revenue driver' or null>"
    },
    {
      "id": 2,
      "title": "Stress Reduction & Emotional Safety",
      "score": <number 3.0-9.8>,
      "drivers": ["<SPECIFIC color with Kelvin temp or Pantone>", "<SPECIFIC material texture>", "<SPECIFIC lighting detail>"],
      "neuralImpact": "Parasympathetic nervous system activation through <specific visual cue>. Cortisol reduction via <mechanism>.",
      "businessEffect": "Extends dwell time by <realistic minutes>. Customers order <number> more items/rounds. +$<amount> per visit.",
      "tag": null
    },
    {
      "id": 3,
      "title": "Perceived Food Quality Enhancement",
      "score": <number>,
      "drivers": ["<SPECIFIC lighting type and placement>", "<SPECIFIC surface finish>", "<SPECIFIC reflectance property>"],
      "neuralImpact": "Gustatory cortex priming through visual contrast. <Color temperature> light makes food appear <percentage>% fresher.",
      "businessEffect": "Reduces food complaints by <percentage>%. Review scores increase by <rating points>. Repeat visits +<percentage>%.",
      "tag": null
    },
    {
      "id": 4,
      "title": "Dwell Time & Seating Comfort",
      "score": <number>,
      "drivers": ["<SPECIFIC seating style and ergonomics>", "<SPECIFIC spacing measurement>", "<SPECIFIC back support detail>"],
      "neuralImpact": "Proprioceptive comfort signals reduce unconscious exit cues. Booth depth of <measurement> optimizes stay duration.",
      "businessEffect": "Average table time increases by <minutes>. Second round orders +<percentage>%. Revenue per seat hour: +$<amount>.",
      "tag": "<if booth/premium seating: 'Strong per-table revenue'>"
    },
    {
      "id": 5,
      "title": "Cognitive Load & Decision Ease",
      "score": <number>,
      "drivers": ["<SPECIFIC wall treatment>", "<SPECIFIC visual hierarchy element>", "<SPECIFIC signage/menu visibility>"],
      "neuralImpact": "Prefrontal cortex load reduced by <percentage>% through <specific design principle>. Decision time drops <seconds>.",
      "businessEffect": "Ordering speed increases <percentage>%. Table turnover improves without rushed feeling. Capacity utilization +<percentage>%.",
      "tag": null
    },
    {
      "id": 6,
      "title": "Brand Memory Encoding",
      "score": <number>,
      "drivers": ["<SPECIFIC unique design element>", "<SPECIFIC color scheme with hex/Pantone>", "<SPECIFIC architectural feature>"],
      "neuralImpact": "Hippocampal encoding strength via <distinctive element>. Memory retention after <days> days: <percentage>% vs <percentage>% industry avg.",
      "businessEffect": "Organic word-of-mouth increases <percentage>%. Return visit rate: <percentage>% vs <percentage>% benchmark. Social sharing +<percentage>%.",
      "tag": null
    },
    {
      "id": 7,
      "title": "Social Bonding & Emotional Warmth",
      "score": <number>,
      "drivers": ["<SPECIFIC lighting Kelvin temp>", "<SPECIFIC table spacing in feet/cm>", "<SPECIFIC textile material>"],
      "neuralImpact": "Oxytocin release triggered by <specific sensory input>. Interpersonal connection scores increase <percentage>%.",
      "businessEffect": "Group dining bookings +<percentage>%. Date night preference rating: <score>/10. Celebration venue selection +<percentage>%.",
      "tag": null
    },
    {
      "id": 8,
      "title": "Premium Perception & Willingness to Pay",
      "score": <number>,
      "drivers": ["<SPECIFIC material quality indicator>", "<SPECIFIC finish detail>", "<SPECIFIC architectural detail>"],
      "neuralImpact": "Price justification circuits activated via perceived craftsmanship. Value perception shifts +<percentage>% above actual pricing.",
      "businessEffect": "Menu prices can be <percentage>% higher without resistance. Premium item conversion: <percentage>%. Wine/cocktail upsells +<percentage>%.",
      "tag": "<if score > 8.5: 'Premium pricing justified'>"
    },
    {
      "id": 9,
      "title": "Instagrammability & Share Trigger",
      "score": <number 4.0-8.5 - be realistic, not everything is Instagram-perfect>,
      "drivers": ["<SPECIFIC photogenic element>", "<SPECIFIC lighting quality for cameras>", "<SPECIFIC background aesthetic>"],
      "neuralImpact": "Social validation dopamine loop activation. Identity signaling strength: <rating>. Shareability index: <percentage>%.",
      "businessEffect": "Organic social posts: <number> per month. Marketing value: $<amount>/month. New customer acquisition via social: <percentage>%.",
      "tag": null
    }
  ],
  "metrics": [
    {"subject": "Biophilia", "A": <realistic current 10-80>, "B": 85, "fullMark": 100},
    {"subject": "Warmth", "A": <realistic current>, "B": 90, "fullMark": 100},
    {"subject": "Social Layout", "A": <realistic current>, "B": 80, "fullMark": 100},
    {"subject": "Lighting", "A": <realistic current>, "B": 95, "fullMark": 100},
    {"subject": "Cleanliness", "A": <realistic current>, "B": 90, "fullMark": 100},
    {"subject": "Acoustics", "A": <estimated from visual cues>, "B": 75, "fullMark": 100}
  ],
  "insights": [
    {
      "type": "critical",
      "title": "<SPECIFIC critical issue you can see>",
      "desc": "<Detailed explanation with visual evidence from image>. Recommend: <specific solution with material/color/placement>.",
      "impact": "-$<realistic amount> per table OR -<minutes> Dwell Time"
    },
    {
      "type": "warning",
      "title": "<SPECIFIC moderate issue>",
      "desc": "<What you see and why it matters>. Quick fix: <actionable suggestion>.",
      "impact": "-<percentage>% satisfaction OR -$<amount> Avg Check"
    },
    {
      "type": "success",
      "title": "<SPECIFIC strong element you can see>",
      "desc": "<What they're doing right and why it works>. This is <benchmark comparison>.",
      "impact": "+$<amount> revenue driver OR +<percentage>% conversion"
    }
  ],
  "financials": {
    "currentDwell": <realistic 25-90 minutes based on restaurant type visible>,
    "predictedDwell": <current + realistic improvement 5-20 min>,
    "currentSpend": <realistic based on visible ambiance quality: $15-150>,
    "predictedSpend": <current + realistic improvement 10-30%>,
    "monthlyRevenueUplift": <realistic calculation: (predictedSpend - currentSpend) × avg daily covers × 30>
  },
  "objects": [
    {
      "label": "<SPECIFIC object you can see: 'Brass pendant lights' not 'lighting'>",
      "x": <percentage 0-100 from left edge>,
      "y": <percentage 0-100 from top edge>,
      "width": <percentage width 5-40>,
      "height": <percentage height 5-40>,
      "type": "positive"
    },
    {
      "label": "<SPECIFIC problem element: 'Cluttered service station' not 'clutter'>",
      "x": <percentage>,
      "y": <percentage>,
      "width": <percentage>,
      "height": <percentage>,
      "type": "negative"
    }
  ]
}


ANALYSIS CHECKLIST - Mention in your analysis:
✓ Exact color temperatures (e.g., 2700K vs 4000K)
✓ Specific materials (velvet, brass, reclaimed wood, terrazzo, etc.)
✓ Measurable spacing (table distance, ceiling height if visible)
✓ Lighting layers (ambient, task, accent - be specific about sources)
✓ Sight lines and privacy levels
✓ Traffic flow observations
✓ Surface textures and finishes
✓ Biophilic elements count (plants, natural materials, natural light)
✓ Color psychology with specific hues
✓ Realistic financial projections based on visible quality tier


Remember: Restaurant owners want ACTIONABLE INSIGHTS with MEASURABLE IMPACT, not academic theory.
"""



def analyze_image_with_openai(image_bytes: bytes) -> dict:
    """Call OpenAI vision model and return parsed JSON."""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")


    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": NEURO_ANALYSIS_PROMPT,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this restaurant interior strictly using the schema.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            },
        ],
        temperature=0.6,
        max_tokens=3500,
    )


    raw = response.choices[0].message.content
    print("🔍 RAW OPENAI OUTPUT (truncated):\n", raw[:1200])


    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned)
            cleaned = re.sub(r"```$", "", cleaned)
        return json.loads(cleaned)



def transform_for_frontend(analysis_data: dict) -> dict:
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
            mid = metric.get('id')
            metric['icon'] = icon_map.get(mid, "Sparkles")
            metric['color'] = color_map.get(mid, "bg-slate-500")


    # Static ideal image for now (frontend expects this)
    analysis_data['idealImage'] = (
        "https://images.unsplash.com/photo-1559339352-11d035aa65de"
        "?q=80&w=1000&auto=format&fit=crop"
    )


    return analysis_data



def normalize_analysis(analysis: dict) -> dict:
    """Ensure the JSON has all fields the frontend expects."""
    if analysis is None:
        analysis = {}


    # --- Scores ---
    scores = analysis.get("scores") or {}
    analysis["scores"] = {
        "overall": scores.get("overall", 75),
        "saliency": scores.get("saliency", 65),
        "biophilia": scores.get("biophilia", 40),
        "warmth": scores.get("warmth", 60),
        "social": scores.get("social", 55),
        "clutter": scores.get("clutter", 50),
    }


    # --- Financials ---
    fin = analysis.get("financials") or {}
    analysis["financials"] = {
        "currentDwell": fin.get("currentDwell", 45),
        "predictedDwell": fin.get("predictedDwell", 60),
        "currentSpend": fin.get("currentSpend", 30),
        "predictedSpend": fin.get("predictedSpend", 36),
        "monthlyRevenueUplift": fin.get("monthlyRevenueUplift", 5000),
    }


    # --- Metrics for radar chart ---
    if not analysis.get("metrics"):
        s = analysis["scores"]
        analysis["metrics"] = [
            {"subject": "Biophilia", "A": s["biophilia"], "B": 85, "fullMark": 100},
            {"subject": "Warmth", "A": s["warmth"], "B": 90, "fullMark": 100},
            {"subject": "Social Layout", "A": s["social"], "B": 80, "fullMark": 100},
            {"subject": "Lighting", "A": 75, "B": 95, "fullMark": 100},
            {"subject": "Cleanliness", "A": 70, "B": 90, "fullMark": 100},
            {"subject": "Acoustics", "A": 65, "B": 75, "fullMark": 100},
        ]


    # --- Neuro Metrics (cards) ---
    neuro = analysis.get("neuroMetrics") or []
    cleaned = []
    next_id = 1


    for m in neuro:
        cleaned.append({
            "id": m.get("id", next_id),
            "title": m.get("title", f"Metric {next_id}"),
            "score": m.get("score", round(analysis["scores"]["overall"] / 10, 1)),
            "drivers": m.get("drivers", []),
            "neuralImpact": m.get("neuralImpact", ""),
            "businessEffect": m.get("businessEffect", ""),
            "tag": m.get("tag"),
        })
        next_id += 1


    # If model gave nothing at all, make at least 2 cards
    if not cleaned:
        overall_10 = round(analysis["scores"]["overall"] / 10, 1)
        cleaned = [
            {
                "id": 1,
                "title": "Dopamine & Appetite Stimulation",
                "score": overall_10,
                "drivers": ["High color contrast", "Strong focal points", "Food-centric visuals"],
                "neuralImpact": "Increased activation of reward pathways via saturated colors and appetitive cues.",
                "businessEffect": "Higher appetizer and dessert conversion and impulse ordering.",
                "tag": "High upsell potential",
            },
            {
                "id": 2,
                "title": "Stress Reduction & Emotional Safety",
                "score": 7.0,
                "drivers": ["Soft seating", "Indirect lighting", "Enclosed booth areas"],
                "neuralImpact": "Parasympathetic activation via soft textures and reduced visual threat.",
                "businessEffect": "Longer dwell time and higher likelihood of second rounds.",
                "tag": None,
            },
        ]


    analysis["neuroMetrics"] = cleaned


    # Ensure insights & objects exist
    if "insights" not in analysis or not isinstance(analysis["insights"], list):
        analysis["insights"] = []


    if "objects" not in analysis or not isinstance(analysis["objects"], list):
        analysis["objects"] = []


    return analysis



# 🔥 ERROR HANDLERS FOR BETTER DEBUGGING
@app.errorhandler(500)
def internal_error(error):
    print(f"❌ 500 Error: {str(error)}")
    return jsonify({"error": "Internal server error", "details": str(error)}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    print(f"❌ Unhandled Exception: {str(e)}")
    import traceback
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500



@app.route('/analyze', methods=['POST', 'OPTIONS'])
@cross_origin()
def analyze():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 204
    
    print("🧠 NeuroSpace: Received image for analysis...")

    if 'file' not in request.files:
        print("❌ No file part in request")
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        print("❌ No file selected")
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        print(f"❌ Invalid file type: {file.filename}")
        return jsonify({"error": "Invalid file type"}), 400

    try:
        image_bytes = file.read()
        print(f"📊 Original image size: {len(image_bytes)/1024/1024:.2f}MB")

        if len(image_bytes) == 0:
            return jsonify({"error": "Empty file uploaded"}), 400

        image_bytes = compress_image(image_bytes, max_size_mb=4)

        print("🔬 Analyzing with OpenAI Vision...")
        
        analysis = analyze_image_with_openai(image_bytes)
        print(f"📋 Analysis received, normalizing...")
        
        analysis = normalize_analysis(analysis)
        print(f"🎨 Transforming for frontend...")
        
        result = transform_for_frontend(analysis)

        print("✅ Analysis complete!")
        return jsonify(result), 200

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return jsonify({"error": "Failed to parse AI response", "details": str(e)}), 500
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "type": type(e).__name__}), 500



@app.route('/health', methods=['GET'])
@cross_origin()
def health():
    return jsonify({"status": "ok", "model": "gpt-4o-mini"})



if __name__ == '__main__':
    print("🚀 NeuroSpace AI Server running...")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
