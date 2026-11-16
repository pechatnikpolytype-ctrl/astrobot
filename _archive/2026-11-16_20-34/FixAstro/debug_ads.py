#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Меняет logger.debug на logger.warning для рекламы + добавляет отладку."""
from pathlib import Path

BASE = Path(r"C:\Users\User\Desktop\AstroBot_clean")
MENU_PATH = BASE / "handlers" / "menu_commands.py"

content = MENU_PATH.read_text(encoding="utf-8")

# 1. Заменяем logger.debug на logger.warning в блоке рекламы
OLD_1 = '''    # 4. Показ рекламы
    try:
        await _maybe_show_ad(message, user_id, chat_id)
    except Exception as e:
        logger.debug(f"Реклама: {e}")'''

NEW_1 = '''    # 4. Показ рекламы
    try:
        logger.info(f"[AD] Вызов _maybe_show_ad для {user_id}")
        await _maybe_show_ad(message, user_id, chat_id)
    except Exception as e:
        logger.warning(f"[AD ERROR] {type(e).__name__}: {e}")
        import traceback
        logger.warning(traceback.format_exc())'''

if OLD_1 in content:
    content = content.replace(OLD_1, NEW_1)
    print("✅ Блок 1: заменён (info + warning)")
else:
    print("⚠️  Блок 1 не найден")

# 2. В _maybe_show_ad — добавляем логи
OLD_2 = '''async def _maybe_show_ad(message: Message, user_id: int, chat_id: int):
    """Показывает рекламу, если нужно."""
    # Проверка: показывать ли
    if not await should_show_ad(user_id):
        return

    # Выбор блока
    ad = await pick_random_ad()
    if not ad:
        return'''

NEW_2 = '''async def _maybe_show_ad(message: Message, user_id: int, chat_id: int):
    """Показывает рекламу, если нужно."""
    logger.info(f"[AD] Проверка should_show_ad({user_id})")
    if not await should_show_ad(user_id):
        logger.info(f"[AD] should_show_ad вернул False")
        return

    logger.info(f"[AD] Выбор блока")
    ad = await pick_random_ad()
    if not ad:
        logger.info(f"[AD] Нет активных блоков")
        return

    logger.info(f"[AD] Выбран блок #{ad['id']}")'''

if OLD_2 in content:
    content = content.replace(OLD_2, NEW_2)
    print("✅ Блок 2: добавлены логи в _maybe_show_ad")
else:
    print("⚠️  Блок 2 не найден")

# 3. В конце _maybe_show_ad — логи отправки
OLD_3 = '''    try:
        ad_msg = await message.answer(text, reply_markup=keyboard)
        # Логируем показ
        await log_ad_action(ad["id"], user_id, "show")
    except Exception as e:
        logger.debug(f"Не отправили рекламу: {e}")'''

NEW_3 = '''    try:
        logger.info(f"[AD] Отправка сообщения...")
        ad_msg = await message.answer(text, reply_markup=keyboard)
        logger.info(f"[AD] ✅ Отправлено msg_id={ad_msg.message_id}")
        # Логируем показ
        await log_ad_action(ad["id"], user_id, "show")
        logger.info(f"[AD] ✅ Показ залогирован")
    except Exception as e:
        logger.warning(f"[AD ERROR] Не отправили: {type(e).__name__}: {e}")
        import traceback
        logger.warning(traceback.format_exc())'''

if OLD_3 in content:
    content = content.replace(OLD_3, NEW_3)
    print("✅ Блок 3: добавлены логи отправки")
else:
    print("⚠️  Блок 3 не найден")

MENU_PATH.write_text(content, encoding="utf-8")
print()
print("=" * 60)
print("ГОТОВО!")
print("=" * 60)
print()
print("Дальше:")
print("  1. cd C:\\Users\\User\\Desktop\\AstroBot_clean")
print("  2. python webhook_bot.py")
print("  3. В Telegram нажми 🏠 Меню")
print("  4. Смотри логи в PowerShell — ищи [AD]")