from flask import request, jsonify
from . import ai_bp
from .chat_ai import run_ai_chat
from .analyze_prompt import analyze_conversation
from .designer_analysis import analyze_designer
from flask import session
conversation_history = []

@ai_bp.route("/chat", methods=["POST"])
def chat_route():
    try:
        user_msg = request.json.get("message")
        if not user_msg:
            return jsonify({"reply": "لم أستلم أي رسالة.", "finished": False})

        conversation_history.append(("المستخدم", user_msg))
        ai_reply = run_ai_chat(conversation_history, False)
        conversation_history.append(("الذكاء", ai_reply))
        finished = "أصبحت لدي صورة واضحة" in ai_reply
        best_designers_html = ""

        if finished:
            # تحليل المحادثة
            result = analyze_conversation(conversation_history, False)

            # إرسال تحليل المستخدم للـ best_designers route
            resp = client.post("/best_designers", json={"user_analysis": result})
            if resp.status_code == 200:
                best_designers_html = resp.data.decode("utf-8")

        return jsonify({
            "reply": ai_reply,
            "finished": finished,
            "best_designers_html": best_designers_html
        })

    except Exception as e:
        return jsonify({"reply": f"حدث خطأ أثناء الاتصال: {str(e)}", "finished": False})
@ai_bp.route("/analyze", methods=["POST"])
def analyze():
    conversation = request.json.get("conversation")

    if not conversation:
        return jsonify({"error": "No conversation"}), 400

    result = analyze_conversation(conversation, False)

    if not result:
        return jsonify({"error": "Analyze failed"}), 500

    return jsonify(result)
@ai_bp.route("/analyze_designer", methods=["POST"])
def analyze_designer_route():
    data = request.json
    designer_text = data.get("designer_text")

    if not designer_text:
        return jsonify({"error": "No designer text provided"}), 400

    try:
        result = analyze_designer(designer_text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "analyze failed"}), 500
