from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 홀덤 서빙 정산봇입니다.\n\n"
        "사용법은 /help 를 입력하세요."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 홀덤 서빙 정산봇\n\n"
        "/start - 시작\n"
        "/help - 사용법 보기"
    )


def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN 환경변수가 설정되지 않았습니다.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("봇 시작됨")

    app.run_polling()


if __name__ == "__main__":
    main()
