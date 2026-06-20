import sqlite3

def init_db():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_name TEXT NOT NULL,
            crop_type TEXT,
            disease_name TEXT,
            treatment TEXT,
            severity TEXT,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def save_scan(user_id, image_name, crop_type, disease_name, treatment, severity):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scans (user_id, image_name, crop_type, disease_name, treatment, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, image_name, crop_type, disease_name, treatment, severity))
    conn.commit()
    conn.close()

def get_user_scans(user_id):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scans WHERE user_id = ? ORDER BY scan_date DESC', (user_id,))
    scans = cursor.fetchall()
    conn.close()
    return scans

def get_all_scans():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scans ORDER BY scan_date DESC')
    scans = cursor.fetchall()
    conn.close()
    return scans

def delete_scan(scan_id):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scans WHERE id = ?', (scan_id,))
    conn.commit()
    conn.close()

def delete_all_scans():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scans')
    conn.commit()
    conn.close()

def register_user(name, email, password, location):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password, location)
            VALUES (?, ?, ?, ?)
        ''', (name, email, password, location))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def delete_user(user_id):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scans WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def delete_user_scans(user_id):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scans WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    conn.close()
    return users

def get_total_users():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_scans():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM scans')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_disease_stats():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT disease_name, COUNT(*) as count 
        FROM scans 
        WHERE disease_name != "No Disease Detected"
        GROUP BY disease_name 
        ORDER BY count DESC 
        LIMIT 5
    ''')
    stats = cursor.fetchall()
    conn.close()
    return stats

def get_severity_stats():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT severity, COUNT(*) as count 
        FROM scans 
        GROUP BY severity
    ''')
    stats = cursor.fetchall()
    conn.close()
    return stats

def get_healthy_crops():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM scans 
        WHERE disease_name = "No Disease Detected"
    ''')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_recent_scans_with_users():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT scans.*, users.name 
        FROM scans 
        JOIN users ON scans.user_id = users.id 
        ORDER BY scan_date DESC 
        LIMIT 10
    ''')
    scans = cursor.fetchall()
    conn.close()
    return scans

def admin_delete_user(user_id):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scans WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_top_crops():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT crop_type, COUNT(*) as count
        FROM scans
        WHERE crop_type != "Unknown"
        GROUP BY crop_type
        ORDER BY count DESC
        LIMIT 5
    ''')
    crops = cursor.fetchall()
    conn.close()
    return crops

def get_top_farmers():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.name, users.location, COUNT(scans.id) as count
        FROM scans
        JOIN users ON scans.user_id = users.id
        GROUP BY users.id
        ORDER BY count DESC
        LIMIT 5
    ''')
    farmers = cursor.fetchall()
    conn.close()
    return farmers

def get_all_diseases():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT disease_name, crop_type, COUNT(*) as count, severity
        FROM scans
        WHERE disease_name != "No Disease Detected"
        AND disease_name != "Unknown"
        GROUP BY disease_name
        ORDER BY count DESC
    ''')
    diseases = cursor.fetchall()
    conn.close()
    return diseases