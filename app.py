from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# 데이터베이스: 키워드 튜플, 답변
animal_qa_db = {
    ("안녕", "안녕하세요", "하이", "헬로우"): "네 안녕하세요! 무엇을 도와드릴까요?",
    
    ("강아지", "먹으면", "안", "될", "것", "금지", "음식", "초콜릿", "포도", "양파", "마늘"): \
        "강아지가 먹으면 안 되는 음식: 초콜릿, 포도, 양파, 마늘, 카페인, 알코올 등이 있어요. 절대 주지 마세요.",
    
    ("초콜릿", "먹었어요", "초콜릿", "먹었어"): \
        "초콜릿은 강아지에게 매우 독성이 있으니 즉시 동물병원에 데려가야 합니다.",
    
    ("똥", "많이", "싸요", "배변", "설사", "변", "자주", "대변", "똥", "많이", "싸", "많이", "쌔"): \
        "강아지가 배변을 많이 하거나 설사를 한다면 소화 문제, 기생충 감염, 스트레스 등이 원인일 수 있습니다. 상태가 심하면 동물병원 방문이 필요해요.",
    
    ("긁어요", "가려워", "벼룩", "피부", "문제", "긁어", "가려워해"): \
        "강아지가 자주 긁는다면 알레르기, 벼룩, 피부 감염 등이 원인일 수 있으니 수의사 상담을 추천합니다.",
    
    ("고양이", "야옹", "울음", "소리"): \
        "고양이는 의사소통을 위해 야옹하며, 배고프거나 관심 받고 싶을 때 주로 울어요.",
    
    ("고양이", "안", "먹어요", "식욕", "부진", "밥", "안", "먹어"): \
        "고양이가 식욕이 떨어지면 스트레스나 건강 문제일 수 있어요. 수의사 상담을 권장합니다.",
    
    ("물", "많이", "마셔요", "갈증", "물", "많이", "마셔"): \
        "강아지가 물을 많이 마시면 당뇨, 신장 질환 등이 의심될 수 있으니 주의가 필요해요.",
    
    ("목욕", "주기", "얼마나", "자주", "목욕", "해"): \
        "강아지는 보통 2~4주에 한 번 목욕하는 게 적당하지만, 피부 상태에 따라 조절하세요.",
    
    ("짖어요", "짖음", "짖는", "이유", "짖어"): \
        "강아지가 많이 짖으면 스트레스, 불안, 외로움 등이 원인일 수 있으니 환경을 점검해 주세요.",
    
    ("화장실", "안", "가요", "배변", "문제"): \
        "고양이가 화장실을 자주 안 가면 요로 질환 등이 의심되니 수의사 상담을 권합니다.",
    
    ("공격적이에요", "갑자기", "공격", "행동", "공격적이야","사나워"): \
        "강아지가 갑자기 공격적이면 스트레스, 통증, 환경 변화 때문일 수 있어 관찰과 수의사 상담이 필요합니다.",
    
    ("예방접종", "접종", "주기", "백신"): \
        "강아지 예방접종은 생후 6~8주부터 시작해 정기적으로 받아야 합니다. 수의사와 상담하세요.",
    
    ("사료", "추천", "먹이", "밥"): \
        "연령과 건강 상태에 맞는 균형 잡힌 사료를 선택하는 것이 중요합니다.",
    
    ("잘", "지냈어", "요즘", "어때", "어떻게", "지내"): \
        "네, 잘 지내고 있어요! 무엇을 도와드릴까요?",
    
    ("기본",): "죄송해요, 그 질문에 대한 답변이 아직 준비되지 않았어요."
}

animals = ["강아지", "개", "고양이", "캣", "퍼피", "애완동물"]

