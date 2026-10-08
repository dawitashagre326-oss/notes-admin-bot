from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from supabase import create_client, Client

app = FastAPI()

# 1. ያዘጋጀናቸውን 4 መረጃዎች በጥቅስ ውስጥ ያስገቡ
SUPABASE_URL = "https://deunqmncldhrrpqiqnyf.supabase.co/rest/v1/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRldW5xbW5jbGRocnJwcWlxbnlmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEwNjEyODIsImV4cCI6MjEwNjYzNzI4Mn0.zrG3B63HGe6Lnmuul928iUmopI4_iJO9Sc0Z4H2OCVg"
BOT_TOKEN = "8633167051:AAHnCizRNwuKHu6DrmFxwQHYgMSBIu5d_Ts"
ADMIN_CHAT_ID = "7405707192"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
bot = Bot(token=BOT_TOKEN)

class PaymentRequest(BaseModel):
    user_name: str
    txn_id: str
    receipt_url: str
    payment_id: int

@app.get("/")
def read_root():
    return {"message": "የቴሌግራም ክፍያ ማረጋገጫ ሲስተም በስኬት እየሰራ ነው!"}

# ተማሪው ክፍያ ሲልክ ለአድሚን መልዕክት መላኪያ
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
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# አድሚኑ Approve/Reject በተን ሲጫን የሚሰራ አውቶማቲክ ክፍል
@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    if "callback_query" in data:
        callback = data["callback_query"]
        callback_data = callback["data"]
        message_id = callback["message"]["message_id"]
        chat_id = callback["message"]["chat"]["id"]

        action, payment_id = callback_data.split("_")
        payment_id = int(payment_id)

        if action == "approve":
            # 1. የክፍያ ጥያቄውን approved ማድረግ
            res = supabase.table("payment_requests").update({"status": "approved"}).eq("id", payment_id).execute()
            if res.data:
                user_id = res.data[0]["user_id"]
                # 2. የተማሪውን አካውንት is_premium = True ማድረግ
                supabase.table("users").update({"is_premium": True}).eq("id", user_id).execute()
            
            # 3. ቴሌግራም ላይ ያለውን መልዕክት ማዘመን
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption="✅ **ክፍያው ተረጋግጧል! የተማሪው አፕሊኬሽን ተከፍቷል።**",
                parse_mode="Markdown"
            )

        elif action == "reject":
            supabase.table("payment_requests").update({"status": "rejected"}).eq("id", payment_id).execute()
            await bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption="❌ **ክፍያው ውድቅ ተደርጓል።**",
                parse_mode="Markdown"
            )

    return {"status": "ok"}

