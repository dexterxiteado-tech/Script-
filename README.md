# 🎮 Dexter Modz Sk - Unity Asset Modifier (Termux)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Unity](https://img.shields.io/badge/Unity-2018%20%E2%86%94%202022-black?style=for-the-badge&logo=unity)
![Termux](https://img.shields.io/badge/Termux-Android-green?style=for-the-badge&logo=android)

> **Sistema de modificación de assets Unity completamente funcional desde tu teléfono Android (Termux).**  
> Incluye autenticación online vía GitHub, soporte para archivos ofuscados y sistema de backups.

---

## 📋 Características Principales

- ✅ **Detección automática**: Detecta archivos Unity ofuscados y sin extensión.
- ✅ **Soporte Multi-versión**: Compatible con Unity 2018, 2019, 2020, 2021 y 2022.
- ✅ **Exportación avanzada**: Extrae materiales a archivos JSON legibles (`dumps`).
- ✅ **Importación precisa**: Reemplaza materiales en assets usando los dumps exportados.
- ✅ **Compresión inteligente**: Comprime assets modificados usando compresión LZMA para reducir su tamaño.
- ✅ **Sistema de Backup**: Crea copias de seguridad automáticas antes de modificar assets.
- ✅ **Sistema de Login Online**: Base de datos de usuarios alojada en GitHub (SHA-256).

---

## 🔐 Sistema de Autenticación (Owner & Users)

El sistema cuenta con una base de datos en GitHub (`users.json`) y un sistema de roles.

### 🌟 ¿Cómo funciona el sistema de "Owner"?
- **El primer usuario** que aparezca en el archivo `users.json` es automáticamente el **Dueño (Owner)**.
- **Solo el Owner** puede utilizar las opciones de:
  - `Agregar nuevo usuario`.
  - `Listar usuarios registrados`.
- Cualquier otro usuario (incluso con rol `admin`) **NO podrá** agregar ni ver la lista de usuarios, garantizando la seguridad del sistema.

---

## 🚀 Instalación y Configuración (Termux)

### 1. Instalar dependencias en Termux
Abre Termux y ejecuta los siguientes comandos:

```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install UnityPy
