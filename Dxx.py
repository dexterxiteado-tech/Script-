#!/usr/bin/env python3
"""
Unity Asset Modifier - Tool for Termux
Sistema de login con GitHub como base de datos
Soporte para archivos ofuscados y sin extensión
"""

import os
import sys
import json
import shutil
import hashlib
import termios
import tty
import urllib.request
import urllib.error
import base64
import UnityPy
from datetime import datetime
import time

# ==================== CONFIGURACIÓN ====================
CONFIG = {
    "assets_folder": "/storage/emulated/0/assets/",
    "dumps_folder": "/storage/emulated/0/dumps/",
    "modified_folder": "/storage/emulated/0/modified/",
    "compress_folder": "/storage/emulated/0/compress/",
    "backup_folder": "/storage/emulated/0/backup_assets/"
}

# ==================== CONFIGURACIÓN GITHUB ====================
# 🔴 CAMBIA ESTE VALOR CON TU TOKEN 🔴
GITHUB_CONFIG = {
    "owner": "dexterxiteado-tech",
    "repo": "Script-",
    "path": "main/users.json",
    "token": "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"  # <--- Pon tu token aquí
}

# ==================== COLORES ====================
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ==================== FUNCIÓN PARA CONTRASEÑAS ====================
def get_password(prompt="Contraseña: "):
    try:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        tty.setraw(sys.stdin.fileno())
        print(f"{Colors.CYAN}{prompt}{Colors.RESET}", end='', flush=True)
        password = ""
        while True:
            char = sys.stdin.read(1)
            if char == '\r' or char == '\n' or char == '\x03':
                print()
                break
            elif char == '\x7f' or char == '\x08':
                if len(password) > 0:
                    password = password[:-1]
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif char.isprintable() or char == ' ':
                password += char
                sys.stdout.write('*')
                sys.stdout.flush()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return password
    except:
        return input(f"{Colors.CYAN}{prompt}{Colors.RESET}")

# ==================== CLASE PARA GITHUB DB ====================
class GitHubDB:
    def __init__(self):
        self.owner = GITHUB_CONFIG["owner"]
        self.repo = GITHUB_CONFIG["repo"]
        self.path = GITHUB_CONFIG["path"]
        self.token = GITHUB_CONFIG["token"]
        self.api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{self.path}"
    
    def _get_headers(self):
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def get_users(self):
        try:
            req = urllib.request.Request(self.api_url, headers=self._get_headers())
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                content = base64.b64decode(data["content"]).decode()
                users_data = json.loads(content)
                return users_data.get("users", {})
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"{Colors.YELLOW}⚠️ Archivo users.json no encontrado en GitHub{Colors.RESET}")
                print(f"{Colors.YELLOW}   Creando archivo por defecto...{Colors.RESET}")
                self._create_default_users()
                return self.get_users()
            else:
                print(f"{Colors.RED}❌ Error GitHub: {e}{Colors.RESET}")
                return {}
        except Exception as e:
            print(f"{Colors.RED}❌ Error conectando a GitHub: {e}{Colors.RESET}")
            return {}
    
    def _create_default_users(self):
        default_users = {
            "users": {
                "admin": {
                    "password": self._hash_password("admin123"),
                    "role": "admin",
                    "created": datetime.now().isoformat()
                },
                "user": {
                    "password": self._hash_password("user123"),
                    "role": "user",
                    "created": datetime.now().isoformat()
                }
            }
        }
        data = json.dumps(default_users, indent=2)
        encoded = base64.b64encode(data.encode()).decode()
        try:
            req = urllib.request.Request(self.api_url, headers=self._get_headers())
            with urllib.request.urlopen(req) as response:
                existing = json.loads(response.read().decode())
                sha = existing.get("sha")
                payload = json.dumps({
                    "message": "Crear archivo de usuarios",
                    "content": encoded,
                    "sha": sha
                }).encode()
                req = urllib.request.Request(
                    self.api_url,
                    data=payload,
                    headers={**self._get_headers(), "Content-Type": "application/json"},
                    method="PUT"
                )
        except urllib.error.HTTPError:
            payload = json.dumps({
                "message": "Crear archivo de usuarios",
                "content": encoded
            }).encode()
            req = urllib.request.Request(
                self.api_url,
                data=payload,
                headers={**self._get_headers(), "Content-Type": "application/json"},
                method="PUT"
            )
        try:
            with urllib.request.urlopen(req) as response:
                print(f"{Colors.GREEN}✅ Archivo users.json creado en GitHub{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Error creando archivo en GitHub: {e}{Colors.RESET}")
    
    def verify_user(self, username, password):
        users = self.get_users()
        if username in users:
            hashed = self._hash_password(password)
            if users[username]["password"] == hashed:
                return users[username]
        return None
    
    def add_user(self, username, password, role="user"):
        try:
            req = urllib.request.Request(self.api_url, headers=self._get_headers())
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                sha = data["sha"]
                content = base64.b64decode(data["content"]).decode()
                users_data = json.loads(content)
            
            if username in users_data.get("users", {}):
                return False, "El usuario ya existe"
            
            users_data["users"][username] = {
                "password": self._hash_password(password),
                "role": role,
                "created": datetime.now().isoformat()
            }
            
            new_content = json.dumps(users_data, indent=2)
            encoded = base64.b64encode(new_content.encode()).decode()
            
            payload = json.dumps({
                "message": f"Agregar usuario: {username}",
                "content": encoded,
                "sha": sha
            }).encode()
            
            req = urllib.request.Request(
                self.api_url,
                data=payload,
                headers={**self._get_headers(), "Content-Type": "application/json"},
                method="PUT"
            )
            
            with urllib.request.urlopen(req) as response:
                return True, "Usuario creado exitosamente"
        except Exception as e:
            return False, f"Error: {e}"