# 반말 존댓말 모두 잡도록 간단한 형태소 대체 (예: 먹어, 먹어요)
def normalize_text(text):
    replacements = {
        "먹어": "먹어요",
        "했어": "했어요",
        "가": "가요",
        "해": "해요",
        "지냈어": "지냈어요",
        "봤어": "봤어요",
        "있어": "있어요",
        "싸": "싸요",
        "마셔": "마셔요",
        "짖어": "짖어요",
        "가려워해": "가려워요"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

def find_answer(user_input):
    user_input = user_input.lower()
    user_input = normalize_text(user_input)
    words = user_input.split()

    # 주어 탐색
    detected_animal = None
    for animal in animals:
        if animal in words:
            detected_animal = animal
            break

    best_answer = animal_qa_db[("기본",)]
    max_score = 0

    for keywords, answer in animal_qa_db.items():
        keyword_tokens = set()
        for kw in keywords:
            # 키워드 하나하나를 띄어쓰기 단위로 쪼갬 (중복 제거)
            keyword_tokens.update(kw.lower().split())

        overlap = len(set(words) & keyword_tokens)

        # 주어 포함 시 가중치 부여
        animal_bonus = 0
        if detected_animal:
            if detected_animal in keyword_tokens:
                animal_bonus = 2

            # 강아지/개, 고양이/캣 동의어 처리
            if detected_animal == "강아지" and "개" in keyword_tokens:
                animal_bonus = 2
            if detected_animal == "개" and "강아지" in keyword_tokens:
                animal_bonus = 2
            if detected_animal == "고양이" and "캣" in keyword_tokens:
                animal_bonus = 2
            if detected_animal == "캣" and "고양이" in keyword_tokens:
                animal_bonus = 2

        score = overlap + animal_bonus

        if score > max_score:
            max_score = score
            best_answer = answer

    return best_answer


html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>동물 전문 챗봇</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f2f2f2;
      display: flex;
      justify-content: center;
      padding: 30px;
    }
    #chatbox {
      background: white;
      width: 100%;
      max-width: 600px;
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .message {
      margin: 10px 0;
      display: flex;
    }
    .user-msg {
      justify-content: flex-end;
    }
    .bot-msg {
      justify-content: flex-start;
    }
    .bubble {
      padding: 10px 15px;
      border-radius: 20px;
      max-width: 70%;
    }
    .user-msg .bubble {
      background-color: #cce5ff;
      align-self: flex-end;
    }
    .bot-msg .bubble {
      background-color: #d4edda;
      align-self: flex-start;
    }
    #input-box {
      display: flex;
      margin-top: 15px;
    }
    #user-input {
      flex: 1;
      padding: 10px;
      font-size: 16px;
      border-radius: 10px;
      border: 1px solid #ccc;
    }
    button {
      padding: 10px 15px;
      margin-left: 10px;
      font-size: 16px;
      border: none;
      border-radius: 10px;
      background-color: #4CAF50;
      color: white;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <div id="chatbox">
    <h2>🐾 동물 챗봇과 대화하기</h2>
    <div id="messages"></div>
    <div id="input-box">
      <input id="user-input" placeholder="동물에 대해 질문해보세요..." />
      <button onclick="sendMessage()">보내기</button>
    </div>
  </div>

  <script>
    async function sendMessage() {
      const input = document.getElementById("user-input");
      const message = input.value.trim();
      if (!message) return;

      addMessage("user", message);
      input.value = "";

      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message })
        });

        const data = await res.json();
        addMessage("bot", data.reply);
      } catch (err) {
        addMessage("bot", "❌ 오류가 발생했어요. 서버를 확인해보세요.");
      }
    }

    function addMessage(sender, text) {
      const msgDiv = document.createElement("div");
      msgDiv.className = "message " + (sender === "user" ? "user-msg" : "bot-msg");

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.innerText = text;

      msgDiv.appendChild(bubble);
      document.getElementById("messages").appendChild(msgDiv);
      window.scrollTo(0, document.body.scrollHeight);
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(html_template)

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    reply = find_answer(user_msg)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
