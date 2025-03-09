#!/usr/bin/env python3
import os
import sys

def generate_directory_structure(startpath, output_file, include_dirs, ignore_patterns):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# ساختار پروژه FastAPI\n\n")
        f.write("```\n")
        
        # فایل‌های روت را ابتدا اضافه کنیم
        root_files = [file for file in os.listdir(startpath) 
                     if os.path.isfile(os.path.join(startpath, file)) 
                     and not any(pattern in file for pattern in ignore_patterns)]
        for file in sorted(root_files):
            f.write(f"{file}\n")
        
        # سپس پوشه‌های اصلی را بررسی کنیم
        for main_dir in include_dirs:
            main_dir_path = os.path.join(startpath, main_dir)
            if os.path.isdir(main_dir_path):
                f.write(f"{main_dir}/\n")
                _write_directory_tree(main_dir_path, f, 1, ignore_patterns)
        
        f.write("```\n")

def _write_directory_tree(path, file, level, ignore_patterns):
    indent = "    " * level
    items = sorted(os.listdir(path))
    
    # ابتدا پوشه‌ها
    for item in items:
        item_path = os.path.join(path, item)
        # بررسی اینکه آیا باید این آیتم را نادیده بگیریم
        if any(pattern in item for pattern in ignore_patterns):
            continue
            
        if os.path.isdir(item_path):
            file.write(f"{indent}{item}/\n")
            _write_directory_tree(item_path, file, level + 1, ignore_patterns)
    
    # سپس فایل‌ها
    for item in items:
        item_path = os.path.join(path, item)
        # بررسی اینکه آیا باید این آیتم را نادیده بگیریم
        if any(pattern in item for pattern in ignore_patterns):
            continue
            
        if os.path.isfile(item_path):
            file.write(f"{indent}{item}\n")

if __name__ == "__main__":
    # پوشه‌های اصلی که می‌خواهیم بررسی کنیم
    include_directories = ["frontend", "app", "docs", "scripts"]
    
    # الگوهایی که می‌خواهیم نادیده بگیریم
    ignore_patterns = ["__pycache__", "__init__.py", ".git", ".idea", ".vscode", ".DS_Store", ".pyc"]
    
    # فایل خروجی در مسیر فعلی
    output_file = "directory_structure.md"
    
    if len(sys.argv) < 2:
        print("استفاده: python script.py [مسیر پروژه]")
        print("مثال: python script.py /path/to/fastapi/project")
        path = input("لطفا مسیر پروژه FastAPI را وارد کنید (پیش‌فرض: مسیر فعلی): ") or os.getcwd()
    else:
        path = sys.argv[1]
    
    if not os.path.exists(path):
        print(f"خطا: مسیر '{path}' وجود ندارد.")
        sys.exit(1)
    
    generate_directory_structure(path, output_file, include_directories, ignore_patterns)
    print(f"ساختار پروژه FastAPI در فایل '{output_file}' در مسیر فعلی ذخیره شد.")