# ==================== SISTEMA DE LOGIN ====================
class AuthSystem:
    def __init__(self):
        self.db = GitHubDB()
        self.current_user = None
        self.current_role = None
    
    def login(self):
        clear_screen()
        print_header("🔐 SISTEMA DE AUTENTICACIÓN ONLINE")
        print()
        print(f"{Colors.YELLOW}  🔗 Conectando a GitHub...{Colors.RESET}")
        print()
        
        try:
            users = self.db.get_users()
            if not users:
                print(f"{Colors.RED}❌ No se pudo conectar a GitHub{Colors.RESET}")
                print(f"{Colors.YELLOW}💡 Verifica tu conexión a internet y el token{Colors.RESET}")
                input("\nPresiona Enter para continuar...")
                return False
        except Exception as e:
            print(f"{Colors.RED}❌ Error de conexión: {e}{Colors.RESET}")
            input("\nPresiona Enter para continuar...")
            return False
        
        print(f"{Colors.GREEN}✅ Conectado a GitHub{Colors.RESET}")
        print()
        print(f"{Colors.CYAN}{'─' * 50}{Colors.RESET}")
        print()
        
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            username = input(f"{Colors.CYAN}👤 Usuario: {Colors.RESET}").strip()
            if not username:
                print(f"{Colors.RED}❌ El usuario no puede estar vacío{Colors.RESET}")
                attempts += 1
                if attempts < max_attempts:
                    print(f"{Colors.YELLOW}Intentos restantes: {max_attempts - attempts}{Colors.RESET}")
                    print()
                continue
            
            password = get_password("🔑 Contraseña: ")
            user_data = self.db.verify_user(username, password)
            
            if user_data:
                self.current_user = username
                self.current_role = user_data.get("role", "user")
                print(f"\n{Colors.GREEN}✅ Acceso concedido{Colors.RESET}")
                time.sleep(1)
                return True
            else:
                attempts += 1
                print(f"{Colors.RED}❌ Credenciales incorrectas{Colors.RESET}")
            
            if attempts < max_attempts:
                print(f"{Colors.YELLOW}Intentos restantes: {max_attempts - attempts}{Colors.RESET}")
                print()
        
        print(f"\n{Colors.RED}❌ Acceso denegado - Demasiados intentos fallidos{Colors.RESET}")
        return False
    
    def change_password(self):
        if not self.current_user:
            print("No hay usuario autenticado")
            return
        clear_screen()
        print_header("CAMBIAR CONTRASEÑA")
        print(f"{Colors.YELLOW}⚠️ Cambio de contraseña desactivado en modo GitHub{Colors.RESET}")
        print(f"{Colors.YELLOW}   Contacta al administrador para cambiar tu contraseña{Colors.RESET}")
        input("\nPresiona Enter para continuar...")
    
    def add_user(self):
        if not self.current_user or self.current_role != "admin":
            print(f"{Colors.RED}❌ Permiso denegado - Se requieren privilegios de administrador{Colors.RESET}")
            input("Presiona Enter para continuar...")
            return
        
        clear_screen()
        print_header("AGREGAR NUEVO USUARIO")
        print(f"{Colors.BLUE}🔗 Los datos se guardarán en GitHub{Colors.RESET}")
        print()
        
        new_user = input(f"{Colors.CYAN}👤 Nombre de usuario: {Colors.RESET}").strip()
        if not new_user:
            print("❌ Nombre inválido")
            input("Presiona Enter para continuar...")
            return
        
        password = get_password("🔑 Contraseña: ")
        confirm_pass = get_password("🔑 Confirmar contraseña: ")
        
        if password != confirm_pass:
            print(f"{Colors.RED}❌ Las contraseñas no coinciden{Colors.RESET}")
            input("Presiona Enter para continuar...")
            return
        
        if len(password) < 4:
            print(f"{Colors.RED}❌ La contraseña debe tener al menos 4 caracteres{Colors.RESET}")
            input("Presiona Enter para continuar...")
            return
        
        role = input(f"{Colors.CYAN}🎭 Rol (admin/user): {Colors.RESET}").strip().lower()
        if role not in ["admin", "user"]:
            role = "user"
        
        print(f"\n{Colors.YELLOW}⏳ Subiendo a GitHub...{Colors.RESET}")
        success, message = self.db.add_user(new_user, password, role)
        
        if success:
            print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ {message}{Colors.RESET}")
        
        input("Presiona Enter para continuar...")
    
    def list_users(self):
        if not self.current_user or self.current_role != "admin":
            print(f"{Colors.RED}❌ Permiso denegado - Se requieren privilegios de administrador{Colors.RESET}")
            input("Presiona Enter para continuar...")
            return
        
        clear_screen()
        print_header("LISTA DE USUARIOS")
        print(f"{Colors.BLUE}🔗 Datos obtenidos de GitHub{Colors.RESET}")
        print()
        
        users = self.db.get_users()
        if not users:
            print("No hay usuarios registrados")
            input("Presiona Enter para continuar...")
            return
        
        print(f"{Colors.CYAN}{'Usuario':<15} {'Rol':<10} {'Creado'}{Colors.RESET}")
        print("-" * 50)
        for user, data in users.items():
            created = data.get("created", "Desconocido")[:16]
            print(f"{user:<15} {data.get('role', 'user'):<10} {created}")
        print()
        input("Presiona Enter para continuar...")

