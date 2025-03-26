import re
import pymysql
import ollama
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database configuration
DB_USER = "root"
DB_PASSWORD = "aayyriad"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "nl2sql"

# Function to connect to MySQL
def get_db_connection():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor  # Ensures results are dictionaries
        )
        return conn
    except pymysql.MySQLError as err:
        print(f"❌ Database Connection Error: {err}")
        return None

# Function to convert natural language to SQL using Ollama
def convert_nl_to_sql(nl_query):
    try:
        prompt = f"""
        Convert the following natural language question into a SQL query for MySQL:
        Question: {nl_query}
        SQL Query:
        """
        response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])

        if "message" in response and "content" in response["message"]:
            raw_sql = response["message"]["content"].strip()
            sql_query = re.search(r"```sql\n(.*?)\n```", raw_sql, re.DOTALL)
            return sql_query.group(1).strip() if sql_query else raw_sql
        return None
    except Exception as e:
        print(f"❌ Error in query generation: {e}")
        return None

# Home route
@app.route("/")
def home():
    return render_template("index.html")

# Query endpoint
@app.route("/query", methods=["POST"])
def query_database():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        data = request.get_json()
        user_query = data.get("query", "").strip()

        if not user_query:
            return jsonify({"error": "Query is empty"}), 400

        sql_query = convert_nl_to_sql(user_query)
        if not sql_query:
            return jsonify({"error": "Failed to generate SQL query"}), 500

        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            result = cursor.fetchall()  # List of dictionaries (row data)
            columns = cursor.description  # Get column names
            
        column_names = [col[0] for col in columns]  # Extract column names

        return jsonify({"query": sql_query, "columns": column_names, "result": result})

    except pymysql.MySQLError as err:
        return jsonify({"error": f"MySQL Query Error: {err}", "generated_query": sql_query}), 500

    finally:
        if conn:
            conn.close()

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)
# SELECT * FROM employees WHERE salary > 70000;