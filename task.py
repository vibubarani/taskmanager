import mysql.connector
import subprocess
import sys
import os

def generate_with_phi(prompt):
    try:
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        kara_prompt = f"You are Kara, a project management assistant. Keep the response brief and friendly. Never mention being an AI, Phi, or language model. {prompt}"
        result = subprocess.run(
            ['ollama', 'run', 'phi3.5', kara_prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            env=my_env
        )
        output = result.stdout.strip()
        output_lines = [
            line for line in output.split('\n') 
            if not any(x in line.lower() for x in [
                'phi', 'ai', 'language model', 'artificial', 
                'failed to get console mode'
            ])
        ]
        return ' '.join(output_lines)
    except Exception as e:
        return "Hi! Ready to help with your projects!"

def execute_query(cursor, db_connection, query, params=None):
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        result = cursor.fetchall()
        db_connection.commit()
        return result
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        db_connection.rollback()
        return None

def connect_to_database():
    try:
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="vibu@1808",
            database="ProjectManagement"
        )
    except mysql.connector.Error as err:
        print(f"Failed to connect to database: {err}")
        sys.exit(1)

def handle_admin_query(query):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    
    try:
        # Execute the query and get results
        results = execute_query(cursor, db_connection, query)
        
        if results is not None:
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            # Print results in a formatted table
            print("\nResults:")
            print("=" * 100)
            print(" | ".join(f"{col:20}" for col in column_names))
            print("=" * 100)
            
            for row in results:
                print(" | ".join(f"{str(val):20}" for val in row))
            
            print("=" * 100)
            print(f"Total rows: {len(results)}")
        
    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        cursor.close()
        db_connection.close()

def admin_interaction():
    print("\nKara: Welcome, admin! I can help you query the project management database.")
    print("You can ask me to:")
    print("1. Show all projects")
    print("2. View employee workload")
    print("3. Check project status")
    print("4. Or enter your own custom SQL query")
    
    while True:
        query = input("\nEnter your query (or 'exit' to quit): ").strip()
        
        if query.lower() == 'exit':
            print("Kara: Goodbye! Have a great day!")
            break
        
        if query == "1":
            query = "SELECT * FROM ProjectTasks ORDER BY task_date DESC"
        elif query == "2":
            query = """
                SELECT person_name, COUNT(*) as project_count, 
                SUM(time_sheet) as total_hours
                FROM ProjectTasks 
                GROUP BY person_name
            """
        elif query == "3":
            query = """
                SELECT project_name, person_name, task_date, 
                task_description, time_sheet
                FROM ProjectTasks 
                WHERE task_date >= CURDATE()
                ORDER BY task_date ASC
            """
        
        # Process the query
        handle_admin_query(query)
        
        # Generate insights about the results
        insight_prompt = generate_with_phi("Provide a brief observation about the query results")
        print(f"\nKara: {insight_prompt}")
        
        follow_up = input("\nWould you like to run another query? (yes/no): ").strip().lower()
        if follow_up != 'yes':
            print("Kara: Goodbye! Have a great day!")
            break

def employee_task_update(user_name):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()

    try:
        greeting = generate_with_phi(f"Greet {user_name} in 8 words or less.")
        print(f"\nKara: {greeting}\n")

        fetch_projects_query = """
            SELECT id, project_name, task_date 
            FROM ProjectTasks 
            WHERE LOWER(person_name) = LOWER(%s)
        """
        cursor.execute(fetch_projects_query, (user_name,))
        projects = cursor.fetchall()

        if not projects:
            print(f"Kara: I don't see any projects assigned to you yet, {user_name}.")
            return

        print(f"\nKara: Here are your current projects, {user_name}:")
        for project in projects:
            project_id, project_name, task_date = project
            description = handle_admin_query(f"Describe the project '{project_name}' in 8 words.")
            print(f"""
Project ID: {project_id}
Project Name: {project_name}
Task Date: {task_date}
{'='*50}""")

        while True:
            try:
                project_id = int(input("\nKara: Which project would you like to update? (Enter Project ID): "))
                break
            except ValueError:
                print("Please enter a valid number for the Project ID.")

        task_description = input("Please describe your task: ").strip()
        while True:
            try:
                time_spent = float(input("How many hours did you spend on this task? "))
                if time_spent < 0:
                    print("Please enter a positive number of hours.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number for hours spent.")

        update_task_query = """
            UPDATE ProjectTasks 
            SET task_description = %s, time_sheet = %s 
            WHERE id = %s AND LOWER(person_name) = LOWER(%s)
        """
        result = execute_query(cursor, db_connection, update_task_query, 
                     (task_description, time_spent, project_id, user_name))
        
        print(f"\nKara: Great! I've updated your task for Project ID {project_id}:")
        print(f"Task: {task_description}")
        print(f"Time logged: {time_spent} hours")

        if time_spent > 5:
            motivation = generate_with_phi("Give a 5-word encouragement for hard work.")
            print(f"\nKara: {motivation}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        db_connection.close()

def main():
    print("\nKara: Hello! I'm Kara, your project management assistant.")
    
    while True:
        role = input("\nEnter your role (admin/employee): ").strip().lower()
        if role == "employee":
            user_name = input("Enter your name: ").strip()
            employee_task_update(user_name)
            break
        elif role == "admin":
            admin_interaction()
            break
        else:
            print("Please enter either 'admin' or 'employee'.")

if __name__ == "__main__":
    main()