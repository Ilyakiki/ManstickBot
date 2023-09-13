from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import time
import sqlite3 as sq
import matplotlib.pyplot as plt

import os

storage = MemoryStorage()
bot = Bot(token='6520241318:AAFf4KKr-pZEJvgQV199p4r2G_QXSaXJPvM')
dp = Dispatcher(bot, storage=storage)

# Подключение к базе данных
async def on_startup(_):
    global base, cur
    base = sq.connect('stick.db')
    cur = base.cursor()
    if base:
        print('База подключена')
    base.execute('CREATE TABLE IF NOT EXISTS stick_table(uid,username,chatid,long INTEGER,updatetime)')
    base.commit()
    print('Бот онлайн')


urlkb = InlineKeyboardMarkup(row_width=1)
urlButton = InlineKeyboardButton(text='Добавить бота в беседу', url='https://t.me/manstickerbot?startgroup=true')
urlkb.add(urlButton)


# Действие на комманду /start
@dp.message_handler(commands=['start'])
async def start_send(message: types.Message):
    await message.answer(
        f'Хай. Ты хочешь помериться палками со своими друзьями? Тогда добавь ManStickBot к себев беседу.\n\n\n В чем суть? Раз в сутки игрок может написать комманду /stick После чего у игрока изменится палка (от -10 до 15 см).\n\n Если остались вопросы, то /help',
        reply_markup=urlkb)


# Действие на комманду /help
@dp.message_handler(commands=['help'])
async def help_send(message: types.Message):
    await message.answer('/stick - Изменит размер вашей палки (от -5 до +10 см) (функция доступна раз в сутки)\n /time - проверит сколько времени осталось до использования /stick\n /top_stick - Выведет топ палок этого чата\n /diagram - Выведет топ палок этого чата в виде диаграммы')


# Действие на комманду /stick, увеличит или уменьшит размер палки
@dp.message_handler(commands=['stick', 'stick@manstickerbot'])
async def echo_send(message: types.Message):
    if message.text == '/stick' or '/stick@manstickerbot':
        if message.chat.type == 'supergroup' or 'group':
            try:
                x = cur.execute(f'SELECT * FROM stick_table WHERE chatid=? AND uid=?',
                                (message.chat.id, message.from_user.id)).fetchall()
                times = time.time()
                if times - x[0][-1] < 20:

                    await message.answer(f'@{message.from_user.username}, Не торопись дружок!')

                else:
                    l = random.randint(10, 50)
                    await message.answer(
                        f'@{message.from_user.username}, Ваша палка была {x[0][-2]} см, она изменилась на {l} см, теперь она {x[0][-2] + l}. Следующая попытка завтра!')
                    cur.execute('UPDATE stick_table SET long=? WHERE chatid=? AND uid=?',
                                (x[0][-2] + l, message.chat.id, message.from_user.id))
                    cur.execute('UPDATE stick_table SET updatetime=? WHERE chatid=? AND uid=?',
                                (times, message.chat.id, message.from_user.id))
                    base.commit()
            except:
                l = random.randint(-5, 10)
                x = cur.execute(f'INSERT INTO stick_table VALUES (?, ?, ?, ?, ?)',
                                (message.from_user.id, str(message.from_user.username), message.chat.id, l, times))
                base.commit()
                await message.answer(f'@{message.from_user.username},Ваша палка равна {l} см')
        else:
            await message.answer(f'Бот работает только в группах', reply_markup=urlkb)

# Действие на комманду /time, выводит таймер до следующего применения
@dp.message_handler(commands=['time', 'time@manstickerbot'])
async def time_message(message: types.Message):
    if message.text == '/time' or '/time@manstickerbot':
        if message.chat.type == 'supergroup' or 'group':
            try:
                x = cur.execute(f'SELECT * FROM stick_table WHERE chatid=? AND uid=?',
                                (message.chat.id, message.from_user.id)).fetchall()
                z = 86400 - (time.time() - x[0][-1])
                await message.answer(
                    f'Долго вам еще ждать @{message.from_user.username} ({time.strftime("%H:%M:%S", time.gmtime(z))})')
            except:
                await message.answer(f'Что-то пошло не так. Возможно вы ни разу не использовали /stick')
        else:
            await message.answer(f'Бот работает только в группах', reply_markup=urlkb)
    # await message.reply(message.text)
    # await bot.send_message(message.from_user.id,message.text)

# Действие на комманду /top_stick, выведет топ палок этого чата
@dp.message_handler(commands=['top_stick', '/top_stick@manstickerbot'])
async def top_sticks(message: types.Message):
    if message.chat.type == 'supergroup' or 'group':
        try:
            x = cur.execute(f'SELECT * FROM stick_table WHERE chatid=?', (message.chat.id,)).fetchall()
            names = [i[1] for i in x]
            long = [i[-2] for i in x]
            z = zip(names, long)
            z = sorted(list(z), key=lambda x: x[1], reverse=True)
        except:
            await message.answer(f'Что-то пошло не так.')
        if message.text == '/top_stick' or '/top_stick@manstickerbot':
            top_str = 'Топ палок:\n\n'
            for i in range(len(z)):
                top_str += f'@{z[i][0]} — {z[i][1]} см\n\n'
            await message.answer(f'{top_str}')
    else:
        await message.answer(f'Бот работает только в группах', reply_markup=urlkb)

# Действие на комманду /top_stick, выведет топ палок этого в виде диаграммы
@dp.message_handler(commands=['diagram', '/diagram@manstickerbot'])
async def top_sticks_diagram(message: types.Message):
    if message.chat.type == 'supergroup' or 'group':
        try:
            x = cur.execute(f'SELECT * FROM stick_table WHERE chatid=?', (message.chat.id,)).fetchall()
            names = [i[1] + ' - ' + str(i[-2]) + ' см' for i in x]
            long = [i[-2] for i in x]
            z = zip(names, long)
            z = sorted(filter(lambda x: x[1] >= 0, list(z)), key=lambda x: x[1], reverse=True)
            names = [i[0] for i in z]
            long = [i[-1] for i in z]
            explode = [0 for i in z]
            explode[0] = 0.05
        except:
            await message.answer(f'Что-то пошло не так.Возможно никто из группы еще не использовал /stick')
        if message.text == '/diagram' or '/diagram@manstickerbot':
            def make_autopct(values):
                def my_autopct(pct):
                    total = sum(values)
                    val = int(round(pct * total / 100.0))
                    return '{v:d}'.format(p=pct, v=val)
                return my_autopct

            plt.pie(long, labels=names, labeldistance=None, autopct=make_autopct(long), explode=explode,
                    pctdistance=0.75, wedgeprops={'width': 0.5, 'lw': 2, 'edgecolor': "white"}, center=(-1.0, 0.0))

            plt.legend(bbox_to_anchor=(0.7, 0.8))

            global rand
            rand = random.randint(1, 100)
            plt.savefig(f'diagram{rand}.png')
            plt.close()
            with open(f'diagram{rand}.png', 'rb') as photo:
                await bot.send_photo(chat_id=message.chat.id, photo=photo)
            os.remove(f'diagram{rand}.png')
    else:
        await message.answer(f'Бот работает только в группах', reply_markup=urlkb)


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
