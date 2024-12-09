import os
import subprocess
import psycopg2
import datetime
import requests

# Configurações
CONFIG = {
    "backend_url": "http://192.168.10.13:8080/api/orders/",
    "frontend_url": "http://192.168.10.13",
    "rabbitmq_url": "http://192.168.10.13:15276",
    "postgres_host": "192.168.10.13",
    "postgres_port": 5432,
    "postgres_user": "postgres",
    "postgres_password": "1234",
    "postgres_db": "teste01",
    "backup_dir": "/home/ubuntu/backup_postgres/",
    "log_dir": "/home/ubuntu/monitor_logs/",
    "windows_laser": "/mnt/windows_laser",
    "windows_laser_facas_ok": "/mnt/windows_laser_facas_ok",
    "hostnames_to_notify": ["recepcao-desktop"]
}

# Funções de Monitoramento
def check_backend():
    try:
        response = requests.get(CONFIG["backend_url"], timeout=5)
        return response.status_code == 200
    except:
        return False

def check_frontend():
    try:
        response = requests.get(CONFIG["frontend_url"], timeout=5)
        return response.status_code == 200
    except:
        return False

def check_rabbitmq():
    try:
        response = requests.get(CONFIG["rabbitmq_url"], timeout=5)
        return response.status_code == 200
    except:
        return False

def check_postgres():
    try:
        conn = psycopg2.connect(
            host=CONFIG["postgres_host"],
            port=CONFIG["postgres_port"],
            user=CONFIG["postgres_user"],
            password=CONFIG["postgres_password"],
            database=CONFIG["postgres_db"]
        )
        conn.close()
        return True
    except:
        return False

def check_windows_files():
    try:
        laser_files = set(os.listdir(CONFIG["windows_laser"]))
        facas_ok_files = set(os.listdir(CONFIG["windows_laser_facas_ok"]))
        return laser_files and facas_ok_files
    except:
        return False

def manage_backups():
    try:
        backups = sorted(
            [f for f in os.listdir(CONFIG["backup_dir"]) if "backup" in f],
            key=lambda x: os.path.getmtime(os.path.join(CONFIG["backup_dir"], x))
        )
        # Mantém os dois backups mais recentes
        for old_backup in backups[:-2]:
            os.remove(os.path.join(CONFIG["backup_dir"], old_backup))
        return True
    except:
        return False

def clean_logs():
    try:
        one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        for log in os.listdir(CONFIG["log_dir"]):
            log_path = os.path.join(CONFIG["log_dir"], log)
            if os.path.getmtime(log_path) < one_week_ago.timestamp():
                os.remove(log_path)
        return True
    except:
        return False

def log_results(results):
    os.makedirs(CONFIG["log_dir"], exist_ok=True)
    log_file = os.path.join(CONFIG["log_dir"], f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(log_file, "w") as file:
        file.write(f"Monitoring Results - {datetime.datetime.now()}\n")
        for key, value in results.items():
            file.write(f"{key}: {'PASS' if value else 'FAIL'}\n")
    return log_file

def notify_hostnames(results):
    signal = "PASS" if all(results.values()) else "FAIL"
    for hostname in CONFIG["hostnames_to_notify"]:
        subprocess.run(["echo", signal, "|", "nc", hostname, "8080"])

# Rotina Principal
def monitor():
    results = {
        "Backend": check_backend(),
        "Frontend": check_frontend(),
        "RabbitMQ": check_rabbitmq(),
        "PostgreSQL": check_postgres(),
        "Windows Files": check_windows_files(),
        "Backups": manage_backups(),
        "Log Cleanup": clean_logs()
    }
    log_results(results)
    notify_hostnames(results)

if __name__ == "__main__":
    monitor()

