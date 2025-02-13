from datetime import datetime, timedelta

import genshin

from database import Database, StarrailScheduleNotes
from utility import EmbedTemplate

from ... import errors, parse_starrail_notes
from .common import CheckResult, cal_next_check_time, get_realtime_notes


async def check_starrail_notes(user: StarrailScheduleNotes) -> CheckResult | None:
    """依據每位使用者的設定檢查即時便箋，若超出設定值時則回傳提醒訊息；若跳過此使用者，回傳 None"""
    try:
        notes = await get_realtime_notes(user)
    except Exception as e:
        if isinstance(e, errors.GenshinAPIException) and isinstance(e.origin, genshin.errors.GeetestError):
            return CheckResult("An error HSR automatically realtime note check, check again in 24 hours。", EmbedTemplate.error(e))
        else:
            return CheckResult("An error HSR automatically realtime note check, check again in 5 hours。", EmbedTemplate.error(e))

    if not isinstance(notes, genshin.models.StarRailNote):
        return None

    msg = await check_threshold(user, notes)
    embed = await parse_starrail_notes(notes, short_form=True)
    return CheckResult(msg, embed)


async def check_threshold(user: StarrailScheduleNotes, notes: genshin.models.StarRailNote) -> str:
    msg = ""
    # 設定一個基本的下次檢查時間
    next_check_time: list[datetime] = [datetime.now() + timedelta(days=1)]

    # 檢查開拓力
    if isinstance(user.threshold_power, int):
        # 當開拓力距離額滿時間低於設定值，則設定要發送的訊息
        if notes.stamina_recover_time <= timedelta(hours=user.threshold_power):
            msg += "Trailblaze Power is full！" if notes.stamina_recover_time <= timedelta(0) else "Trailblaze Power is almost full！"
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if notes.current_stamina >= notes.max_stamina
            else cal_next_check_time(notes.stamina_recover_time, user.threshold_power)
        )
    # 檢查委託
    if isinstance(user.threshold_expedition, int) and len(notes.expeditions) > 0:
        longest_expedition = max(notes.expeditions, key=lambda epd: epd.remaining_time)
        if longest_expedition.remaining_time <= timedelta(hours=user.threshold_expedition):
            msg += "Expeditions is complete！" if longest_expedition.remaining_time <= timedelta(0) else "Expeditions is almost complete！"
        next_check_time.append(
            datetime.now() + timedelta(hours=6)
            if longest_expedition.finished is True
            else cal_next_check_time(longest_expedition.remaining_time, user.threshold_expedition)
        )
    # 檢查每日實訓
    if isinstance(user.check_daily_training_time, datetime):
        # 當現在時間已超過設定的檢查時間
        if datetime.now() >= user.check_daily_training_time:
            if notes.current_train_score < notes.max_train_score:
                msg += "Today's daily training has not yet completed.！"
            # 下次檢查時間為今天+1天，並更新至資料庫
            user.check_daily_training_time += timedelta(days=1)
        next_check_time.append(user.check_daily_training_time)
    # 檢查模擬宇宙
    if isinstance(user.check_universe_time, datetime):
        # 當現在時間已超過設定的檢查時間
        if datetime.now() >= user.check_universe_time:
            if notes.current_rogue_score < notes.max_rogue_score:
                msg += "This week's Simulated Universe is not yet complete！"
            # 下次檢查時間為下一周，並更新至資料庫
            user.check_universe_time += timedelta(weeks=1)
        next_check_time.append(user.check_universe_time)
    # 檢查歷戰餘響
    if isinstance(user.check_echoofwar_time, datetime):
        # 當現在時間已超過設定的檢查時間
        if datetime.now() >= user.check_echoofwar_time:
            if notes.remaining_weekly_discounts > 0:
                msg += "The Weekly bosses is not yet complete.！"
            # 下次檢查時間為下一周，並更新至資料庫
            user.check_echoofwar_time += timedelta(weeks=1)
        next_check_time.append(user.check_echoofwar_time)

    # 設定下次檢查時間，從上面設定的時間中取最小的值
    check_time = min(next_check_time)
    # 若此次需要發送訊息，則將下次檢查時間設為至少1小時
    if len(msg) > 0:
        check_time = max(check_time, datetime.now() + timedelta(minutes=60))
    user.next_check_time = check_time
    await Database.insert_or_replace(user)

    return msg
