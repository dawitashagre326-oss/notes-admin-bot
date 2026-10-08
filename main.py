from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from supabase import create_client, Client

app = FastAPI()

# 1. ያዘጋጀናቸውን 4 መረጃዎች እዚህ በጥቅሶቹ ውስጥ ያስገቡ
SUPABASE_URL = "https://deunqmncldhrrpqiqnyf.supabase.co/rest/v1/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRldW5xbW5jbGRocnJwcWlxbnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEwNjEyODIsImV4cCI6MjEwNjYzNzI4Mn0.zrG3B63HGe6Lnmuul928iUmopI4_iJO9Sc0Z4H2OCVg"
BOT_TOKEN = "8633167051:AAHnCizRNwuKHu6DrmFxwQHYgMSBIu5d_Ts"
ADMIN_CHAT_ID = "7405707192"

# ዳታቤዙን እና ቦቱን ማገናኘት
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=BOT_TOKEN)

class PaymentRequest(BaseModel):
    user_name: str
    txn_id: str
    receipt_url: str
    payment_id: int

@app.post("/notify_admin")
async def notify_admin(payment: PaymentRequest):
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{payment.payment_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{payment.payment_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = f"📩 **አዲስ የክፍያ ጥያቄ**\n\n👤 ተማሪ: {payment.user_name}\n🔢 Txn ID: `{payment.txn_id}`"
    
    try:
        await bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=payment.receipt_url,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return {"status": "success", "message": "መልዕክቱ ለአድሚን ተልኳል!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "የቴሌግራም ክፍያ ማረጋገጫ ሲስተም በስኬት እየሰራ ነው!"}
