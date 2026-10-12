import logging
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import ADMINS
from locales import t
from database.postgres_db import (
    get_ads_config, set_ads_config,
    get_all_ads, get_ad, add_ad, update_ad, delete_ad, toggle_ad,
    get_ad_stats, get_all_ad_stats,
)

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# FSM
# ============================================================
class AdStates(StatesGroup):
    waiting_text = State()
    waiting_link = State()
    waiting_button_text = State()
    waiting_edit_text = State()
    waiting_edit_link = State()
    waiting_edit_button = State()
    waiting_freq_value = State()
    waiting_max_per_day = State()


# ============================================================
# МЕНЮ РЕКЛАМЫ
# ============================================================
async def _admin_lang(user_id: int) -> str:
    try:
        from config import MULTILANG_ENABLED
        if not MULTILANG_ENABLED:
            return "ru"
        from database.postgres_db import get_user_lang_cached
        return await get_user_lang_cached(user_id)
    except Exception:
        return "ru"


@router.callback_query(F.data == "admin_ads")
async def admin_ads_menu(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if callback.from_user.id not in ADMINS:
        return

    config = await get_ads_config()
    ads = await get_all_ads()
    stats = await get_all_ad_stats(days=7)

    status = t("ADMIN_TRIAL_ON", lang) if config.get("enabled") else t("ADMIN_TRIAL_OFF", lang)
    freq_map = {
        "always": t("ADS_FREQ_ALWAYS", lang),
        "daily": t("ADS_FREQ_DAILY", lang),
        "every_n": t("ADS_FREQ_EVERY_N", lang, n=config.get('frequency_value', 5)),
    }
    freq_text = freq_map.get(config.get("frequency", "daily"), "?")

    text = (
        f"{t('ADS_MENU_TITLE', lang)}\n\n"
        f"{t('ADS_CONFIG_ENABLED', lang, status=status)}\n"
        f"{t('ADS_PLACE_MENU', lang)}\n"
        f"{t('ADS_CONFIG_FREQ', lang, freq=freq_text)}\n"
        f"{t('ADS_CONFIG_MAXDAY', lang, count=config.get('max_per_day', 3))}\n"
        f"{t('ADS_CONFIG_ADMINS', lang, mode=(t('ADS_CONFIG_ADMINS_SHOW', lang) if config.get('show_to_admins') else t('ADS_CONFIG_ADMINS_HIDE', lang)))}\n\n"
        f"{t('ADS_STATS_7D', lang)}\n"
        f"  \u2022 {t('ADS_STATS_SHOWS', lang, count=stats['shows'])}\n"
        f"  \u2022 {t('ADS_STATS_CLICKS', lang, count=stats['clicks'])}\n"
        f"  • CTR: {stats['ctr']}%\n\n"
        f"{t('ADS_STATS_ACTIVE', lang, active=len([a for a in ads if a['enabled']]), total=len(ads))}"
    )

    toggle_text = t("ADS_BTN_DISABLE", lang) if config.get("enabled") else t("ADS_BTN_ENABLE", lang)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data="ads_toggle_all")],
        [InlineKeyboardButton(text=t("ADS_BTN_ADD", lang), callback_data="ads_add")],
        [InlineKeyboardButton(text=t("ADS_BTN_LIST", lang), callback_data="ads_list")],
        [InlineKeyboardButton(text=t("ADS_BTN_SETTINGS", lang), callback_data="ads_settings")],
        [InlineKeyboardButton(text=t("ADS_BTN_STATS", lang), callback_data="ads_stats")],
        [InlineKeyboardButton(text=t("ADS_BTN_HELP", lang), callback_data="ads_help")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ВКЛ/ВЫКЛ
# ============================================================
@router.callback_query(F.data == "ads_toggle_all")
async def ads_toggle_all(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    new_state = not config.get("enabled", False)
    await set_ads_config(enabled=new_state)
    await callback.answer(
        t("ADS_ENABLED_ON", lang) if new_state else t("ADS_ENABLED_OFF", lang),
        show_alert=True,
    )
    await admin_ads_menu(callback)


# ============================================================
# СПИСОК БЛОКОВ
# ============================================================
@router.callback_query(F.data == "ads_list")
async def ads_list(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if callback.from_user.id not in ADMINS:
        return
    ads = await get_all_ads()

    if not ads:
        text = t("ADS_LIST_EMPTY", lang)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("ADS_BTN_ADD", lang), callback_data="ads_add")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
        ])
    else:
        text = t("ADS_LIST_HEADER", lang) + "\n\n"
        buttons = []
        for a in ads:
            status = "✅" if a["enabled"] else "❌"
            short = a["text"][:30] + "..." if len(a["text"]) > 30 else a["text"]
            buttons.append([InlineKeyboardButton(
                text=f"{status} #{a['id']} {short}",
                callback_data=f"ads_view_{a['id']}"
            )])
        buttons.append([InlineKeyboardButton(text=t("ADS_BTN_ADD", lang), callback_data="ads_add")])
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("ads_view_"))
async def ads_view(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_view_", ""))
    ad = await get_ad(ad_id)
    if not ad:
        await callback.answer(t("ADS_NOT_FOUND", lang), show_alert=True)
        return

    stats = await get_ad_stats(ad_id, days=7)
    status = t("ADMIN_TRIAL_ON", lang) if ad["enabled"] else t("ADMIN_TRIAL_OFF", lang)

    text = (
        f"{t('ADS_VIEW_TITLE', lang, id=ad['id'])}\n\n"
        f"{t('ADS_CONFIG_ENABLED', lang, status=status)}\n"
        f"{t('ADS_VIEW_WEIGHT', lang, n=ad.get('weight', 1))}\n\n"
        f"{t('ADS_VIEW_TEXT', lang, text=ad['text'])}\n\n"
        f"{t('ADS_VIEW_LINK', lang, link=ad.get('link') or t('ADS_VIEW_LINK_NONE', lang))}\n"
        f"{t('ADS_VIEW_BUTTON', lang, text=ad.get('button_text', t('ADS_BTN_DEFAULT', lang)))}\n\n"
        f"{t('ADS_STATS_7D', lang)}\n"
        f"  \u2022 {t('ADS_STATS_SHOWS', lang, count=stats['shows'])}\n"
        f"  \u2022 {t('ADS_STATS_CLICKS', lang, count=stats['clicks'])}\n"
        f"  • CTR: {stats['ctr']}%"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("ADS_BTN_TOGGLE_OFF", lang) if ad["enabled"] else t("ADS_BTN_TOGGLE_ON", lang),
            callback_data=f"ads_toggle_{ad_id}"
        )],
        [InlineKeyboardButton(text=t("ADS_BTN_EDIT_TEXT", lang), callback_data=f"ads_edit_text_{ad_id}")],
        [InlineKeyboardButton(text=t("ADS_BTN_EDIT_LINK", lang), callback_data=f"ads_edit_link_{ad_id}")],
        [InlineKeyboardButton(text=t("ADS_BTN_EDIT_BUTTON", lang), callback_data=f"ads_edit_button_{ad_id}")],
        [InlineKeyboardButton(text=t("ADS_BTN_DELETE", lang), callback_data=f"ads_delete_{ad_id}")],
        [InlineKeyboardButton(text=t("ADS_BTN_BACK_LIST", lang), callback_data="ads_list")],
    ])

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ДОБАВИТЬ БЛОК
# ============================================================
@router.callback_query(F.data == "ads_add")
async def ads_add_start(callback: CallbackQuery, state: FSMContext):
    lang = await _admin_lang(callback.from_user.id)
    if callback.from_user.id not in ADMINS:
        return
    await state.set_state(AdStates.waiting_text)
    await callback.message.edit_text(
        t("ADS_ADD_STEP1_TITLE", lang) + "\n\n"
        f"{t('ADS_ENTER_TEXT', lang)}\n\n"
        "/cancel — отмена"
    )


