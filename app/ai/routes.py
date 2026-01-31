from flask import request, jsonify
from . import ai_bp
from .chat_ai import run_ai_chat
from .analyze_prompt import analyze_conversation


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

        if(finished):
            result = analyze_conversation(conversation_history, False)

        return jsonify({"reply": ai_reply, "finished": finished, "result":result if finished else ""})

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

