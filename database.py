import sqlite3

def init_db():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT NOT NULL,
            crop_type TEXT,
            disease_name TEXT,
            treatment TEXT,
            severity TEXT,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_scan(image_name, crop_type, disease_name, treatment, severity):
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO scans (image_name, crop_type, disease_name, treatment, severity)
        VALUES (?, ?, ?, ?, ?)
    ''', (image_name, crop_type, disease_name, treatment, severity))
    
    conn.commit()
    conn.close()

def get_all_scans():
    conn = sqlite3.connect('crop_disease.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM scans ORDER BY scan_date DESC')
    scans = cursor.fetchall()
    
    conn.close()
    return scans