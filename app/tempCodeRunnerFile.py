from flask import Flask, request, jsonify, render_template
import mysql.connector
import subprocess  # Assuming using subprocess to call Ollama CLI
import json
from config import DB_CONFIG, OLLAMA_COMMAND  # Importing configurations

app = Flask(__name__)

def query_db(sql_query):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql_query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def convert_nl_to_sql(nl_query):
    # Build a prompt for the LLM that includes the schema context
    prompt = (
        "You are given a MySQL table 'employees' with the following columns:\n"
        "id, name, department, salary.\n"
        "Convert the following natural language query into a valid SQL query for this table:\n"
        f"'{nl_query}'"
    )
    # Example: using a CLI call to Ollama. Adjust command and flags per your installation.
    try:
        result = subprocess.run(
            [OLLAMA_COMMAND, "llama3", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        # Extract and clean the SQL command from the output.
        sql_query = result.stdout.strip()
        return sql_query
    except subprocess.CalledProcessError as e:
        print("Error calling Ollama:", e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    data = request.get_json()
    nl_query = data.get('query')
    
    # Convert NL query to SQL using Ollama llama3
    sql_query = convert_nl_to_sql(nl_query)
    
    if not sql_query:
        return jsonify({'error': 'Failed to generate SQL query'}), 500

    try:
        results = query_db(sql_query)
        return jsonify({'sql': sql_query, 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