@router.message(AdStates.waiting_text)
async def ads_add_text(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    text = message.text.strip()
    if len(text) < 5:
        await message.answer(t("ADS_ERR_TEXT_SHORT", lang))
        return
    await state.update_data(ad_text=text)
    await state.set_state(AdStates.waiting_link)
    await message.answer(
        t("ADS_ADD_STEP2_TITLE", lang) + "\n\n"
        f"{t('ADS_ENTER_LINK', lang)}\n\n"
        f"{t('ADS_ENTER_LINK_HINT', lang)}"
    )


@router.message(AdStates.waiting_link)
async def ads_add_link(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    link = message.text.strip()
    if link == "/skip":
        link = None
    elif not (link.startswith("http://") or link.startswith("https://")):
        await message.answer(t("ADS_ERR_LINK_FORMAT", lang))
        return
    await state.update_data(ad_link=link)
    await state.set_state(AdStates.waiting_button_text)
    await message.answer(
        t("ADS_ADD_STEP3_TITLE", lang) + "\n\n"
        f"{t('ADS_ENTER_BUTTON', lang)}"
    )


@router.message(AdStates.waiting_button_text)
async def ads_add_button(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    btn_text = message.text.strip() or t("ADS_BTN_DEFAULT", lang)
    data = await state.get_data()
    await state.clear()

    ad_id = await add_ad(
        text=data["ad_text"],
        link=data.get("ad_link"),
        button_text=btn_text,
    )
    await message.answer(t("ADS_BLOCK_ADDED", lang, id=ad_id))
    # Отправляем в меню
    from aiogram.types import CallbackQuery as FakeCallback
    # Просто вызываем меню админа через message
    await show_ads_after_action(message)


async def show_ads_after_action(target):
    lang = await _admin_lang(target.from_user.id) if hasattr(target, "from_user") else "ru"
    """Показ меню рекламы после действия."""
    config = await get_ads_config()
    ads = await get_all_ads()
    stats = await get_all_ad_stats(days=7)

    status = t("ADMIN_TRIAL_ON", lang) if config.get("enabled") else t("ADMIN_TRIAL_OFF", lang)
    freq_map = {
        "always": t("ADS_FREQ_ALWAYS", lang),
        "daily": t("ADS_FREQ_DAILY", lang),
        "every_n": t("ADS_FREQ_EVERY_N", lang, n=config.get('frequency_value', 5)),
    }
    freq_text = freq_map.get(config.get("frequency", "daily"), "?")

    text = (
        f"{t('ADS_MENU_TITLE', lang)}\n\n"
        f"{t('ADS_CONFIG_ENABLED', lang, status=status)}\n"
        f"{t('ADS_PLACE_MENU', lang)}\n"
        f"{t('ADS_CONFIG_FREQ', lang, freq=freq_text)}\n"
        f"Лимит: {config.get('max_per_day', 3)} показов/день\n\n"
        f"📊 За 7 дней: показов {stats['shows']}, кликов {stats['clicks']}"
    )

    toggle_text = "❌ Выключить" if config.get("enabled") else "✅ Включить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data="ads_toggle_all")],
        [InlineKeyboardButton(text=t("ADS_BTN_ADD", lang), callback_data="ads_add")],
        [InlineKeyboardButton(text=t("ADS_BTN_LIST", lang), callback_data="ads_list")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="ads_settings")],
        [InlineKeyboardButton(text=t("ADS_BTN_STATS", lang), callback_data="ads_stats")],
        [InlineKeyboardButton(text=t("ADS_BTN_HELP", lang), callback_data="ads_help")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ])

    if hasattr(target, "answer"):
        await target.answer(text, reply_markup=keyboard)


# ============================================================
# РЕДАКТИРОВАНИЕ
# ============================================================
@router.callback_query(F.data.startswith("ads_edit_text_"))
async def ads_edit_text_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_text_", ""))
    await state.update_data(ad_id=ad_id)
    await state.set_state(AdStates.waiting_edit_text)
    await callback.message.edit_text(
        f"✏️ Новый ТЕКСТ для блока #{ad_id}:\n\n/cancel — отмена"
    )


@router.message(AdStates.waiting_edit_text)
async def ads_edit_text_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    data = await state.get_data()
    ad_id = data.get("ad_id")
    await update_ad(ad_id, text=message.text.strip())
    await state.clear()
    await message.answer(f"✅ Текст блока #{ad_id} обновлён")


@router.callback_query(F.data.startswith("ads_edit_link_"))
async def ads_edit_link_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_link_", ""))
    await state.update_data(ad_id=ad_id)
    await state.set_state(AdStates.waiting_edit_link)
    await callback.message.edit_text(
        f"🔗 Новая ССЫЛКА для блока #{ad_id}:\n\n/skip — без ссылки\n/cancel — отмена"
    )


@router.message(AdStates.waiting_edit_link)
async def ads_edit_link_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    link = message.text.strip()
    if link == "/skip":
        link = None
    elif link and not (link.startswith("http://") or link.startswith("https://")):
        await message.answer(t("ADS_ERR_LINK_FORMAT", lang))
        return
    data = await state.get_data()
    ad_id = data.get("ad_id")
    await update_ad(ad_id, link=link)
    await state.clear()
    await message.answer(f"✅ Ссылка блока #{ad_id} обновлена")


@router.callback_query(F.data.startswith("ads_edit_button_"))
async def ads_edit_button_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_button_", ""))
    await state.update_data(ad_id=ad_id)
    await state.set_state(AdStates.waiting_edit_button)
    await callback.message.edit_text(
        f"🔘 Новый текст КНОПКИ для блока #{ad_id}:\n\n/cancel — отмена"
    )


@router.message(AdStates.waiting_edit_button)
async def ads_edit_button_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    data = await state.get_data()
    ad_id = data.get("ad_id")
    await update_ad(ad_id, button_text=message.text.strip() or "Подробнее")
    await state.clear()
    await message.answer(f"✅ Кнопка блока #{ad_id} обновлена")


# ============================================================
# УДАЛЕНИЕ / ВКЛ-ВЫКЛ
# ============================================================
@router.callback_query(F.data.startswith("ads_delete_"))
async def ads_delete(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_delete_", ""))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"ads_delete_do_{ad_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"ads_view_{ad_id}")],
    ])
    await callback.message.edit_text(
        f"⚠️ Удалить блок #{ad_id}?", reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("ads_delete_do_"))
