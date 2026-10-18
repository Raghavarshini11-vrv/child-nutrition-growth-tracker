from flask import Flask, render_template, request, redirect, session, send_file
import mysql.connector

app = Flask(__name__)
app.secret_key = "childtracker123"
def calculate_bmi(weight, height):
    if weight and height:
        height_m = height / 100
        return round(weight / (height_m ** 2), 2)
    return None
def get_status_from_bmi(bmi):
    if bmi is None:
        return None

    if bmi < 14:
        return "Severe Malnutrition"
    elif bmi < 18:
        return "Mild Malnutrition"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"
    

# ✅ MySQL Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="project2026@AK",
        database="child_nutrition_tracker",
        autocommit=True
    )

# 🏠 FRONT PAGE
@app.route('/')
def home():
    return render_template('index.html')

# 📝 REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')

        if not role:
            message = "⚠ Please select role"
            return render_template('register.html', message=message)

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        existing = cursor.fetchone()

        if existing:
            message = "⚠ Username already exists!"
        else:
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role)
            )
            db.commit()

        cursor.close()
        db.close()
        return redirect('/login')

    return render_template('register.html', message=message)

# 🔐 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user:
            if password == user[2]:
                # ✅ STORE SESSION
                session['user'] = username
                session['role'] = user[3].strip().lower()

                # ✅ REDIRECT BASED ON ROLE
                if session['role'] == 'admin':
                    return redirect('/admin_dashboard')
                elif session['role'] == 'user':
                    return redirect('/user_dashboard')
                else:
                    message = "⚠ Invalid role in database"
            else:
                message = "❌ Wrong Password"
        else:
            message = "❌ User not found"

        cursor.close()
        db.close()

    return render_template('login.html', message=message)

# ➕ ADD CHILD
@app.route('/add', methods=['GET', 'POST'])
def add_child():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        years = request.form['years']
        months = request.form['months']
        gender = request.form['gender']

        weight = request.form.get('weight')
        height = request.form.get('height')

        # ✅ VALIDATION
        if not weight or not height:
            return "⚠ Weight and Height are required!"

        weight = float(weight)
        height = float(height)

        if height == 0:
            return "⚠ Height cannot be zero!"

        if height < 50 or height > 150:
            return "⚠ Enter valid height (50–150 cm)"

        age = f"{years} Years {months} Months"

        # ✅ BMI
        bmi = weight / ((height / 100) ** 2)
        status = get_status_from_bmi(bmi)

        # ✅ INSERT INTO DB
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO child (name, age, gender, weight, height, bmi, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, age, gender, weight, height, bmi, status))

        db.commit()
        cursor.close()
        db.close()

        return redirect('/admin_dashboard')

    return render_template('add_child.html')

# ✏ EDIT CHILD
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_child(id):
    if 'user' not in session or session['role'] != 'admin':
     return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor()

    if request.method == 'POST':
        name = request.form['name']
        years = request.form['years']
        months = request.form['months']
        gender = request.form['gender']
        weight = float(request.form['weight'])
        height = float(request.form['height'])

        age = f"{years} Years {months} Months"

        bmi = weight / ((height / 100) ** 2)
        status = get_status_from_bmi(bmi)

        cursor.execute("""
            UPDATE child 
            SET name=%s, age=%s, gender=%s, weight=%s, height=%s, bmi=%s, status=%s
            WHERE child_id=%s
        """, (name, age, gender, weight, height, bmi, status, id))

        db.commit()
        cursor.close()
        db.close()

        return redirect('/admin_dashboard')

    cursor.execute("SELECT * FROM child WHERE child_id=%s", (id,))
    child = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template('edit_child.html', child=child)
# ❌ DELETE CHILD
@app.route('/delete/<int:id>')
def delete_child(id):
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM nutrition WHERE child_id=%s", (id,))
    cursor.execute("DELETE FROM child WHERE child_id=%s", (id,))

    db.commit()
    cursor.close()
    db.close()

    return redirect('/admin_dashboard')

# 🍽 ADD NUTRITION
@app.route('/add_nutrition/<int:child_id>', methods=['GET', 'POST'])
def add_nutrition(child_id):
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        breakfast = request.form.get('breakfast')
        lunch = request.form.get('lunch')
        dinner = request.form.get('dinner')
        milk = request.form.get('milk')
        water = request.form.get('water')

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO nutrition (child_id, breakfast, lunch, dinner, milk, water)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (child_id, breakfast, lunch, dinner, milk, water))

        db.commit()
        cursor.close()
        db.close()

        return redirect('/admin_dashboard')

    return render_template("add_nutrition.html", child_id=child_id)

# 👀 VIEW NUTRITION
@app.route('/view_nutrition/<int:child_id>')
def view_nutrition(child_id):
    if 'user' not in session:
        return redirect('/login')
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM nutrition WHERE child_id=%s", (child_id,))
    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("view_nutrition.html", data=data)

@app.route('/delete_nutrition/<int:id>')
def delete_nutrition(id):
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("DELETE FROM nutrition WHERE nutrition_id=%s", (id,))
    db.commit()

    cursor.close()
    db.close()

    return redirect('/admin_dashboard')

