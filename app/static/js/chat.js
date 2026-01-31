document.addEventListener("DOMContentLoaded", () => {
    const aiButton = document.getElementById("ai-button");
    const chatBox = document.getElementById("chat-box");
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const closeBtn = document.getElementById("close-btn");

    aiButton.addEventListener("click", () => {
        chatBox.style.display = "block";
        addMessage("AI", "كيف يمكنني مساعدتك؟");
    });

    closeBtn.addEventListener("click", () => {
        chatBox.style.display = "none";
        chatMessages.innerHTML = "";
    });

    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", e => { if(e.key==="Enter") sendMessage(); });

    function addMessage(sender, msg){
        chatMessages.innerHTML += `<p><b>${sender}:</b> ${msg}</p>`;
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function sendMessage(){
        const msg = chatInput.value.trim();
        if(!msg) return;
        addMessage("أنت", msg);
        chatInput.value = "";

        fetch("/ai/chat", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({message:msg})
        })
        .then(res=>res.json())
        .then(data=>{
            addMessage("AI", data.reply);
            if(data.finished) addMessage("AI", data.result);
        })
        .catch(()=>addMessage("AI","حدث خطأ أثناء الاتصال"));
    }
    
});
