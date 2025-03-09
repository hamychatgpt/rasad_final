import os
import re
import chardet

def detect_encoding(file_path):
    """تشخیص encoding فایل"""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding'] or 'utf-8'  # استفاده از utf-8 به عنوان پیش‌فرض

def remove_persian_comments(content, file_ext):
    """حذف کامنت‌های فارسی از کد"""
    if file_ext == '.py':
        # حذف کامنت‌های تک خطی پایتون (# ...)
        content = re.sub(r'#[^\n]*[\u0600-\u06FF]+[^\n]*\n', '\n', content)
        # حذف کامنت‌های چند خطی پایتون (''' ... ''' or """ ... """)
        content = re.sub(r'(?:\'\'\'|\"\"\")[^\n]*[\u0600-\u06FF]+.*?(?:\'\'\'|\"\"\")', '', content, flags=re.DOTALL)
    elif file_ext in ['.js', '.html']:
        # حذف کامنت‌های تک خطی جاوااسکریپت (// ...)
        content = re.sub(r'//[^\n]*[\u0600-\u06FF]+[^\n]*\n', '\n', content)
        # حذف کامنت‌های چند خطی جاوااسکریپت و HTML (/* ... */)
        content = re.sub(r'/\*.*?[\u0600-\u06FF]+.*?\*/', '', content, flags=re.DOTALL)
        # برای HTML، حذف کامنت‌ها (<!-- ... -->)
        if file_ext == '.html':
            content = re.sub(r'<!--.*?[\u0600-\u06FF]+.*?-->', '', content, flags=re.DOTALL)
    
    return content

def get_tree_representation(base_path, path):
    """ایجاد نمایش درختی از مسیر فایل"""
    rel_path = os.path.relpath(path, base_path)
    parts = rel_path.split(os.sep)
    
    result = ""
    for i, part in enumerate(parts):
        if i == 0:
            result += part + "\n"
        else:
            prefix = "│   " * (i-1) + "├── " if i < len(parts)-1 else "│   " * (i-1) + "└── "
            result += prefix + part + "\n"
    
    return result.rstrip()

def get_code_files(directory, code_extensions):
    """دریافت تمام فایل‌های کد در یک دایرکتوری و زیردایرکتوری‌های آن"""
    code_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1] in code_extensions:
                code_files.append(os.path.join(root, file))
    
    return code_files

def document_code_file(file_path, base_path, code_extensions):
    """مستندسازی یک فایل کد و بازگرداندن محتوای مارک‌داون"""
    file_ext = os.path.splitext(file_path)[1]
    if file_ext not in code_extensions:
        return ""
    
    md_content = f"\n## {os.path.basename(file_path)}\n\n"
    
    # اضافه کردن مسیر فایل به صورت درختی
    tree_path = get_tree_representation(base_path, file_path)
    md_content += f"```\n{tree_path}\n```\n\n"
    
    # اضافه کردن محتوای کد
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        
        # حذف کامنت‌های فارسی
        content = remove_persian_comments(content, file_ext)
        
        # اضافه کردن کد به مارک‌داون با highlighting مناسب
        if file_ext == '.py':
            md_content += f"```python\n{content}\n```\n\n"
        elif file_ext == '.js':
            md_content += f"```javascript\n{content}\n```\n\n"
        elif file_ext == '.html':
            md_content += f"```html\n{content}\n```\n\n"
    except Exception as e:
        md_content += f"Error reading file: {str(e)}\n\n"
    
    return md_content

def document_directory(directory, project_root, code_extensions):
    """ایجاد فایل مستندسازی مارک‌داون برای یک دایرکتوری"""
    rel_path = os.path.relpath(directory, project_root)
    
    if rel_path == '.':
        md_filename = 'project_root.md'
        md_title = "Documentation for Project Root"
    else:
        md_filename = f"{os.path.basename(directory)}.md"
        md_title = f"Documentation for {rel_path}"
    
    md_path = os.path.join(directory, md_filename)
    md_content = f"# {md_title}\n\n"
    
    # دریافت تمام فایل‌های کد در این دایرکتوری و زیردایرکتوری‌ها
    code_files = get_code_files(directory, code_extensions)
    
    # مستندسازی هر فایل کد
    for file_path in sorted(code_files):
        md_content += document_code_file(file_path, directory, code_extensions)
    
    # نوشتن فایل مارک‌داون
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"Created documentation for {rel_path} in {md_path}")

def document_project(project_root):
    """مستندسازی تمام فایل‌های کد در پروژه و ایجاد فایل‌های مارک‌داون برای هر پوشه"""
    CODE_EXTENSIONS = ['.py', '.js', '.html']
    
    # ایجاد یک مجموعه برای پیگیری دایرکتوری‌هایی که قبلاً پردازش شده‌اند
    processed_dirs = set()
    
    # ابتدا ریشه پروژه را مستندسازی می‌کنیم
    document_directory(project_root, project_root, CODE_EXTENSIONS)
    processed_dirs.add(project_root)
    
    # پیمایش دایرکتوری پروژه
    for root, _, _ in os.walk(project_root):
        # رد کردن پوشه‌های محیط مجازی یا سایر پوشه‌های قابل چشم‌پوشی
        if any(ignore in root for ignore in ['venv', '__pycache__', '.git']):
            continue
        
        # مستندسازی این دایرکتوری اگر شامل فایل‌های کد باشد و قبلاً پردازش نشده باشد
        if root not in processed_dirs:
            code_files = get_code_files(root, CODE_EXTENSIONS)
            if code_files:
                document_directory(root, project_root, CODE_EXTENSIONS)
                processed_dirs.add(root)

if __name__ == "__main__":
    # دریافت مسیر ریشه پروژه
    project_root = input("Enter the project root directory path (default is current directory): ").strip()
    if not project_root:
        project_root = os.getcwd()
    
    if not os.path.isdir(project_root):
        print(f"Error: {project_root} is not a valid directory.")
    else:
        document_project(project_root)
        print("Documentation completed successfully!")