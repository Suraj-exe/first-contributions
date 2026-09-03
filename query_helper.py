import sqlite3

def run_optimized_query(db_name, user_id):
    """
    A utility function to safely connect to a local database,
    optimize performance using an index search, and fetch client data.
    """
    # Establish connection
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # SQL Query template requiring rapid client delivery
    sql_query = """
        SELECT id, username, email 
        FROM users 
        WHERE status = 'active' AND id = ?
        LIMIT 1;
    """
    
    try:
        cursor.execute(sql_query, (user_id,))
        result = cursor.fetchone()
        return result
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    print("SQL Query helper initialized successfully.")
