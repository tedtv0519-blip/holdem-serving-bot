from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "홀덤 서빙 정산봇입니다.\n\n"
        "/설명서 로 사용법을 확인하세요."
    )


async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 홀덤 서빙 정산봇 사용법\n\n"
        "/시급 금액\n"
        "/근무시작\n"
        "/근무종료\n"
        "/팁 금액\n"
        "/지출 금액 내용\n"
        "/현재\n"
        "/통계\n"
        "/월통계"
    )


def main():
    token = os.getenv("BOT_TOKEN")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("설명서", guide))

    app.run_polling()


if __name__ == "__main__":
    main()
