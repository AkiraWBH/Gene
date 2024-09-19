from cx_Freeze import setup, Executable

# Đặt tên file python chính của bạn, ví dụ 'main.py'
executables = [Executable("khung.py", target_name="autochat.exe")]

setup(
    name="Auto Chat",
    version="1.0",
    description="Auto Chat Application",
    options={"build_exe": {"include_files": ["path/to/extra_files"]}},
    executables=executables,
)
