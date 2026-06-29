#!/usr/bin/env python3
"""
AI Assistant на базе Groq API (Llama 3 70B)
"""

import os
from groq import Groq

# Получаем API ключ из переменной окружения
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ Ошибка: GROQ_API_KEY не установлен!")
    print("Выполни: export GROQ_API_KEY='твой_ключ'")
    exit(1)

client = Groq(api_key=api_key)

print("=" * 60)
print("🤖 AI Assistant (Groq + Llama 3 70B)")
print("=" * 60)
print("Команды: /code, /python, /telegram, /fix, /explain, /exit")
print("=" * 60)

def ask_groq(prompt, system_msg="Ты опытный Python разработчик."):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка: {e}"

while True:
    try:
        user_input = input("\n👉 Ты: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == '/exit':
            print("\n👋 Пока!")
            break
        
        if user_input.startswith('/code'):
            prompt = user_input[5:].strip()
            system_msg = "Ты опытный программист. Пиши рабочий код с комментариями."
        elif user_input.startswith('/python'):
            prompt = f"Напиши Python код: {user_input[7:].strip()}"
            system_msg = "Ты эксперт по Python."
        elif user_input.startswith('/telegram'):
            prompt = f"Создай Telegram бота: {user_input[9:].strip()}"
            system_msg = "Ты эксперт по Telegram ботам на Python."
        elif user_input.startswith('/fix'):
            prompt = f"Исправь ошибку: {user_input[4:].strip()}"
            system_msg = "Ты эксперт по отладке кода."
        else:
            prompt = user_input
            system_msg = "Ты помощник программиста."
        
        print("\n⏳ Думаю...")
        print("-" * 60)
        
        answer = ask_groq(prompt, system_msg)
        print(f"\n🤖 AI:\n{answer}")
        print("-" * 60)
        
    except KeyboardInterrupt:
        print("\n\n👋 Пока!")
        break
