import json
import os
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

DATA_FILE = "data.json"


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_user(data, user_id):
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = {
            "hourly_wage": 0,
            "current_shift": None,
            "tips": [],
            "expenses": [],
            "shifts": []
        }

    return data[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 홀덤 서빙 정산봇\n\n"
        "설명서 를 입력하면 사용법을 확인할 수 있습니다."
    )


async def show_help(update: Update):
    await update.message.reply_text(
        "📖 홀덤 서빙 정산봇 사용법\n\n"
        "시급 12000\n"
        "근무시작\n"
        "근무종료\n"
        "팁 5000\n"
        "지출 3000 물티슈\n"
        "현재\n"
        "통계\n"
        "월통계\n"
        "설명서"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    data = load_data()
    user = get_user(data, update.effective_user.id)

    try:

        if text == "설명서":
            await show_help(update)
            return

        if text.startswith("시급 "):
            amount = int(text.split(" ", 1)[1])

            user["hourly_wage"] = amount
            save_data(data)

            await update.message.reply_text(
                f"시급이 {amount:,}원으로 설정되었습니다."
            )
            return

        if text == "근무시작":

            if user["current_shift"]:
                await update.message.reply_text("이미 근무 중입니다.")
                return

            user["current_shift"] = datetime.now().isoformat()

            save_data(data)

            await update.message.reply_text("근무 시작 완료 ✅")
            return

        if text.startswith("팁 "):
            amount = int(text.split(" ", 1)[1])

            user["tips"].append({
                "amount": amount,
                "time": datetime.now().isoformat()
            })

            save_data(data)

            await update.message.reply_text(
                f"팁 {amount:,}원 등록 완료"
            )
            return

        if text.startswith("지출 "):

            parts = text.split()

            amount = int(parts[1])

            memo = ""

            if len(parts) >= 3:
                memo = " ".join(parts[2:])

            user["expenses"].append({
                "amount": amount,
                "memo": memo,
                "time": datetime.now().isoformat()
            })

            save_data(data)

            await update.message.reply_text(
                f"지출 {amount:,}원 등록 완료"
            )
            return

        if text == "현재":

            if not user["current_shift"]:
                await update.message.reply_text(
                    "현재 근무 중이 아닙니다."
                )
                return

            start_time = datetime.fromisoformat(
                user["current_shift"]
            )

            worked = datetime.now() - start_time

            wage_amount = int(
                worked.total_seconds() / 3600
                * user["hourly_wage"]
            )

            tips_total = sum(
                x["amount"] for x in user["tips"]
            )

            expenses_total = sum(
                x["amount"] for x in user["expenses"]
            )

            final_amount = (
                wage_amount
                + tips_total
                + expenses_total
            )

            await update.message.reply_text(
                f"현재 근무시간 : {str(worked).split('.')[0]}\n\n"
                f"예상 급여 : {wage_amount:,}원\n"
                f"팁 : {tips_total:,}원\n"
                f"지출 : {expenses_total:,}원\n\n"
                f"최종 받을 금액 : {final_amount:,}원"
            )
            return

        if text == "근무종료":

            if not user["current_shift"]:
                await update.message.reply_text(
                    "현재 근무 중이 아닙니다."
                )
                return

            start_time = datetime.fromisoformat(
                user["current_shift"]
            )

            end_time = datetime.now()

            worked = end_time - start_time

            wage_amount = int(
                worked.total_seconds() / 3600
                * user["hourly_wage"]
            )

            tips_total = sum(
                x["amount"] for x in user["tips"]
            )

            expenses_total = sum(
                x["amount"] for x in user["expenses"]
            )

            final_amount = (
                wage_amount
                + tips_total
                + expenses_total
            )

            user["shifts"].append({
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "wage": wage_amount,
                "tips": tips_total,
                "expenses": expenses_total
            })

            user["current_shift"] = None
            user["tips"] = []
            user["expenses"] = []

            save_data(data)

            await update.message.reply_text(
                "근무 종료\n\n"
                f"근무시간 : {str(worked).split('.')[0]}\n"
                f"시급 : {user['hourly_wage']:,}원\n\n"
                f"급여 : {wage_amount:,}원\n"
                f"팁 : {tips_total:,}원\n"
                f"지출 : {expenses_total:,}원\n\n"
                f"총 수입 : {wage_amount + tips_total:,}원\n"
                f"최종 받을 금액 : {final_amount:,}원"
            )
            return

        if text == "통계":

            if not user["shifts"]:
                await update.message.reply_text(
                    "기록이 없습니다."
                )
                return

            result = "최근 근무 기록\n\n"

            for shift in user["shifts"][-20:]:

                day = datetime.fromisoformat(
                    shift["end"]
                ).strftime("%m/%d")

                result += (
                    f"{day}\n"
                    f"급여 {shift['wage']:,}원\n"
                    f"팁 {shift['tips']:,}원\n"
                    f"지출 {shift['expenses']:,}원\n\n"
                )

            await update.message.reply_text(result)
            return

        if text == "월통계":

            now = datetime.now()

            wage_total = 0
            tip_total = 0
            expense_total = 0
            work_days = 0

            for shift in user["shifts"]:

                end = datetime.fromisoformat(
                    shift["end"]
                )

                if (
                    end.year == now.year
                    and end.month == now.month
                ):
                    wage_total += shift["wage"]
                    tip_total += shift["tips"]
                    expense_total += shift["expenses"]
                    work_days += 1

            final_amount = (
                wage_total
                + tip_total
                + expense_total
            )

            await update.message.reply_text(
                f"{now.year}년 {now.month}월\n\n"
                f"근무일수 : {work_days}일\n\n"
                f"급여 : {wage_total:,}원\n"
                f"팁 : {tip_total:,}원\n"
                f"지출 : {expense_total:,}원\n\n"
                f"총 수입 : {wage_total + tip_total:,}원\n"
                f"최종 받을 금액 : {final_amount:,}원"
            )
            return

    except Exception as e:
        await update.message.reply_text(
            f"오류 발생: {e}"
        )


def main():
    token = os.getenv("BOT_TOKEN")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    app.run_polling()


if __name__ == "__main__":
    main()