# ==================== FUNCIONES DE UTILIDAD ====================
def create_folders():
    for folder in CONFIG.values():
        os.makedirs(folder, exist_ok=True)

def clear_screen():
    os.system('clear')

def print_header(title):
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}  {title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")

def print_route(label, path):
    print(f"  {label}: {Colors.YELLOW}{path}{Colors.RESET}")

def get_file_list(folder, extension=None):
    files = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isfile(path):
                if extension is None:
                    files.append(f)
                elif f.endswith(extension):
                    files.append(f)
    return sorted(files)

def is_unity_asset(filepath):
    try:
        with open(filepath, 'rb') as f:
            header = f.read(20)
            if header.startswith(b'UnityFS'):
                return True
            if header.startswith(b'UnityRaw') or header.startswith(b'UnityWeb'):
                return True
            if header.startswith(b'\x00\x00\x00\x00') or header.startswith(b'\x01\x00\x00\x00'):
                f.seek(0)
                data = f.read(4096)
                if b'Unity' in data or b'Material' in data or b'Shader' in data:
                    return True
        return False
    except:
        return False

def select_files_unity(folder, prompt="Selecciona archivos Unity:"):
    all_files = get_file_list(folder)
    if not all_files:
        print(f"No hay archivos en {folder}")
        return []
    unity_files = []
    other_files = []
    print(f"\n🔍 Escaneando archivos en {folder}...")
    for f in all_files:
        path = os.path.join(folder, f)
        if is_unity_asset(path):
            unity_files.append(f)
        else:
            other_files.append(f)
    if not unity_files:
        print("⚠️  No se encontraron archivos Unity en esta carpeta")
        print("   Mostrando todos los archivos:")
        for i, f in enumerate(all_files, 1):
            print(f"  {i}. {f}")
    else:
        print(f"\n✅ {len(unity_files)} archivos Unity detectados:")
        for i, f in enumerate(unity_files, 1):
            size = os.path.getsize(os.path.join(folder, f)) / (1024 * 1024)
            print(f"  {i}. {f} ({size:.1f} MB)")
        if other_files:
            print(f"\n⚠️  {len(other_files)} archivos no-Unity ignorados")
    print("\n  a. Todos los archivos Unity")
    print("  b. Volver")
    selection = input("Selecciona números separados por coma (ej: 1,3,5) o 'a' para todos: ").strip().lower()
    if selection == 'b':
        return []
    if selection == 'a':
        return unity_files if unity_files else all_files
    selected = []
    try:
        for s in selection.split(','):
            s = s.strip()
            if s.isdigit():
                idx = int(s) - 1
                if 0 <= idx < len(unity_files if unity_files else all_files):
                    selected.append((unity_files if unity_files else all_files)[idx])
    except:
        print("Selección inválida")
        return []
    return selected

def select_files(folder, extension=None, prompt="Selecciona archivos:"):
    files = get_file_list(folder, extension)
    if not files:
        print(f"No hay archivos en {folder}")
        return []
    print(f"\n{prompt}")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f}")
    print("  a. Todos los archivos")
    print("  b. Volver")
    selection = input("Selecciona números separados por coma (ej: 1,3,5) o 'a' para todos: ").strip().lower()
    if selection == 'b':
        return []
    if selection == 'a':
        return files
    selected = []
    try:
        for s in selection.split(','):
            s = s.strip()
            if s.isdigit():
                idx = int(s) - 1
                if 0 <= idx < len(files):
                    selected.append(files[idx])
    except:
        print("Selección inválida")
        return []
    return selected

