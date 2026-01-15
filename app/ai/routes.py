from flask import request, jsonify
from . import ai_bp
from .chat_ai import run_ai_chat

conversation_history = []

@ai_bp.route("/chat", methods=["POST"])
def chat_route():
    try:
        user_msg = request.json.get("message")
        if not user_msg:
            return jsonify({"reply": "لم أستلم أي رسالة.", "finished": False})

        conversation_history.append(("المستخدم", user_msg))
        ai_reply = run_ai_chat(conversation_history)
        conversation_history.append(("الذكاء", ai_reply))
        finished = "أصبحت لدي صورة واضحة" in ai_reply

        return jsonify({"reply": ai_reply, "finished": finished})

    except Exception as e:
        return jsonify({"reply": f"حدث خطأ أثناء الاتصال: {str(e)}", "finished": False})
