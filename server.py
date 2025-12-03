from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
import os
import json
import base64
import re
from PIL import Image
import io
from openai import OpenAI


load_dotenv()

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://YOUR_VERCEL_URL_HERE"
])

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(image_bytes, max_size_mb=4):
    """Compress image if it's too large for Gemini API"""
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


# 🔥 ENHANCED PROMPT - More specific, actionable, revenue-focused
NEURO_ANALYSIS_PROMPT = """You are Dr. Maya Chen, a neuro-aesthetic consultant who has worked with 200+ restaurants generating $50M+ in revenue optimization through design psychology.

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

def analyze_image_with_openai(image_bytes):
    # Encode image as base64 for OpenAI vision
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4o" if you want max quality
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a neuro-aesthetic consultant. "
                    "Return ONLY valid JSON. No markdown, no comments."
                ),
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
    # In JSON mode you *usually* don't get back ``` fences, but we can keep the safety:
    if response_text.startswith("`"):
        response_text = re.sub(r"^```(?:json)?", "", response_text)
        response_text = re.sub(r"\n?```\s*$", "", response_text)

    return json.loads(response_text)

    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    image_part = {
        "mime_type": "image/jpeg",
        "data": image_bytes   # ✅ RAW BYTES, NOT BASE64
    }
    
    response = model.generate_content(
        [NEURO_ANALYSIS_PROMPT, image_part],
        generation_config=genai.GenerationConfig(
            temperature=0.8,
            max_output_tokens=6000,
        )
    )
    
    response_text = response.text.strip()
    
    if response_text.startswith('`'):
        response_text = re.sub(r'^```(?:json)?', '', response_text)
        response_text = re.sub(r'\n?```\s*$', '', response_text)
    
    return json.loads(response_text)



def transform_for_frontend(analysis_data):
    """Transform Gemini response to match frontend expectations"""
    
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
            metric['icon'] = icon_map.get(metric['id'], "Sparkles")
            metric['color'] = color_map.get(metric['id'], "bg-slate-500")
    
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
        
        print("🔬 Analyzing with Gemini Vision...")
        
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
    return jsonify({"status": "ok", "model": "gemini-2.0-flash-exp"})


if __name__ == '__main__':
    print("🚀 NeuroSpace AI Server running on port 5000...")
    print("📡 Using Google Gemini 2.0 Flash (Experimental) for enhanced vision analysis")
    app.run(debug=True, port=5000)
