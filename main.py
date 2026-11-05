from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
import re
import logging
import asyncio
from maxapi import Bot, Dispatcher, F
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(i.strip()) for i in admin_ids_str.split(",") if i.strip().isdigit()]
# Замените на НОВЫЙ токен, старый скомпрометирован
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

app = FastAPI()

# CORS — чтобы React мог обращаться к API с другого порта
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGINS[0], ALLOWED_ORIGINS[1]],  # ваш фронт
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Application(BaseModel):
    kvantum: str
    name: str
    phone: str
    email: EmailStr
    comment: str = ""

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Имя обязательно")
        return v.strip()

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v):
        if not re.match(r"^[+\d\s()\-]{7,}$", v):
            raise ValueError("Некорректный телефон")
        return v

@app.post("/api/applications", status_code=201)
async def create_application(app_data: Application):
    # Здесь сохраняем в БД / отправляем в Telegram / email
    print("Новая заявка:", app_data.dict())
    kvantum = app_data.kvantum
    name = app_data.name
    phone = app_data.phone
    email = app_data.email
    comment = app_data.comment or "-"

    text = (
        "🎓 Новая заявка на обучение\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📚 Квантум: {kvantum}\n"
        f"👤 Имя: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"📧 E-mail: {email}\n"
        f"💬 Комментарий: {comment}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🕐 Заявка получена с сайта"
    )
    for user_id in ADMIN_IDS:
        try:
            await bot.send_message(
                user_id=user_id,
                text=text
            )
            logging.info("Сообщение Роману отправлено")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение: {e}")
        await asyncio.sleep(2)
    return {"success": "ok"}