async def ads_delete_do(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_delete_do_", ""))
    ok = await delete_ad(ad_id)
    await callback.answer("✅ Удалено" if ok else "❌ Не найден", show_alert=True)
    await ads_list(callback)


@router.callback_query(F.data.startswith("ads_toggle_"))
async def ads_toggle(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    # Защита от конфликтов с другими ads_toggle_* callback
    raw = callback.data.replace("ads_toggle_", "")
    if not raw.isdigit():
        return
    ad_id = int(raw)
    new_state = await toggle_ad(ad_id)
    await callback.answer(
        "✅ Включен" if new_state else "❌ Выключен",
        show_alert=True,
    )
    # Обновляем страницу
    callback.data = f"ads_view_{ad_id}"
    await ads_view(callback)


# ============================================================
# НАСТРОЙКИ
# ============================================================
@router.callback_query(F.data == "ads_settings")
async def ads_settings(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    freq = config.get("frequency", "daily")

    text = (
        "⚙️ НАСТРОЙКИ ПОКАЗА\n\n"
        f"Частота: {freq}\n"
        f"Значение: {config.get('frequency_value', 5)}\n"
        f"Лимит в день: {config.get('max_per_day', 3)}\n"
        f"Показывать админам: {'Да' if config.get('show_to_admins') else 'Нет'}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Частота", callback_data="ads_set_freq")],
        [InlineKeyboardButton(text="🔢 Лимит в день", callback_data="ads_set_max")],
        [InlineKeyboardButton(
            text=f"👑 Админам: {'Да' if config.get('show_to_admins') else 'Нет'}",
            callback_data="ads_admins_toggle"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "ads_set_freq")
async def ads_set_freq(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    freq = config.get("frequency", "daily")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if freq == 'always' else '☐'} Всегда",
            callback_data="ads_freq_always"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if freq == 'daily' else '☐'} 1 раз в день",
            callback_data="ads_freq_daily"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if freq == 'every_n' else '☐'} Каждый N-й раз",
            callback_data="ads_freq_every_n"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="ads_settings")],
    ])
    await callback.message.edit_text(
        "📅 ЧАСТОТА ПОКАЗА\n\nКак часто показывать рекламу?",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("ads_freq_"))
