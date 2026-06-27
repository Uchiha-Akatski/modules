# meta developer: @Itachi_Uchiha_sss

import html
from .. import loader, utils


class DBMod(loader.Module):
    """Module to check and clean the database\nBe careful while using this module!"""

    strings = {
        "name": "DBMod",
        "del_text": "<b>Choose a module to delete from the database</b>\n\n⚠ Be careful and do not delete the core modules",
        "deleted": "Key {key} deleted from Database",
        "close_btn": "🔻 Close",
        "back_btn": "◀ Back",
        "del_btn": "❌ Delete",
        "not_found": "Key {key} not found in Database",
        "too_long": "⚠️ Data is too large ({size} chars). Showing first {limit} chars:\n\n{data}\n\n... (truncated)",
        "data_too_large": "⚠️ Data is too large ({size} chars). Download as file?",
        "download_btn": "📥 Download as file",
    }

    strings_ru = {
        "del_text": "<b>Выберите модуль для удаления из базы данных</b>\n\n⚠ Будьте осторожны и не удаляйте основные модули",
        "deleted": "Ключ {key} удален из базы данных",
        "close_btn": "🔻 Закрыть",
        "back_btn": "◀ Назад",
        "del_btn": "❌ Очистить",
        "not_found": "Ключ {key} не найден в базе данных",
        "too_long": "⚠️ Данные слишком большие ({size} символов). Показано первых {limit} символов:\n\n{data}\n\n... (обрезано)",
        "data_too_large": "⚠️ Данные слишком большие ({size} символов). Скачать как файл?",
        "download_btn": "📥 Скачать как файл",
    }

    MAX_MESSAGE_LEN = 4096
    MAX_PRE_CONTENT = 3500  # Запас для форматирования и клавиатуры

    async def delete_db(self, call, item):
        """Clean db of the module"""
        if item[0] in self._db.keys():
            self._db.pop(f"{item[0]}")
            self._db.save()
            await call.edit(
                self.strings["del_text"], reply_markup=self.generate_info_all_markup()
            )
            await call.answer(self.strings["deleted"].format(key=item[0]))
            return True
        await call.answer(self.strings["not_found"].format(key=item[0]))
        return False

    async def info_db(self, call, item):
        """Info about db of the module"""
        if item[0] in self._db.keys():
            # Формируем текст
            data_str = str(item[1])
            data_len = len(data_str)
            
            # Если данные слишком большие
            if data_len > self.MAX_PRE_CONTENT:
                # Обрезаем данные
                truncated = data_str[:self.MAX_PRE_CONTENT]
                text = self.strings["too_long"].format(
                    size=data_len,
                    limit=self.MAX_PRE_CONTENT,
                    data=html.escape(truncated)
                )
                
                # Создаем клавиатуру с опцией скачивания
                markup = self.generate_delete_markup_with_download(item)
            else:
                # Нормальные данные
                text = f"<pre><code class='language-{item[0]}'>{html.escape(data_str)}</code></pre>"
                markup = self.generate_delete_markup(item)
            
            await call.edit(text, reply_markup=markup)
            return True
            
        await call.answer(self.strings["not_found"].format(key=item[0]))
        return False

    def generate_delete_markup_with_download(self, item):
        """Generate markup with download option for large data"""
        markup = [[]]
        markup[-1].append(
            {
                "text": self.strings["back_btn"],
                "callback": self.main_menu,
            }
        )
        markup[-1].append(
            {
                "text": self.strings["download_btn"],
                "callback": self.download_data,
                "args": [item],
            }
        )
        markup[-1].append(
            {
                "text": self.strings["del_btn"],
                "callback": self.delete_db,
                "args": [item],
            }
        )
        return markup

    def generate_delete_markup(self, item):
        """Generate markup for inline form"""
        markup = [[]]
        markup[-1].append(
            {
                "text": self.strings["back_btn"],
                "callback": self.main_menu,
            }
        )
        markup[-1].append(
            {
                "text": self.strings["del_btn"],
                "callback": self.delete_db,
                "args": [item],
            }
        )
        return markup

    async def download_data(self, call, item):
        """Send database content as a file"""
        if item[0] not in self._db.keys():
            await call.answer(self.strings["not_found"].format(key=item[0]))
            return
        
        data_str = str(item[1])
        
        # Создаем файл в памяти
        import io
        file_content = f"Module: {item[0]}\n\n{data_str}"
        file_bytes = io.BytesIO(file_content.encode('utf-8'))
        file_bytes.name = f"{item[0]}_db_data.txt"
        
        # Отправляем файл
        await call.message.answer_document(
            document=file_bytes,
            caption=f"📦 Database data for module: {item[0]}",
            reply_to_message_id=call.message.message_id
        )
        await call.answer("✅ Data sent as file")
        
        # Возвращаемся в меню
        await self.main_menu(call.message)

    async def main_menu(self, message, page_num=0):
        await utils.answer(
            message,
            self.strings["del_text"],
            reply_markup=self.generate_info_all_markup(page_num),
        )

    def generate_info_all_markup(self, page_num=0):
        """Generate markup for inline form with 3x3 grid and navigation buttons"""
        items = list(self._db.items())
        markup = [[]]
        items_per_page = 9
        num_pages = len(items) // items_per_page + (
            1 if len(items) % items_per_page != 0 else 0
        )

        page_items = items[page_num * items_per_page : (page_num + 1) * items_per_page]
        for item in page_items:
            if len(markup[-1]) == 3:
                markup.append([])
            markup[-1].append(
                {
                    "text": f"{item[0]}",
                    "callback": self.info_db,
                    "args": [item],
                }
            )

        nav_markup = []
        if page_num > 0:
            nav_markup.append(
                {
                    "text": "◀",
                    "callback": self.change_page,
                    "args": [page_num - 1],
                }
            )
        nav_markup.append(
            {
                "text": f"{page_num + 1}/{num_pages}",
                "callback": self.change_page,
                "args": [page_num],
            }
        )
        if page_num < num_pages - 1:
            nav_markup.append(
                {
                    "text": "▶",
                    "callback": self.change_page,
                    "args": [page_num + 1],
                }
            )

        if nav_markup:
            markup.append(nav_markup)

        markup.append([])
        markup[-1].append(
            {
                "text": self.strings["close_btn"],
                "action": "close",
            }
        )

        return markup

    async def change_page(self, call, page_num):
        """Change to the specified page"""
        await call.edit(
            self.strings["del_text"],
            reply_markup=self.generate_info_all_markup(page_num),
        )

    @loader.command(
        ru_doc="Посмотреть модуль в базе данных",
    )
    async def mydbcmd(self, message):
        """Check the info of the modules"""
        await self.main_menu(message=message)
