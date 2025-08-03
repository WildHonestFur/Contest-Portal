from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta, timezone
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

creds_json = os.environ.get("GOOGLE_CREDS_JSON")
creds_dict = json.loads(creds_json)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open("Test").worksheet("Participants")
ans = client.open("Test").worksheet("Answers")
testtimes = client.open("Test").worksheet("Test")


def isover():
    times = testtimes.col_values(1)
    times.pop(0)

    now = datetime.now(timezone.utc)
    ninety_min = timedelta(minutes=90)
    
    curnext = None

    start_times = [
        datetime.combine(now.date(), datetime.strptime(t, "%H:%M:%S").time()).replace(tzinfo=timezone.utc)
        for t in times
    ]

    for start in start_times:
        end = start + ninety_min
        if start <= now < end:
            curnext = start
            break
        elif now < start:
            if curnext is None or start < curnext:
                curnext = start

    return curnext == None


@app.route("/nexttime", methods=["GET", "POST"])
def nexttime():
    return render_template("nexttime.html")

@app.route("/", methods=["GET", "POST"])
def form():
    if isover():
        return render_template("nexttime.html")
    if request.method == "POST":
        name = request.form["name"]
        profile = request.form["profile"]

        session["profile"] = profile
        session["name"] = name

        ids = sheet.col_values(2)
        ids.pop(0)            

        if profile not in ids:
            sheet.append_row([name, profile, 'info'])
            return redirect(url_for("round"))           
    
    return render_template("form.html")

@app.route("/round", methods=["GET", "POST"])
def round():
    if isover():
        return render_template("nexttime.html")
    if "profile" not in session or "name" not in session:
        return redirect(url_for("form"))
    
    profile = session["profile"]
    name = session["name"]

    ids = sheet.get_all_values()
    ids.pop(0)
    
    for row in ids:
        if row[1] == profile and row[0] == name:
            round_selected = row[3]
            status = row[2]

            if round_selected == '':
                continue
            if status == 'info':
                return redirect(url_for("info"))
            if status == 'started':
                return redirect(url_for("test"))
            if status == 'completed':
                return redirect(url_for("done"))
    
    if request.method == "POST":
        r = request.form["round"]
        session["round"] = r
        
        ids = sheet.col_values(2)
        ids.pop(0)
        sheet.update_cell(ids.index(session["profile"])+2, 4, r)

        return redirect(url_for("info"))
    
    return render_template("round.html")

@app.route("/info", methods=["GET", "POST"])
def info():
    if isover():
        return render_template("nexttime.html")
    if "profile" not in session or "name" not in session:
        return redirect(url_for("form"))
    
    profile = session["profile"]
    name = session["name"]

    ids = sheet.get_all_values()
    ids.pop(0)
    
    for row in ids:
        if row[1] == profile and row[0] == name:
            round_selected = row[3]
            status = row[2]

            if round_selected == '':
                return redirect(url_for("round"))
            if status == 'started':
                return redirect(url_for("test"))
            if status == 'completed':
                return redirect(url_for("done"))

    times = testtimes.col_values(1)
    times.pop(0)

    now = datetime.now(timezone.utc)
    ninety_min = timedelta(minutes=90)

    curnext = None
    ses = 1

    start_times = [
        datetime.combine(now.date(), datetime.strptime(t, "%H:%M:%S").time()).replace(tzinfo=timezone.utc)
        for t in times
    ]

    for start in start_times:
        end = start + ninety_min
        if start <= now < end:
            curnext = start
            break
        elif now < start:
            if curnext is None or start < curnext:
                curnext = start
        ses += 1

    session["session"] = ses
    
    if request.method == "POST":
        ids = sheet.col_values(2)
        ids.pop(0)

        sheet.update_cell(ids.index(session["profile"])+2, 7, str(session["session"]))
        sheet.update_cell(ids.index(session["profile"])+2, 3, "started")
        return redirect(url_for("test"))

    return render_template("info.html", start_time=curnext.isoformat())


@app.route("/contest", methods=["GET", "POST"])
def test():
    if isover():
        return render_template("nexttime.html")
    if "profile" not in session or "name" not in session:
        return redirect(url_for("form"))
    
    profile = session["profile"]
    name = session["name"]

    ids = sheet.get_all_values()
    ids.pop(0)
    
    for row in ids:
        if row[1] == profile and row[0] == name:
            round_selected = row[3]
            status = row[2]

            if round_selected == '':
                return redirect(url_for("info"))
            if status == 'info':
                return redirect(url_for("info"))
            if status == 'completed':
                return redirect(url_for("done"))
    
    questions = {
        "Algebra": [
            {
                "id": "q1",
                "number": "1",
                "type": "text",
                "text": "What is the answer to this question? A lot of stuff. This is filling up some space. I want to test if lines wrap or not."
            },
            {
                "number": "2",
                "type": "text",
                "text": r"Solve the following integral: \[ \int_0^1 \frac{1}{x^2(1-x)} \, dx \]"
            },
            {
                "number": "3",
                "type": "mcq",
                "text": "Which of the following is a prime number?",
                "options": ["12", "17", "21", "1"]
            }
        ],
        "Geometry": [
            {
                "number": "4",
                "type": "text",
                "text": "Geometry text input question."
            },
            {
                "number": "5",
                "type": "text",
                "text": r"Solve the following integral: \[ \int_0^1 \frac{1}{x^2(1-x)} \, dx \]"
            },
            {
                "number": "6",
                "type": "text",
                "text": r"Solve the following integral: \[ \int_0^1 \frac{1}{x^2(1-x)} \, dx \]"
            },
            {
                "number": "7",
                "type": "mcq",
                "text": r"Does it work?",
                "options": ["12", "17", "21", "1"]
            }
        ]
    }
    qlist = []
    for i in questions:
        for j in questions[i]:
            qlist.append(j)

    if request.method == "POST":
        answers = []
        for q in qlist:
            key = f"q{q['number']}"
            answers.append(request.form.get(key, "").strip())

        ans.append_row([session["name"], session["profile"]] + answers)
        
        time = datetime.now(timezone.utc).strftime("%H:%M:%S")
        ids = sheet.col_values(2)
        ids.pop(0)
        sheet.update_cell(ids.index(session["profile"])+2, 3, "completed")
        sheet.update_cell(ids.index(session["profile"])+2, 6, time)

        return redirect(url_for("done"))

    times = testtimes.col_values(1)
    times.pop(0)

    now = datetime.now(timezone.utc)

    end = datetime.combine(now.date(), datetime.strptime(times[session["session"]-1], "%H:%M:%S").time()).replace(tzinfo=timezone.utc)
    end = end + timedelta(minutes=90)

    return render_template("test.html", questions_by_category=questions, qlist=qlist, cround = session["round"].capitalize(), end_time = end.isoformat())

@app.route("/done")
def done():
    if isover():
        return render_template("nexttime.html")
    if "profile" not in session or "name" not in session:
        return redirect(url_for("form"))
    
    profile = session["profile"]
    name = session["name"]

    ids = sheet.get_all_values()
    ids.pop(0)
    
    for row in ids:
        if row[1] == profile and row[0] == name:
            round_selected = row[3]
            status = row[2]

            if round_selected == '':
                return redirect(url_for("round"))
            if status == 'info':
                return redirect(url_for("info"))
            if status == 'started':
                return redirect(url_for("test"))
    
    return render_template("thanks.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1000))
    app.run(host="0.0.0.0", port=port)
