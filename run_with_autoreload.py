"""
Script để chạy bot với auto-reload khi có thay đổi file
"""
import sys
import time
import subprocess
import signal
from pathlib import Path

# Global process để tracking
bot_process = None

def start_bot():
    """Khởi động bot"""
    global bot_process
    
    if bot_process:
        print("🛑 Đang dừng bot...")
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bot_process.kill()
            bot_process.wait()
        except Exception as e:
            print(f"⚠️  Lỗi khi dừng bot: {e}")
    
    print("🚀 Đang khởi động bot...")
    bot_process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    print("✅ Bot đã khởi động!")
    return bot_process

def watch_files():
    """Watch files và restart bot khi có thay đổi"""
    watch_dir = Path.cwd()
    file_mtimes = {}
    
    # Lấy modification time ban đầu
    for py_file in watch_dir.rglob('*.py'):
        # Skip .venv và __pycache__
        if '.venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        try:
            file_mtimes[py_file] = py_file.stat().st_mtime
        except Exception:
            pass
    
    last_restart = time.time()
    
    while True:
        try:
            time.sleep(1)
            
            # Check nếu bot bị crash
            if bot_process and bot_process.poll() is not None:
                print("\n⚠️  Bot đã dừng! Khởi động lại...")
                start_bot()
                last_restart = time.time()
                continue
            
            # Check file changes
            for py_file in watch_dir.rglob('*.py'):
                if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                    continue
                
                try:
                    current_mtime = py_file.stat().st_mtime
                    
                    if py_file not in file_mtimes:
                        file_mtimes[py_file] = current_mtime
                        continue
                    
                    if current_mtime != file_mtimes[py_file]:
                        # Debounce: tránh restart liên tục
                        if time.time() - last_restart < 2:
                            file_mtimes[py_file] = current_mtime
                            continue
                        
                        print(f"\n📝 Phát hiện thay đổi: {py_file.name}")
                        print("🔄 Đang restart bot...")
                        file_mtimes[py_file] = current_mtime
                        start_bot()
                        last_restart = time.time()
                        break
                        
                except Exception:
                    pass
                    
        except KeyboardInterrupt:
            raise

def signal_handler(sig, frame):
    """Xử lý Ctrl+C"""
    global bot_process
    print("\n\n🛑 Đang dừng bot...")
    if bot_process:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
        except Exception:
            bot_process.kill()
    print("✅ Bot đã dừng")
    sys.exit(0)

def main():
    """Main function"""
    global bot_process
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("🤖 Bot Auto-Reload Mode")
    print("=" * 60)
    print("ℹ️  Bot sẽ tự động restart khi bạn save file .py")
    print("ℹ️  Nhấn Ctrl+C để dừng")
    print("=" * 60)
    print()
    
    # Khởi động bot lần đầu
    start_bot()
    
    # Hiển thị output từ bot trong background thread
    import threading
    
    def read_output():
        global bot_process
        while True:
            if bot_process and bot_process.stdout:
                try:
                    line = bot_process.stdout.readline()
                    if line:
                        print(line, end='', flush=True)
                    elif bot_process.poll() is not None:
                        break
                except Exception:
                    break
            time.sleep(0.1)
    
    output_thread = threading.Thread(target=read_output, daemon=True)
    output_thread.start()
    
    # Watch files
    try:
        watch_files()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
