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
            "shifts": [],
            "last_actions": []
        }

    if "last_actions" not in data[user_id]:
        data[user_id]["last_actions"] = []

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
        "→ 시급 설정\n\n"

        "근무시작\n"
        "→ 근무 시작\n\n"

        "근무종료\n"
        "→ 근무 종료 및 정산\n\n"

        "팁 5000\n"
        "→ 팁 입력\n\n"

        "지출 3000 물티슈\n"
        "→ 가게 물품 구매 기록\n\n"

        "현재\n"
        "→ 현재 정산 현황\n\n"

        "통계\n"
        "→ 현재 근무 중 팁/지출 기록\n\n"

        "월통계\n"
        "→ 이번 달 누적 통계\n\n"

        "취소\n"
        "→ 최근 입력한 팁 또는 지출 삭제\n\n"

        "초기화\n"
        "→ 현재 근무 데이터 초기화\n\n"

        "정산 방식\n\n"

        "급여 = 근무시간 × 시급\n"
        "총 수입 = 급여 + 팁\n"
        "최종 받을 금액 = 급여 + 팁 + 지출\n\n"

        "※ 지출은 차감이 아닌\n"
        "가게에서 돌려받을 금액입니다."
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

            user["last_actions"].append({
                "type": "tip"
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

            user["last_actions"].append({
                "type": "expense"
            })

            save_data(data)

            await update.message.reply_text(
                f"지출 {amount:,}원 등록 완료"
            )
            return

        if text == "취소":

            if not user["last_actions"]:
                await update.message.reply_text(
                    "취소할 기록이 없습니다."
                )
                return

            last = user["last_actions"].pop()

            if last["type"] == "tip":

                if user["tips"]:
                    deleted = user["tips"].pop()

                    save_data(data)

                    await update.message.reply_text(
                        f"삭제 완료\n\n"
                        f"팁 {deleted['amount']:,}원"
                    )

            elif last["type"] == "expense":

                if user["expenses"]:
                    deleted = user["expenses"].pop()

                    save_data(data)

                    await update.message.reply_text(
                        f"삭제 완료\n\n"
                        f"지출 {deleted['amount']:,}원"
                    )

            return

        if text == "초기화":

            user["current_shift"] = None
            user["tips"] = []
            user["expenses"] = []
            user["last_actions"] = []

            save_data(data)

            await update.message.reply_text(
                "현재 근무 데이터 초기화 완료"
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

        if text == "통계":

            result = "📊 현재 근무 통계\n\n"

            tip_total = 0

            result += "팁 기록\n\n"

            if user["tips"]:
                for tip in user["tips"]:
                    time_str = datetime.fromisoformat(
                        tip["time"]
                    ).strftime("%H:%M:%S")

                    result += (
                        f"{time_str} - "
                        f"{tip['amount']:,}원\n"
                    )

                    tip_total += tip["amount"]

            else:
                result += "기록 없음\n"

            result += (
                f"\n총 팁 : {tip_total:,}원\n\n"
                "━━━━━━━━━━\n\n"
                "지출 기록\n\n"
            )

            expense_total = 0

            if user["expenses"]:
                for expense in user["expenses"]:

                    time_str = datetime.fromisoformat(
                        expense["time"]
                    ).strftime("%H:%M:%S")

                    result += (
                        f"{time_str} - "
                        f"{expense['amount']:,}원"
                    )

                    if expense["memo"]:
                        result += (
                            f" ({expense['memo']})"
                        )

                    result += "\n"

                    expense_total += expense["amount"]

            else:
                result += "기록 없음\n"

            result += (
                f"\n총 지출 : {expense_total:,}원"
            )

            await update.message.reply_text(result)
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
            user["last_actions"] = []

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