# 📊 ADMIN DASHBOARD
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' not in session or session['role'] != 'admin':
        return redirect('/login')

    search = request.args.get('search')

    db = get_db_connection()
    cursor = db.cursor()

    if search:
        cursor.execute("SELECT * FROM child WHERE name LIKE %s", ('%' + search + '%',))
    else:
        cursor.execute("SELECT * FROM child")

    children = cursor.fetchall()

    updated_children = []

    for child in children:
        weight = child[4]
        height = child[5]

        bmi = calculate_bmi(weight, height)
        status = get_status_from_bmi(bmi)

        updated_children.append({
            "child_id": child[0],
            "name": child[1],
            "age": child[2],
            "gender": child[3],
            "weight": weight,
            "height": height,
            "bmi": bmi,
            "status": status
        })

    # ✅ COUNTS
    severe_count = sum(1 for c in updated_children if c["status"] == "Severe Malnutrition")
    mild_count = sum(1 for c in updated_children if c["status"] == "Mild Malnutrition")

    cursor.close()
    db.close()

    return render_template(
        "admin_dashboard.html",
        children=updated_children,
        total=len(updated_children),
        severe_count=severe_count,
        mild_count=mild_count
    )
# 👩‍👧 USER DASHBOARD
@app.route('/user_dashboard')
def user_dashboard():
    if 'user' not in session or session['role'] != 'user':
        return redirect('/login')

    search = request.args.get('search')

    db = get_db_connection()
    cursor = db.cursor()

    if search:
        cursor.execute("SELECT * FROM child WHERE name LIKE %s", ('%' + search + '%',))
    else:
        cursor.execute("SELECT * FROM child")

    children = cursor.fetchall()

    updated_children = []

    for child in children:
        weight = child[4]
        height = child[5]

        bmi = calculate_bmi(weight, height)
        status = get_status_from_bmi(bmi)

        updated_children.append({
            "child_id": child[0],
            "name": child[1],
            "age": child[2],
            "gender": child[3],
            "weight": weight,
            "height": height,
            "bmi": bmi,
            "status": status
        })

    cursor.close()
    db.close()

    return render_template("user_dashboard.html", children=updated_children)

# 📊 CHART
@app.route('/nutrition_chart')
def nutrition_chart():
    if 'user' not in session:
        return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT bmi FROM child")
    data = cursor.fetchall()

    severe = mild = normal = overweight = obese = 0

    for row in data:
        bmi = row[0]
        status = get_status_from_bmi(bmi)

        if status == "Severe Malnutrition":
            severe += 1
        elif status == "Mild Malnutrition":
            mild += 1
        elif status == "Normal":
            normal += 1
        elif status == "Overweight":
            overweight += 1
        elif status == "Obese":
            obese += 1

    cursor.close()
    db.close()

    return render_template(
        "nutrition_chart.html",
        severe=severe,
        mild=mild,
        normal=normal,
        overweight=overweight,
        obese=obese
    )

# 🚪 LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/download_report')
def download_report():
    if 'user' not in session:
        return redirect('/login')

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM child")
    children = cursor.fetchall()

    from reportlab.platypus import SimpleDocTemplate, Table
    from reportlab.lib import colors

    file_path = "report.pdf"

    data = [["Name", "Age", "Gender", "Weight", "Height", "BMI", "Status"]]

    for child in children:
        weight = child[4]
        height = child[5]

        bmi = calculate_bmi(weight, height)
        status = get_status_from_bmi(bmi)

        data.append([
            child[1],
            child[2],
            child[3],
            weight,
            height,
            bmi,
            status
        ])

    pdf = SimpleDocTemplate(file_path)
    table = Table(data)

    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke)
    ])

    pdf.build([table])

    cursor.close()
    db.close()

    return send_file(file_path, as_attachment=True)

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'user' not in session or session['role'] != 'user':
        return redirect('/login')

    response = ""

    if request.method == 'POST':
        user_input = request.form['message'].lower()

        # 🔴 Severe Malnutrition
        if "severe" in user_input:
            response = """⚠ Severe Malnutrition:
- Immediate medical consultation required
- Give high-protein foods: milk, eggs, dal
- Increase meal frequency (5–6 times/day)
- Monitor weight regularly"""

        # 🟠 Mild Malnutrition
        elif "mild" in user_input:
            response = """🟠 Mild Malnutrition:
- Improve diet quality
- Include fruits, vegetables, milk
- Ensure proper meal timings
- Avoid skipping meals"""

        # 🟢 Normal
        elif "normal" in user_input:
            response = """🟢 Healthy Child:
- Maintain balanced diet
- Include proteins, carbs, vitamins
- Encourage physical activity
- Regular health checkups"""

        # 🟡 Overweight
        elif "overweight" in user_input:
            response = """🟡 Overweight:
- Reduce junk food & sugary drinks
- Encourage outdoor activities
- Balanced diet with less fat
- Monitor screen time"""

        # 🍎 Food Suggestions
        elif "food" in user_input or "diet" in user_input:
            response = """🍎 Recommended Foods:
- Milk & dairy products
- Eggs & pulses
- Fruits (banana, apple)
- Green leafy vegetables
- Rice, wheat, cereals"""

        # 📊 BMI Info
        elif "bmi" in user_input:
            response = """📊 BMI (Body Mass Index):
- It measures weight vs height
- Helps identify malnutrition
- Categories:
  Severe, Mild, Normal, Overweight"""

        # 👶 Age-based hint
        elif "age" in user_input:
            response = """👶 Age-based care:
- 1–3 yrs: milk, soft foods, fruits
- 4–6 yrs: balanced diet + activity
- 7+ yrs: proper meals + exercise"""

        else:
            response = """🤖 I can help with:
- Malnutrition types
- Child diet plans
- BMI understanding
- Health suggestions"""

    return render_template("chatbot.html", response=response)