def detect_unity_version(asset_path):
    try:
        with open(asset_path, 'rb') as f:
            data = f.read(4096)
            if b'2018' in data:
                return '2018'
            elif b'2019' in data:
                return '2019'
            elif b'2020' in data:
                return '2020'
            elif b'2021' in data:
                return '2021'
            elif b'2022' in data:
                return '2022'
            elif b'2023' in data:
                return '2023'
            else:
                return 'unknown'
    except:
        return 'unknown'

def export_assets(selected_files=None):
    clear_screen()
    print_header("EXPORTAR ASSETS A DUMPS")
    if selected_files is None:
        selected_files = select_files_unity(CONFIG["assets_folder"], 
                                           prompt="Selecciona assets Unity para exportar:")
    if not selected_files:
        print("No se seleccionaron archivos.")
        input("Presiona Enter para continuar...")
        return
    total_exported = 0
    total_errors = 0
    for filename in selected_files:
        asset_path = os.path.join(CONFIG["assets_folder"], filename)
        print(f"\n📤 Exportando: {filename}")
        unity_version = detect_unity_version(asset_path)
        print(f"  🏷️  Versión detectada: {unity_version}")
        try:
            env = UnityPy.load(asset_path)
            exported_in_file = 0
            for obj in env.objects:
                if obj.type.name == "Material":
                    try:
                        tree = obj.read_typetree()
                        nombre = tree.get("m_Name", f"material_{obj.path_id}")
                        tree['_unity_version'] = unity_version
                        base_name = os.path.splitext(filename)[0]
                        dump_name = f"{base_name}_{nombre}_{obj.path_id}.json"
                        dump_path = os.path.join(CONFIG["dumps_folder"], dump_name)
                        counter = 1
                        while os.path.exists(dump_path):
                            dump_name = f"{base_name}_{nombre}_{obj.path_id}_{counter}.json"
                            dump_path = os.path.join(CONFIG["dumps_folder"], dump_name)
                            counter += 1
                        with open(dump_path, "w", encoding='utf-8') as f:
                            json.dump(tree, f, indent=4, default=str, ensure_ascii=False)
                        exported_in_file += 1
                        total_exported += 1
                        print(f"  ✅ Dump: {dump_name}")
                    except Exception as e:
                        print(f"  ❌ Error con objeto {obj.path_id}: {e}")
            if exported_in_file == 0:
                print(f"  ⚠️ No se encontraron materiales en {filename}")
        except Exception as e:
            total_errors += 1
            print(f"  ❌ Error cargando asset: {e}")
    print(f"\n📊 Resumen: {total_exported} dumps exportados, {total_errors} errores")
    input("\nPresiona Enter para continuar...")

