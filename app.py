from flask import Flask, render_template, request, redirect, session
from models import db, User
from deep_translator import GoogleTranslator
from gtts import gTTS
from datetime import date, timedelta
import gtts
import language_tool_python
import json
import speech_recognition as sr
tool = language_tool_python.LanguageTool('en-US')
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "languageapp"

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("login.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already exists!"

        new_user = User(name=name, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter_by(email=email, password=password).first()

    if user:
        session["user_id"] = user.id
        return redirect("/dashboard")

    return "Invalid Email or Password"


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    
    user = User.query.get(session["user_id"])
    level = 1

    if user.xp >= 100:
        level = 2

    if user.xp >= 250:
        level = 3

    if user.xp >= 500:
        level = 4

    progress = user.xp % 100
    return render_template(
        "dashboard.html",
        user=user,
        level=level,
        progress=progress
    )

# ---------------- SAVE LANGUAGE ----------------

@app.route("/save-language", methods=["POST"])
def save_language():
    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    user.selected_language = request.form.get("language")

    db.session.commit()

    return redirect("/dashboard")

@app.route("/family")
def family():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    words = {
        "Father": "తండ్రి",
        "Mother": "తల్లి",
        "Brother": "అన్న / తమ్ముడు",
        "Sister": "అక్క / చెల్లి",
        "Grandfather": "తాత"
    }

    return render_template(
        "family.html",
        user=user,
        words=words
    )


@app.route("/food")
def food():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    words = {
        "Rice": "అన్నం",
        "Water": "నీరు",
        "Milk": "పాలు",
        "Apple": "ఆపిల్",
        "Bread": "బ్రెడ్"
    }

    return render_template(
        "food.html",
        user=user,
        words=words
    )


@app.route("/travel")
def travel():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    words = {
        "Bus": "బస్సు",
        "Train": "రైలు",
        "Airport": "విమానాశ్రయం",
        "Ticket": "టికెట్",
        "Journey": "ప్రయాణం"
    }

    return render_template(
        "travel.html",
        user=user,
        words=words
    )


@app.route("/shopping")
def shopping():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    words = {
        "Shop": "దుకాణం",
        "Price": "ధర",
        "Money": "డబ్బు",
        "Discount": "తగ్గింపు",
        "Bag": "బ్యాగ్"
    }

    return render_template(
        "shopping.html",
        user=user,
        words=words
    )


@app.route("/weather")
def weather():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    words = {
        "Rain": "వర్షం",
        "Sun": "సూర్యుడు",
        "Cloud": "మేఘం",
        "Wind": "గాలి",
        "Storm": "తుఫాను"
    }

    return render_template(
        "weather.html",
        user=user,
        words=words
    )


@app.route("/translate", methods=["POST"])
def translate():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    text = request.form.get("text")
    corrected_text = correct_sentence(text)

    if corrected_text:
        corrected_text = corrected_text[0].upper() + corrected_text[1:]

    if not corrected_text.endswith((".", "!", "?")):
        corrected_text += "."
    

    language_codes = {
        "Telugu": "te",
        "Hindi": "hi",
        "Tamil": "ta",
        "Kannada": "kn",
        "Malayalam": "ml",
        "Marathi": "mr",
        "Gujarati": "gu",
        "Bengali": "bn",
        "Punjabi": "pa"
    }

    translated_text = GoogleTranslator(
        source="en",
        target=language_codes.get(
            user.selected_language,
            "te"
        )
    ).translate(corrected_text)

    level = 1

    if user.xp >= 100:
        level = 2

    if user.xp >= 250:
        level = 3

    if user.xp >= 500:
        level = 4

    progress = user.xp % 100

    return render_template(
        "dashboard.html",
        user=user,
        original_text=text,
        corrected_text=corrected_text,
        translated_text=translated_text,
        level=level,
        progress=progress
    )

def correct_sentence(text):

    matches = tool.check(text)

    print("MATCHES:", matches)

    corrected_text = language_tool_python.utils.correct(
        text,
        matches
    )

    print("CORRECTED:", corrected_text)

    return corrected_text

@app.route("/voice-input")
def voice_input():

    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:

            recognizer.adjust_for_ambient_noise(source)

            audio = recognizer.listen(source)

        text = recognizer.recognize_google(audio)

        return text

    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/speak", methods=["POST"])
def speak():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    text = request.form.get("translated_text")

    print("FORM DATA =", request.form)
    print("TEXT TO SPEAK =", text)

    language_codes = {
        "Telugu": "te",
        "Hindi": "hi",
        "Tamil": "ta",
        "Kannada": "kn",
        "Malayalam": "ml",
        "Marathi": "mr",
        "Gujarati": "gu",
        "Bengali": "bn",
        "Punjabi": "pa"
    }

    tts = gTTS(
        text=text,
        lang=language_codes.get(
            user.selected_language,
            "te"
        )
    )

    tts.save("static/audio/output.mp3")

    return redirect("/dashboard")
# ---------------- LEARN PAGE ----------------

@app.route("/learn")
def learn():
    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    with open("data/vocabulary.json", "r", encoding="utf-8") as file:
        vocabulary = json.load(file)

    words = vocabulary.get(user.selected_language, {})

    return render_template("learn.html", user=user, words=words)


# ---------------- COMPLETE LESSON ----------------

@app.route("/complete-lesson", methods=["POST"])
def complete_lesson():
    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    user.xp = (user.xp or 0) + 10

    db.session.commit()

    return redirect("/dashboard")


# ---------------- QUIZ ----------------

@app.route("/quiz")
def quiz():
    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    return render_template("quiz.html", user=user)


# ---------------- CHECK QUIZ ----------------

@app.route("/check-quiz", methods=["POST"])
def check_quiz():
    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    score = 0

    results = []

    questions = [
        ("q1", "Namaste"),
        ("q2", "Dhanyavad"),
        ("q3", "Dost"),
        ("q4", "Pani"),
        ("q5", "Khana")
    ]

    for q, correct_answer in questions:

        user_answer = request.form.get(q)

        if user_answer == correct_answer:

            score += 1

            results.append(
                f"{q.upper()} ✅ Correct"
            )

        else:

            results.append(
                f"{q.upper()} ❌ Wrong"
            )

    if score >= 3:

        user.xp += 20

        today = date.today()

        if user.last_quiz_date:

            last_date = date.fromisoformat(
                user.last_quiz_date
            )

            if today - last_date == timedelta(days=1):
                user.streak += 1

            elif today - last_date > timedelta(days=1):
                user.streak = 1

        else:
            user.streak = 1

        user.last_quiz_date = str(today)

        db.session.commit()

        status = "🎉 Quiz Passed!"
        status_class = "pass"

    else:

        status = "❌ Quiz Failed!"
        status_class = "fail"

    return render_template(
        "quiz_result.html",
        user=user,
        score=score,
        results=results,
        status=status,
        status_class=status_class
    )

@app.route("/food-quiz")
def food_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    return render_template(
        "food_quiz.html",
        user=user
    )


@app.route("/check-food-quiz", methods=["POST"])
def check_food_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    score = 0

    if request.form.get("q1") == "అన్నం":
        score += 1

    if request.form.get("q2") == "నీరు":
        score += 1

    if score == 2:
        user.xp += 10
        db.session.commit()

    return render_template(
        "quiz_result.html",
        user=user,
        score=score,
        results=[f"Question 1: {'✅ Correct' if request.form.get('q1') == 'అన్నం' else '❌ Wrong'}",
                 f"Question 2: {'✅ Correct' if request.form.get('q2') == 'నీరు' else '❌ Wrong'}"],
        status="🎉 Quiz Passed!" if score == 2 else "❌ Quiz Failed!",
        status_class="pass" if score == 2 else "fail"
    )

@app.route("/family-quiz")
def family_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    return render_template(
        "family_quiz.html",
        user=user
    )

@app.route("/check-family-quiz", methods=["POST"])
def check_family_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    score = 0

    if request.form.get("q1") == "తండ్రి":
        score += 1

    if request.form.get("q2") == "తల్లి":
        score += 1

    if score == 2:
        user.xp += 10
        db.session.commit()

    return render_template(
        "quiz_result.html",
        user=user,
        score=score,
        results=[
            f"Question 1: {'✅ Correct' if request.form.get('q1') == 'తండ్రి' else '❌ Wrong'}",
            f"Question 2: {'✅ Correct' if request.form.get('q2') == 'తల్లి' else '❌ Wrong'}"
        ],
        status="🎉 Quiz Passed!" if score == 2 else "❌ Quiz Failed!",
        status_class="pass" if score == 2 else "fail"
    )




@app.route("/travel-quiz")
def travel_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    return render_template(
        "travel_quiz.html",
        user=user
    )
@app.route("/check-travel-quiz", methods=["POST"])
def check_travel_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    score = 0

    if request.form.get("q1") == "బస్సు":
        score += 1

    if request.form.get("q2") == "రైలు":
        score += 1

    if score == 2:
        user.xp += 10
        db.session.commit()

    return render_template(
        "quiz_result.html",
        user=user,
        score=score,
        results=[
            f"Question 1: {'✅ Correct' if request.form.get('q1') == 'బస్సు' else '❌ Wrong'}",
            f"Question 2: {'✅ Correct' if request.form.get('q2') == 'రైలు' else '❌ Wrong'}"
        ],
        status="🎉 Quiz Passed!" if score == 2 else "❌ Quiz Failed!",
        status_class="pass" if score == 2 else "fail"
    )


@app.route("/shopping-quiz")
def shopping_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    return render_template(
        "shopping_quiz.html",
        user=user
    )

@app.route("/check-shopping-quiz", methods=["POST"])
def check_shopping_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    score = 0

    if request.form.get("q1") == "డబ్బు":
        score += 1

    if request.form.get("q2") == "ధర":
        score += 1

    if score == 2:
        user.xp += 10
        db.session.commit()

    return render_template(
        "quiz_result.html",
        user=user,
        score=score,
        results=[
            f"Question 1: {'✅ Correct' if request.form.get('q1') == 'డబ్బు' else '❌ Wrong'}",
            f"Question 2: {'✅ Correct' if request.form.get('q2') == 'ధర' else '❌ Wrong'}"
        ],
        status="🎉 Quiz Passed!" if score == 2 else "❌ Quiz Failed!",
        status_class="pass" if score == 2 else "fail"
    )


@app.route("/weather-quiz")
def weather_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    return render_template(
        "weather_quiz.html",
        user=user
    )

@app.route("/check-weather-quiz", methods=["POST"])
def check_weather_quiz():

    if "user_id" not in session:
        return redirect("/")

    user = User.query.get(session["user_id"])

    score = 0

    if request.form.get("q1") == "వర్షం":
        score += 1

    if request.form.get("q2") == "సూర్యుడు":
        score += 1

    if score == 2:
        user.xp += 10
        db.session.commit()

    return render_template(
        "quiz_result.html",
        user=user,
        score=score,
        results=[
            f"Question 1: {'✅ Correct' if request.form.get('q1') == 'వర్షం' else '❌ Wrong'}",
            f"Question 2: {'✅ Correct' if request.form.get('q2') == 'సూర్యుడు' else '❌ Wrong'}"
        ],
        status="🎉 Quiz Passed!" if score == 2 else "❌ Quiz Failed!",
        status_class="pass" if score == 2 else "fail"
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)