async def ads_freq_set(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    freq = callback.data.replace("ads_freq_", "")
    if freq == "every_n":
        await state.set_state(AdStates.waiting_freq_value)
        await callback.message.edit_text(
            "🔢 Введите число N (каждый N-й раз):\n\n/cancel — отмена"
        )
        return
    await set_ads_config(frequency=freq)
    await callback.answer(f"✅ {freq}", show_alert=True)
    await ads_settings(callback)


@router.message(AdStates.waiting_freq_value)
async def ads_freq_value_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    try:
        n = int(message.text.strip())
        if n < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число ≥ 1")
        return
    await set_ads_config(frequency="every_n", frequency_value=n)
    await state.clear()
    await message.answer(f"✅ Каждый {n}-й раз")


@router.callback_query(F.data == "ads_set_max")
async def ads_set_max(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        return
    await state.set_state(AdStates.waiting_max_per_day)
    await callback.message.edit_text(
        "🔢 Сколько показов в день максимум?\n\nВведите число (0 = без лимита):\n\n/cancel — отмена"
    )


@router.message(AdStates.waiting_max_per_day)
async def ads_max_save(message: Message, state: FSMContext):
    lang = await _admin_lang(message.from_user.id)
    if message.text == "/cancel":
        await state.clear()
        await message.answer(t("ADMIN_CANCELLED", lang))
        return
    try:
        n = int(message.text.strip())
        if n < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число ≥ 0")
        return
    await set_ads_config(max_per_day=n)
    await state.clear()
    await message.answer(f"✅ Лимит: {n} показов/день")


@router.callback_query(F.data == "ads_admins_toggle")
async def ads_toggle_admins(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    config = await get_ads_config()
    await set_ads_config(show_to_admins=not config.get("show_to_admins", False))
    await callback.answer("✅ Изменено", show_alert=True)
    await ads_settings(callback)


# ============================================================
# СТАТИСТИКА
# ============================================================
@router.callback_query(F.data == "ads_stats")
async def ads_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    ads = await get_all_ads()

    text = "📊 СТАТИСТИКА РЕКЛАМЫ (7 дней)\n\n"
    for a in ads:
        st = await get_ad_stats(a["id"], days=7)
        short = a["text"][:40] + "..." if len(a["text"]) > 40 else a["text"]
        status = "✅" if a["enabled"] else "❌"
        text += f"{status} #{a['id']} {short}\n"
        text += f"   Показов: {st['shows']}, Кликов: {st['clicks']}, CTR: {st['ctr']}%\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="ads_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ИНСТРУКЦИЯ
# ============================================================
@router.callback_query(F.data == "ads_help")
async def ads_help(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    text = (
        "📖 ИНСТРУКЦИЯ ПО РЕКЛАМЕ\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 ЧТО ЭТО\n"
        "Реклама показывается пользователям в главном меню. "
        "Вы можете размещать партнёрские ссылки, промокоды, "
        "анонсы и получать доход.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "➕ КАК ДОБАВИТЬ БЛОК\n"
        "1. Нажмите «➕ Добавить блок»\n"
        "2. Введите текст рекламы\n"
        "3. Введите ссылку (https://...)\n"
        "4. Введите текст кнопки (по умолчанию «Подробнее»)\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ НАСТРОЙКИ\n"
        "• Вкл/выкл — общий переключатель\n"
        "• Частота — как часто показывать\n"
        "  - Всегда — при каждом заходе\n"
        "  - 1 раз в день — не спамит\n"
        "  - Каждый N-й раз — промежуточный вариант\n"
        "• Лимит в день — максимум показов\n"
        "• Админам — показывать ли вам\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 СТАТИСТИКА\n"
        "Бот считает:\n"
        "• Показы — сколько раз видели\n"
        "• Клики — сколько нажали\n"
        "• CTR — процент кликов от показов\n\n"
        "Хороший CTR: 5-20%\n"
        "Отличный: >20%\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔗 ГДЕ БРАТЬ РЕКЛАМУ\n"
        "• Admitad — admitad.com\n"
        "• Ozon — партнёрка Ozon\n"
        "• Яндекс.Маркет — партнёрка\n"
        "• КупиКупон — купоны и скидки\n"
        "• Прямые партнёры (астро-сервисы, эзотерика)\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 СОВЕТЫ\n"
        "• Делайте короткий текст (1-2 строки)\n"
        "• Используйте эмодзи в начале\n"
        "• UTM-метки добавляются автоматически\n"
        "• Меняйте блоки раз в 1-2 недели\n"
        "• Не ставьте >3 показов в день\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ ПРАВИЛА\n"
        "• Запрещено: наркотики, оружие, взрослый контент\n"
        "• Запрещено: крипто-скам, финансовые пирамиды\n"
        "• Осторожно: букмекеры (могут забанить бота)\n"
        "• Telegram разрешает рекламу с пометкой #реклама\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🆘 ПОЛЕЗНЫЕ ССЫЛКИ\n"
        "• Документация Telegram: core.telegram.org\n"
        "• Admitad: admitad.com\n"
        "• Партнёрка Ozon: ozon.ru/partners\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


# ============================================================
# ОБРАБОТКА КЛИКА ПО РЕКЛАМЕ
# ============================================================
@router.callback_query(F.data.startswith("ad_click_"))
async def ad_click(callback: CallbackQuery):
    """Клик по рекламе — считаем, показываем ссылку."""
    from database.postgres_db import get_ad, log_ad_action
    try:
        ad_id = int(callback.data.replace("ad_click_", ""))
    except ValueError:
        return

    ad = await get_ad(ad_id)
    if not ad:
        await callback.answer("Реклама не найдена", show_alert=True)
        return

    # Считаем клик
    try:
        await log_ad_action(ad_id, callback.from_user.id, "click")
    except Exception:
        pass

    # Показываем детальную карточку
    full_link = _build_ad_url(ad)
    text = (
        f"📢 РЕКЛАМА\n\n"
        f"{ad['text']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    buttons = []
    if full_link:
        buttons.append([InlineKeyboardButton(
            text="➡️ Открыть сайт", url=full_link
        )])
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад в меню", callback_data="main_menu"
    )])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        try:
            await callback.message.answer(text, reply_markup=keyboard)
        except Exception:
            pass
    await callback.answer()


def _build_ad_url(ad: dict) -> str:
    """
    Строит URL с учётом режима:
    - 'direct' — как есть
    - 'utm' — авто UTM
    - None / 'none' — без ссылки
    """
    link = ad.get("link")
    if not link:
        return ""

    mode = ad.get("link_mode", "direct")

    if mode == "direct":
        return link
    elif mode == "utm":
        # Разделитель ? или &
        sep = "&" if "?" in link else "?"
        utm_source = ad.get("utm_source", "astro_bot")
        utm_medium = ad.get("utm_medium", "ad")
        utm_campaign = f"ad_{ad['id']}"
        return f"{link}{sep}utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"

    return link


# ============================================================
# ВЫБОР РЕЖИМА ССЫЛКИ
# ============================================================
@router.callback_query(F.data.startswith("ads_edit_mode_"))
async def ads_edit_mode(callback: CallbackQuery):
    lang = await _admin_lang(callback.from_user.id)
    if callback.from_user.id not in ADMINS:
        return
    ad_id = int(callback.data.replace("ads_edit_mode_", ""))
    ad = await get_ad(ad_id)
    if not ad:
        await callback.answer(t("ADS_NOT_FOUND", lang), show_alert=True)
        return

    current_mode = ad.get("link_mode", "direct")
    text = (
        f"⚙️ РЕЖИМ ССЫЛКИ для блока #{ad_id}\n\n"
        f"Текущий: {current_mode}\n\n"
        f"• Прямая — админ вводит полный URL\n"
        f"• Авто UTM — бот добавит utm_source, utm_medium, utm_campaign\n"
        f"• Без ссылки — только текст"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if current_mode == 'direct' else '☐'} Прямая ссылка",
            callback_data=f"ads_set_mode_direct_{ad_id}"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if current_mode == 'utm' else '☐'} Авто UTM",
            callback_data=f"ads_set_mode_utm_{ad_id}"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if current_mode == 'none' else '☐'} Без ссылки",
            callback_data=f"ads_set_mode_none_{ad_id}"
        )],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"ads_view_{ad_id}")],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("ads_set_mode_"))
async def ads_set_mode(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return
    # ads_set_mode_direct_5
    rest = callback.data.replace("ads_set_mode_", "")
    parts = rest.rsplit("_", 1)
    if len(parts) != 2:
        return
    mode, ad_id_str = parts
    if not ad_id_str.isdigit():
        return
    ad_id = int(ad_id_str)
    if mode not in ("direct", "utm", "none"):
        return

    # Обновляем в БД (нужно добавить поле link_mode)
    pool = await __import__("database.postgres_db", fromlist=["db"]).db.create_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "ALTER TABLE ads ADD COLUMN IF NOT EXISTS link_mode TEXT DEFAULT 'direct'"
        )
        await conn.execute(
            "UPDATE ads SET link_mode = $1 WHERE id = $2",
            mode, ad_id
        )
    await callback.answer(f"✅ Режим: {mode}", show_alert=True)
    # Перерисовываем
    callback.data = f"ads_view_{ad_id}"
    await ads_view(callback)