def import_dumps(selected_assets=None, selected_dumps=None):
    clear_screen()
    print_header("IMPORTAR DUMPS A ASSETS")
    print("⚠️  Reemplazo completo de materiales")
    print("✅ Soporte para archivos Unity ofuscados")
    print()
    if selected_assets is None:
        selected_assets = select_files_unity(CONFIG["assets_folder"],
                                            prompt="Selecciona assets Unity de destino:")
    if not selected_assets:
        print("No se seleccionaron assets.")
        input("Presiona Enter para continuar...")
        return
    if selected_dumps is None:
        selected_dumps = select_files(CONFIG["dumps_folder"], extension=".json",
                                     prompt="Selecciona dumps para importar:")
    if not selected_dumps:
        print("No se seleccionaron dumps.")
        input("Presiona Enter para continuar...")
        return
    confirm = input("\n¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
    if confirm != "SI":
        print("Operación cancelada.")
        input("Presiona Enter para continuar...")
        return
    if not os.path.exists(CONFIG["backup_folder"]):
        print("\n📦 Creando backup...")
        os.makedirs(CONFIG["backup_folder"], exist_ok=True)
        for asset in selected_assets:
            src = os.path.join(CONFIG["assets_folder"], asset)
            dst = os.path.join(CONFIG["backup_folder"], asset)
            shutil.copy2(src, dst)
        print("✅ Backup creado")
    dumps_data = {}
    for dump_name in selected_dumps:
        dump_path = os.path.join(CONFIG["dumps_folder"], dump_name)
        try:
            with open(dump_path, 'r', encoding='utf-8') as f:
                tree_data = json.load(f)
                if isinstance(tree_data, dict):
                    unity_ver = tree_data.pop('_unity_version', 'unknown')
                    dumps_data[dump_name] = {
                        'data': tree_data,
                        'version': unity_ver,
                        'used': False
                    }
                else:
                    print(f"⚠️  {dump_name} no es válido")
        except Exception as e:
            print(f"❌ Error cargando {dump_name}: {e}")
    if not dumps_data:
        print("No se pudieron cargar los dumps.")
        input("Presiona Enter para continuar...")
        return
    total_imported = 0
    total_errors = 0
    for asset_name in selected_assets:
        asset_path = os.path.join(CONFIG["assets_folder"], asset_name)
        print(f"\n📥 Procesando: {asset_name}")
        unity_version = detect_unity_version(asset_path)
        print(f"  🏷️  Asset destino: {unity_version}")
        try:
            env = UnityPy.load(asset_path)
            modified = False
            for obj in env.objects:
                if obj.type.name != "Material":
                    continue
                try:
                    current_tree = obj.read_typetree()
                    current_name = current_tree.get("m_Name", "")
                    current_path_id = obj.path_id
                    for dump_name, dump_info in list(dumps_data.items()):
                        new_tree = dump_info['data']
                        dump_version = dump_info['version']
                        match = False
                        if current_name in dump_name or dump_name in current_name:
                            match = True
                        if str(current_path_id) in dump_name:
                            match = True
                        if match:
                            print(f"  🔄 Reemplazando: {current_name} (path_id: {current_path_id})")
                            print(f"     Con dump: {dump_name}")
                            try:
                                obj.save_typetree(new_tree)
                                modified = True
                                total_imported += 1
                                dump_info['used'] = True
                                print(f"    ✅ Guardado exitosamente")
                            except Exception as e:
                                print(f"    ❌ Falló: {e}")
                            break
                except Exception as e:
                    print(f"  ❌ Error con objeto {obj.path_id}: {e}")
            if modified:
                output_path = os.path.join(CONFIG["modified_folder"], asset_name)
                with open(output_path, "wb") as f:
                    f.write(env.file.save())
                print(f"  💾 Guardado en: {output_path}")
            else:
                print(f"  ⚠️ No se encontraron coincidencias")
        except Exception as e:
            total_errors += 1
            print(f"  ❌ Error: {e}")
    print(f"\n📊 Resumen: {total_imported} materiales importados, {total_errors} errores")
    input("\nPresiona Enter para continuar...")

def compress_assets(selected_files=None, compression="lzma"):
    clear_screen()
    print_header("COMPRIMIR ASSETS")
    if selected_files is None:
        selected_files = select_files(CONFIG["modified_folder"],
                                     prompt="Selecciona assets modificados para comprimir:")
    if not selected_files:
        print("No se seleccionaron archivos.")
        input("Presiona Enter para continuar...")
        return
    total_compressed = 0
    total_errors = 0
    for filename in selected_files:
        input_path = os.path.join(CONFIG["modified_folder"], filename)
        output_path = os.path.join(CONFIG["compress_folder"], filename)
        print(f"\n📦 Comprimiendo: {filename}")
        try:
            env = UnityPy.load(input_path)
            data = env.file.save(packer=compression)
            with open(output_path, "wb") as f:
                f.write(data)
            original_size = os.path.getsize(input_path) / 1024
            compressed_size = os.path.getsize(output_path) / 1024
            ratio = (1 - compressed_size / original_size) * 100
            total_compressed += 1
            print(f"  ✅ {filename} ({original_size:.1f}KB -> {compressed_size:.1f}KB, {ratio:.1f}% reducción)")
        except Exception as e:
            total_errors += 1
            print(f"  ❌ Error: {e}")
    print(f"\n📊 Resumen: {total_compressed} comprimidos, {total_errors} errores")
    input("\nPresiona Enter para continuar...")

def view_dumps():
    clear_screen()
    print_header("VER DUMPS")
    dumps = get_file_list(CONFIG["dumps_folder"], ".json")
    if not dumps:
        print("No hay dumps disponibles.")
        input("Presiona Enter para continuar...")
        return
    selected = select_files(CONFIG["dumps_folder"], ".json", "Selecciona un dump para ver:")
    if not selected:
        return
    for dump_name in selected:
        dump_path = os.path.join(CONFIG["dumps_folder"], dump_name)
        try:
            with open(dump_path, 'r', encoding='utf-8') as f:
                tree = json.load(f)
            print(f"\n📄 {dump_name}")
            print("-" * 40)
            unity_ver = tree.get('_unity_version', 'desconocida')
            print(f"   Versión Unity: {unity_ver}")
            print(f"   Nombre: {tree.get('m_Name', 'N/A')}")
            print(f"   Shader: {tree.get('m_Shader', {}).get('m_Name', 'N/A')}")
            if 'm_Color' in tree:
                color = tree['m_Color']
                print(f"   Color: rgba({color.get('r', 0)}, {color.get('g', 0)}, {color.get('b', 0)}, {color.get('a', 0)})")
            if 'm_Floats' in tree:
                print(f"   Floats: {len(tree['m_Floats'])} propiedades")
                for key, value in list(tree['m_Floats'].items())[:3]:
                    print(f"     {key}: {value}")
                if len(tree['m_Floats']) > 3:
                    print(f"     ... y {len(tree['m_Floats']) - 3} más")
            print("-" * 40)
        except Exception as e:
            print(f"❌ Error leyendo {dump_name}: {e}")
    input("\nPresiona Enter para continuar...")

def clean_folders():
    clear_screen()
    print_header("LIMPIAR CARPETAS")
    print("1. Limpiar dumps")
    print("2. Limpiar modified")
    print("3. Limpiar compress")
    print("4. Limpiar backup")
    print("5. Limpiar todo")
    print("b. Volver")
    choice = input("Selecciona: ")
    if choice.lower() == 'b':
        return
    folders_to_clean = []
    if choice == "1":
        folders_to_clean = [CONFIG["dumps_folder"]]
    elif choice == "2":
        folders_to_clean = [CONFIG["modified_folder"]]
    elif choice == "3":
        folders_to_clean = [CONFIG["compress_folder"]]
    elif choice == "4":
        folders_to_clean = [CONFIG["backup_folder"]]
    elif choice == "5":
        folders_to_clean = list(CONFIG.values())[1:]
    else:
        return
    confirm = input(f"¿Seguro? (s/n): ")
    if confirm.lower() != 's':
        return
    for folder in folders_to_clean:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                f_path = os.path.join(folder, f)
                try:
                    if os.path.isfile(f_path):
                        os.remove(f_path)
                    elif os.path.isdir(f_path):
                        shutil.rmtree(f_path)
                except Exception as e:
                    print(f"❌ Error eliminando {f}: {e}")
            print(f"✅ Limpiado: {folder}")
    input("\nPresiona Enter para continuar...")

def restore_backup():
    clear_screen()
    print_header("RESTAURAR BACKUP")
    backups = get_file_list(CONFIG["backup_folder"])
    if not backups:
        print("No hay backups disponibles.")
        input("Presiona Enter para continuar...")
        return
    selected = select_files(CONFIG["backup_folder"], prompt="Selecciona backups para restaurar:")
    if not selected:
        return
    confirm = input(f"¿Restaurar {len(selected)} archivos? (s/n): ")
    if confirm.lower() != 's':
        return
    for backup in selected:
        src = os.path.join(CONFIG["backup_folder"], backup)
        dst = os.path.join(CONFIG["assets_folder"], backup)
        try:
            shutil.copy2(src, dst)
            print(f"✅ Restaurado: {backup}")
        except Exception as e:
            print(f"❌ Error restaurando {backup}: {e}")
    input("\nPresiona Enter para continuar...")

# ==================== MENÚ DE USUARIO ====================
def user_menu(auth):
    while True:
        clear_screen()
        print_header(f"👤 USUARIO: {auth.current_user}")
        print()
        print(f"  {Colors.CYAN}1.{Colors.RESET} Cambiar contraseña")
        print(f"  {Colors.CYAN}2.{Colors.RESET} Agregar usuario (admin)")
        print(f"  {Colors.CYAN}3.{Colors.RESET} Listar usuarios (admin)")
        print(f"  {Colors.CYAN}4.{Colors.RESET} Volver al menú principal")
        print(f"  {Colors.CYAN}0.{Colors.RESET} Salir")
        print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
        choice = input("Selecciona una opción: ")
        if choice == "1":
            auth.change_password()
        elif choice == "2":
            auth.add_user()
        elif choice == "3":
            auth.list_users()
        elif choice == "4":
            return
        elif choice == "0":
            print(f"\n{Colors.GREEN}👋 ¡Hasta luego!{Colors.RESET}")
            exit(0)
        else:
            print("Opción inválida")
            input("Presiona Enter para continuar...")

# ==================== MENÚ PRINCIPAL ====================
def main_menu(auth):
    create_folders()
    while True:
        clear_screen()
        print_header("¯⁠\⁠_⁠(⁠ツ⁠)⁠_⁠/⁠¯ MODIFICADOR Dexter Modz Sk ¯⁠\⁠_⁠(⁠ツ⁠)⁠_⁠/⁠¯")
        print(f"  {Colors.GREEN}✅{Colors.RESET} Detecta archivos Unity ofuscados")
        print(f"  {Colors.GREEN}✅{Colors.RESET} Soporte: Unity 2018 ↔ 2022")
        print(f"  {Colors.BLUE}👤 Usuario:{Colors.RESET} {auth.current_user}")
        print(f"  {Colors.BLUE}🔗 Modo:{Colors.RESET} GitHub Online")
        print()
        print_route("📁 Assets", CONFIG['assets_folder'])
        print_route("📄 Dumps", CONFIG['dumps_folder'])
        print_route("✏️ Modified", CONFIG['modified_folder'])
        print_route("📦 Compress", CONFIG['compress_folder'])
        print_route("💾 Backup", CONFIG['backup_folder'])
        print()
        print(f"  {Colors.CYAN}1.{Colors.RESET} 📤 Exportar assets a dumps")
        print(f"  {Colors.CYAN}2.{Colors.RESET} 📥 Importar dumps a assets")
        print(f"  {Colors.CYAN}3.{Colors.RESET} 📦 Comprimir assets modificados")
        print(f"  {Colors.CYAN}4.{Colors.RESET} 📄 Ver dumps existentes")
        print(f"  {Colors.CYAN}5.{Colors.RESET} 💾 Restaurar backup")
        print(f"  {Colors.CYAN}6.{Colors.RESET} 🧹 Limpiar carpetas")
        print(f"  {Colors.CYAN}7.{Colors.RESET} 👤 Administrar usuario")
        print(f"  {Colors.CYAN}0.{Colors.RESET} ❌ Salir")
        print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
        
        choice = input("Selecciona una opción: ")
        
        if choice == "1":
            export_assets()
        elif choice == "2":
            import_dumps()
        elif choice == "3":
            compress_assets()
        elif choice == "4":
            view_dumps()
        elif choice == "5":
            restore_backup()
        elif choice == "6":
            clean_folders()
        elif choice == "7":
            user_menu(auth)
        elif choice == "0":
            print(f"\n{Colors.GREEN}👋 ¡Hasta luego!{Colors.RESET}")
            break
        else:
            print("Opción inválida")
            input("Presiona Enter para continuar...")

# ==================== EJECUCIÓN ====================
if __name__ == "__main__":
    try:
        auth = AuthSystem()
        if auth.login():
            main_menu(auth)
        else:
            print(f"\n{Colors.RED}Acceso denegado{Colors.RESET}")
    except KeyboardInterrupt:
        print(f"\n\n{Colors.GREEN}👋 ¡Hasta luego!{Colors.RESET}")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        input("Presiona Enter para salir...")