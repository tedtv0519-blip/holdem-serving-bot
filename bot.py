import json
import os
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

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
    text = (
        "👋 홀덤 서빙 정산봇\n\n"
        "/help - 사용법\n"
        "/wage 금액 - 시급 설정\n"
        "/startwork - 근무 시작\n"
        "/endwork - 근무 종료\n"
        "/tip 금액 - 팁 입력\n"
        "/expense 금액 내용 - 지출 입력\n"
        "/status - 현재 현황\n"
        "/stats - 기록 조회\n"
        "/monthly - 월 통계"
    )

    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 사용법\n\n"
        "/wage 12000\n"
        "시급 설정\n\n"
        "/startwork\n"
        "근무 시작\n\n"
        "/endwork\n"
        "근무 종료 및 정산\n\n"
        "/tip 5000\n"
        "팁 입력\n\n"
        "/expense 3000 물티슈\n"
        "지출 입력\n\n"
        "/status\n"
        "현재 현황\n\n"
        "/stats\n"
        "팁/지출 기록\n\n"
        "/monthly\n"
        "월 통계"
    )

    await update.message.reply_text(text)


async def wage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("예시: /wage 12000")
        return

    data = load_data()
    user = get_user(data, update.effective_user.id)

    user["hourly_wage"] = int(context.args[0])

    save_data(data)

    await update.message.reply_text(
        f"시급이 {user['hourly_wage']:,}원으로 설정되었습니다."
    )


async def startwork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)

    if user["current_shift"]:
        await update.message.reply_text("이미 근무 중입니다.")
        return

    user["current_shift"] = datetime.now().isoformat()

    save_data(data)

    await update.message.reply_text("근무 시작 완료 ✅")


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("예시: /tip 5000")
        return

    amount = int(context.args[0])

    data = load_data()
    user = get_user(data, update.effective_user.id)

    user["tips"].append({
        "amount": amount,
        "time": datetime.now().isoformat()
    })

    save_data(data)

    await update.message.reply_text(
        f"팁 {amount:,}원 등록 완료"
    )


async def expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text(
            "예시: /expense 3000 물티슈"
        )
        return

    amount = int(context.args[0])

    memo = ""
    if len(context.args) > 1:
        memo = " ".join(context.args[1:])

    data = load_data()
    user = get_user(data, update.effective_user.id)

    user["expenses"].append({
        "amount": amount,
        "memo": memo,
        "time": datetime.now().isoformat()
    })

    save_data(data)

    await update.message.reply_text(
        f"지출 {amount:,}원 등록 완료"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)

    if not user["current_shift"]:
        await update.message.reply_text("현재 근무 중이 아닙니다.")
        return

    start_time = datetime.fromisoformat(user["current_shift"])

    worked = datetime.now() - start_time

    hours = worked.total_seconds() / 3600

    wage_amount = int(hours * user["hourly_wage"])

    today_tip = sum(x["amount"] for x in user["tips"])
    today_expense = sum(x["amount"] for x in user["expenses"])

    final_amount = wage_amount + today_tip + today_expense

    text = (
        f"현재 근무시간 : {worked}\n\n"
        f"예상 급여 : {wage_amount:,}원\n"
        f"팁 : {today_tip:,}원\n"
        f"지출 : {today_expense:,}원\n\n"
        f"최종 받을 금액 : {final_amount:,}원"
    )

    await update.message.reply_text(text)


async def endwork(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)

    if not user["current_shift"]:
        await update.message.reply_text("현재 근무 중이 아닙니다.")
        return

    start_time = datetime.fromisoformat(user["current_shift"])

    end_time = datetime.now()

    worked = end_time - start_time

    hours = worked.total_seconds() / 3600

    wage_amount = int(hours * user["hourly_wage"])

    tips_total = sum(x["amount"] for x in user["tips"])
    expenses_total = sum(x["amount"] for x in user["expenses"])

    final_amount = wage_amount + tips_total + expenses_total

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

    text = (
        "근무 종료\n\n"
        f"근무시간 : {worked}\n"
        f"시급 : {user['hourly_wage']:,}원\n\n"
        f"급여 : {wage_amount:,}원\n"
        f"팁 : {tips_total:,}원\n"
        f"지출 : {expenses_total:,}원\n\n"
        f"총 수입 : {wage_amount + tips_total:,}원\n"
        f"최종 받을 금액 : {final_amount:,}원"
    )

    await update.message.reply_text(text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)

    shifts = user["shifts"][-20:]

    if not shifts:
        await update.message.reply_text("기록이 없습니다.")
        return

    text = "최근 근무 기록\n\n"

    for s in shifts:
        end_date = datetime.fromisoformat(
            s["end"]
        ).strftime("%m/%d")

        text += (
            f"{end_date}\n"
            f"급여 {s['wage']:,}원\n"
            f"팁 {s['tips']:,}원\n"
            f"지출 {s['expenses']:,}원\n\n"
        )

    await update.message.reply_text(text)


async def monthly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = get_user(data, update.effective_user.id)

    now = datetime.now()

    wage_total = 0
    tip_total = 0
    expense_total = 0
    days = 0

    for shift in user["shifts"]:
        end = datetime.fromisoformat(shift["end"])

        if end.month == now.month and end.year == now.year:
            wage_total += shift["wage"]
            tip_total += shift["tips"]
            expense_total += shift["expenses"]
            days += 1

    final_amount = wage_total + tip_total + expense_total

    text = (
        f"{now.year}년 {now.month}월\n\n"
        f"근무일수 : {days}일\n\n"
        f"급여 : {wage_total:,}원\n"
        f"팁 : {tip_total:,}원\n"
        f"지출 : {expense_total:,}원\n\n"
        f"총 수입 : {wage_total + tip_total:,}원\n"
        f"최종 받을 금액 : {final_amount:,}원"
    )

    await update.message.reply_text(text)


def main():
    token = os.getenv("BOT_TOKEN")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("wage", wage))
    app.add_handler(CommandHandler("startwork", startwork))
    app.add_handler(CommandHandler("endwork", endwork))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("expense", expense))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("monthly", monthly))

    app.run_polling()


if __name__ == "__main__":
    main()