def predict_weight(weights):
    if not weights:
        return 0

    # simple prediction logic (BCA level)
    current_weight = weights[-1]

    # assume +1 kg growth in 3 months
    predicted = current_weight + 1  

    return round(predicted, 2)
def get_growth_trend(weights):
    if len(weights) < 2:
        return "Stable"

    first = weights[0]
    last = weights[-1]

    if last > first:
        return "Increasing"
    elif last < first:
        return "Declining"
    else:
        return "Stable"
import mysql.connector

# 🔹 Get child weight
def get_child_weights(child_id):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="child_nutrition_tracker"
    )

    cursor = conn.cursor()

    cursor.execute("SELECT weight FROM child WHERE child_id=%s", (child_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return [float(row[0])]
    return []


# 🔹 Predict weight
def predict_weight(weights):
    if not weights:
        return 0
    return round(weights[-1] + 1, 2)   # simple logic


# 🔹 Growth trend
def get_growth_trend(weights):
    if len(weights) < 2:
        return "Stable"

    if weights[-1] > weights[0]:
        return "Increasing"
    elif weights[-1] < weights[0]:
        return "Declining"
    else:
        return "Stable"

def extract_years(age_string):
    try:
        return int(age_string.split()[0])
    except:
        return 0

# 🔹 Get child details
def get_child_by_id(child_id):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="project2026@AK",
        database="child_nutrition_tracker"
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM child WHERE child_id=%s", (child_id,))
    child = cursor.fetchone()

    cursor.close()
    conn.close()

    return child


# 🔹 BMI
def calculate_bmi(weight, height_cm):
    if height_cm == 0:
        return 0
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)


# 🔹 Risk
def calculate_risk(bmi, trend, illness_count, nutrition_score):
    score = 100

    if bmi < 18:
        score -= 20

    if trend == "Declining":
        score -= 25

    score -= illness_count * 5
    score -= (100 - nutrition_score) * 0.2

    if score <= 40:
        return "High Risk"
    elif score <= 70:
        return "Moderate Risk"
    else:
        return "Healthy"


# 🔹 Get meals
def get_meals(child_id):
    import mysql.connector

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="project2026@AK",
        database="child_nutrition_tracker"
    )

    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT meal_type FROM meal_log WHERE child_id=%s", (child_id,))
    meals = cursor.fetchall()

    cursor.close()
    conn.close()

    return meals


# 🔹 Nutrition alerts
def check_nutrition(meals):
    protein = sum(1 for m in meals if m['meal_type'].lower() == 'protein')
    iron = sum(1 for m in meals if m['meal_type'].lower() == 'iron')

    alerts = []

    if protein < 2:
        alerts.append("Low Protein Intake")

    if iron == 0:
        alerts.append("Iron Deficiency Risk")

    return alerts


# 🔹 Recommendation
def meal_recommendation(age, bmi):
    if bmi < 18:
        return "Increase protein foods like eggs, milk, dal"
    elif bmi > 25:
        return "Reduce oily and sugary foods"
    else:
        return "Maintain balanced diet"

@app.route('/prediction/<int:child_id>')
def prediction(child_id):
    weights = get_child_weights(child_id)

    predicted = predict_weight(weights)
    trend = get_growth_trend(weights)

    child = get_child_by_id(child_id)

    if child:
        weight = float(child['weight'])
        height = float(child['height'])
        age = extract_years(child['age'])   # ✅ FIX HERE
    else:
        weight, height, age = 0, 1, 0

    bmi = calculate_bmi(weight, height)

    risk = calculate_risk(bmi, trend, 2, 70)

    meals = get_meals(child_id)
    alerts = check_nutrition(meals)

    recommendation = meal_recommendation(age, bmi)

    return render_template("prediction.html",
                           predicted=predicted,
                           trend=trend,
                           risk=risk,
                           alerts=alerts,
                           recommendation=recommendation)
import mysql.connector
def get_child_weights(child_id):
    import mysql.connector

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="project2026@AK",
        database="child_nutrition_tracker"
    )

    cursor = conn.cursor()

    cursor.execute("SELECT weight FROM child WHERE child_id=%s", (child_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return [float(row[0])]
    return []

# ▶ RUN
if __name__ == '__main__':
    app.run(debug=True)