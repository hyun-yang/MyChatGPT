import logging

from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel

from util.Constants import Constants, DATABASE_MESSAGE


class SqliteDatabase:
    def __init__(self, db_filename=Constants.DATABASE_NAME):
        self.initialize_vars(db_filename)
        self.initialize_db()
        logging.basicConfig(level=logging.INFO)

    def initialize_vars(self, db_filename):
        self.db_filename = db_filename
        self.db = None
        self.model = None

        # Chat
        self.chat_main_table_name = Constants.CHAT_MAIN_TABLE
        self.chat_detail_table_name = Constants.CHAT_DETAIL_TABLE

        # Image
        self.image_main_table_name = Constants.IMAGE_MAIN_TABLE
        self.image_detail_table_name = Constants.IMAGE_DETAIL_TABLE

        # Image File
        self.image_file_table_name = Constants.IMAGE_FILE_TABLE

        # Vision
        self.vision_main_table_name = Constants.VISION_MAIN_TABLE
        self.vision_detail_table_name = Constants.VISION_DETAIL_TABLE

        # Vision File
        self.vision_file_table_name = Constants.VISION_FILE_TABLE

        # TTS
        self.tts_main_table_name = Constants.TTS_MAIN_TABLE
        self.tts_detail_table_name = Constants.TTS_DETAIL_TABLE

        # STT
        self.stt_main_table_name = Constants.STT_MAIN_TABLE
        self.stt_detail_table_name = Constants.STT_DETAIL_TABLE

        # Prompt
        self.prompt_table_name = Constants.CHAT_PROMPT_TABLE

    def initialize_db(self):
        self.db = QSqlDatabase.addDatabase(Constants.SQLITE_DATABASE)
        self.db.setDatabaseName(self.db_filename)
        if not self.db.open():
            print(f"{DATABASE_MESSAGE.DATABASE_FAILED_OPEN}")
            return

        self.enable_foreign_key()
        self.create_all_tables()

    def enable_foreign_key(self):
        query = QSqlQuery(db=self.db)
        query_string = DATABASE_MESSAGE.DATABASE_PRAGMA_FOREIGN_KEYS_ON
        if not query.exec(query_string):
            print(f"{DATABASE_MESSAGE.DATABASE_ENABLE_FOREIGN_KEY} {query.lastError().text()}")

    def setup_model(self, table_name, filter=""):
        self.model = QSqlTableModel(db=self.db)
        self.model.setTable(table_name)
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        if filter:
            self.model.setFilter(filter)
        self.model.select()

    def create_all_tables(self):
        self.create_chat_main()
        self.create_image_main()
        self.create_image_file()
        self.create_tts_main()
        self.create_stt_main()
        self.create_vision_main()
        self.create_vision_file()
        self.create_prompt()

    def create_chat_main(self):
        query = QSqlQuery()
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {self.chat_main_table_name} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_CHAT_CREATE_TABLE_ERROR} {e}")

    def add_chat_main(self, title):
        query = QSqlQuery()
        query.prepare(f"INSERT INTO {self.chat_main_table_name} (title) VALUES (:title)")
        query.bindValue(":title", title)
        try:
            if query.exec():
                chat_main_id = query.lastInsertId()
                self.create_chat_detail(chat_main_id)
                return chat_main_id
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_CHAT_ADD_ERROR} {e}")
        return None

    def update_chat_main(self, id, title):
        query = QSqlQuery()
        query.prepare(f"UPDATE {self.chat_main_table_name} SET title = :title WHERE id = :id")
        query.bindValue(":title", title)
        query.bindValue(":id", id)
        try:
            if query.exec():
                return True
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_CHAT_UPDATE_ERROR} {e}")
        return False

    def delete_chat_main_entry(self, id):
        try:
            query = QSqlQuery()
            query.prepare(f"DELETE FROM {self.chat_main_table_name} WHERE id = :id")
            query.bindValue(":id", id)
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_CHAT_MAIN_ENTRY_SUCCESS} {id}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_CHAT_MAIN_ENTRY_FAIL} {id}: {e}")
            return False
        return True

    def delete_chat_main(self, id):
        try:
            if not self.delete_chat_detail(id):
                raise Exception(f"Failed to delete chat details for id {id}")
            if not self.delete_chat_main_entry(id):
                raise Exception(f"Failed to delete chat main entry for id {id}")
        except Exception as e:
            logging.error(f"Error deleting chat main for id {id}: {e}")
            return False
        return True

    def get_all_chat_main_list(self):
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {self.chat_main_table_name} ORDER BY created_at DESC")
        try:
            if query.exec():
                results = []
                while query.next():
                    id = query.value(0)
                    title = query.value(1)
                    created_at = query.value(2)
                    results.append({'id': id, 'title': title, 'created_at': created_at})
                return results
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_RETRIEVE_DATA_FAIL} {self.chat_main_table_name}: {e}")
        return []

    def create_chat_detail(self, chat_main_id):
        query = QSqlQuery()
        chat_detail_table = f"{self.chat_detail_table_name}_{chat_main_id}"
        query_string = f"""
          CREATE TABLE IF NOT EXISTS {chat_detail_table}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_main_id INTEGER,
                chat_type TEXT,
                chat_model TEXT,   
                chat TEXT,     
                elapsed_time TEXT, 
                finish_reason TEXT,            
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(chat_main_id) REFERENCES {self.chat_main_table_name}(id) ON DELETE CASCADE 
            )
         """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_CREATE_TABLE_ERROR} {chat_main_id}: {e}")

    def insert_chat_detail(self, chat_main_id, chat_type, chat_model, chat, elapsed_time, finish_reason):
        chat_detail_table = f"{self.chat_detail_table_name}_{chat_main_id}"
        query = QSqlQuery()
        query.prepare(
            f"INSERT INTO {chat_detail_table} (chat_main_id, chat_type, chat_model, chat, elapsed_time, finish_reason) "
            f" VALUES (:chat_main_id, :chat_type, :chat_model, :chat, :elapsed_time, :finish_reason)")
        query.bindValue(":chat_main_id", chat_main_id)
        query.bindValue(":chat_type", chat_type)
        query.bindValue(":chat_model", chat_model)
        query.bindValue(":chat", chat)
        query.bindValue(":elapsed_time", elapsed_time)
        query.bindValue(":finish_reason", finish_reason)
        try:
            return query.exec()
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_INSERT_ERROR} {e}")
            return False

    def delete_chat_detail(self, id):
        try:
            query = QSqlQuery()
            table_name = f"{self.chat_detail_table_name}_{id}"
            query.prepare(f"DROP TABLE IF EXISTS {table_name}")
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_DELETE_TABLE_SUCCESS} {table_name}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_DELETE_ERROR} {table_name}: {e}")
            return False
        return True

    def get_all_chat_details_list(self, chat_main_id):
        chat_detail_table = f"{self.chat_detail_table_name}_{chat_main_id}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {chat_detail_table}")

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_FETCH_ERROR} {chat_main_id}: {query.lastError().text()}")
                return []
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return []

        chat_details_list = []
        while query.next():
            chat_detail = {
                "id": query.value("id"),
                "chat_main_id": query.value("chat_main_id"),
                "chat_type": query.value("chat_type"),
                "chat_model": query.value("chat_model"),
                "chat": query.value("chat"),
                "elapsed_time": query.value("elapsed_time"),
                "finish_reason": query.value("finish_reason"),
                "created_at": query.value("created_at")
            }
            chat_details_list.append(chat_detail)

        return chat_details_list

    def create_prompt(self):
        query = QSqlQuery()
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {self.prompt_table_name} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            prompt TEXT NOT NULL, 
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_PROMPT_CREATE_TABLE_ERROR} {e}")

    def add_prompt(self, title, prompt):
        query = QSqlQuery()
        query_string = f"""
                        INSERT INTO {self.prompt_table_name} (title, prompt)
                        VALUES (:title, :prompt)
                        """
        try:
            query.prepare(query_string)
            query.bindValue(":title", title)
            query.bindValue(":prompt", prompt)
            if not query.exec():
                raise Exception(query.lastError().text())
            return query.lastInsertId()
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_PROMPT_ADD_ERROR} {e}")
        return None

    def update_prompt(self, id, title, prompt):
        query = QSqlQuery()
        query_string = f"""
                        UPDATE {self.prompt_table_name}
                        SET title = :title, prompt = :prompt
                        WHERE id = :id
                        """
        try:
            query.prepare(query_string)
            query.bindValue(":title", title)
            query.bindValue(":prompt", prompt)
            query.bindValue(":id", id)
            if not query.exec():
                raise Exception(query.lastError().text())
            return True
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_PROMPT_UPDATE_ERROR} {e}")
        return False

    def delete_prompt(self, id):
        query = QSqlQuery()
        query_string = f"""
                        DELETE FROM {self.prompt_table_name}
                        WHERE id = :id
                        """
        try:
            query.prepare(query_string)
            query.bindValue(":id", id)
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_PROMPT_DELETE_SUCCESS} {id}")
            return True
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_PROMPT_DELETE_FAIL} {id}: {e}")
        return False

    def create_image_main(self):
        query = QSqlQuery()
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {self.image_main_table_name} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_CREATE_TABLE_ERROR} {e}")

    def add_image_main(self, title):
        query = QSqlQuery()
        query.prepare(f"INSERT INTO {self.image_main_table_name} (title) VALUES (:title)")
        query.bindValue(":title", title)
        try:
            if query.exec():
                image_main_id = query.lastInsertId()
                self.create_image_detail(image_main_id)
                return image_main_id
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_ADD_ERROR} {e}")
        return None

    def update_image_main(self, id, title):
        query = QSqlQuery()
        query.prepare(f"UPDATE {self.image_main_table_name} SET title = :title WHERE id = :id")
        query.bindValue(":title", title)
        query.bindValue(":id", id)
        try:
            if query.exec():
                return True
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_UPDATE_ERROR} {e}")
        return False

    def delete_image_main_entry(self, id):
        try:
            query = QSqlQuery()
            query.prepare(f"DELETE FROM {self.image_main_table_name} WHERE id = :id")
            query.bindValue(":id", id)
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DELETE_SUCCESS} {id}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DELETE_FAIL} {id}: {e}")
            return False
        return True

    def delete_image_detail(self, id):
        try:
            query = QSqlQuery()
            table_name = f"{self.image_detail_table_name}_{id}"
            query.prepare(f"DROP TABLE IF EXISTS {table_name}")
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_DELETE_TABLE_SUCCESS} {table_name}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_DELETE_ERROR} {table_name}: {e}")
            return False
        return True

    def delete_image_main(self, id):
        try:
            if not self.delete_image_main_entry(id):
                raise Exception(f"Failed to delete image main entry for id {id}")
        except Exception as e:
            logging.error(f"Error deleting image main for id {id}: {e}")
            return False
        return True

    def get_all_image_main_list(self):
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {self.image_main_table_name} ORDER BY created_at DESC")
        try:
            if query.exec():
                results = []
                while query.next():
                    id = query.value(0)
                    title = query.value(1)
                    created_at = query.value(2)
                    results.append({'id': id, 'title': title, 'created_at': created_at})
                return results
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_RETRIEVE_DATA_FAIL} {self.image_main_table_name}: {e}")
        return []

    def create_image_detail(self, image_main_id):
        query = QSqlQuery()
        image_detail_table = f"{self.image_detail_table_name}_{image_main_id}"
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {image_detail_table} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            image_main_id TEXT,
                            image_type TEXT,
                            image_model TEXT,
                            image_text TEXT, 
                            image_creation_type TEXT,                            
                            image_revised_prompt TEXT,                            
                            elapsed_time TEXT, 
                            finish_reason TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                            FOREIGN KEY(image_main_id) REFERENCES {self.image_main_table_name}(id) ON DELETE CASCADE
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_CREATE_TABLE_ERROR} {e}")

    def get_all_image_details_list(self, image_main_id):
        image_detail_table = f"{self.image_detail_table_name}_{image_main_id}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {image_detail_table}")

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_FETCH_ERROR} {image_main_id}: {query.lastError().text()}")
                return []
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return []

        image_details_list = []
        while query.next():
            image_detail = {
                "id": query.value("id"),
                "image_main_id": query.value("image_main_id"),
                "image_type": query.value("image_type"),
                "image_model": query.value("image_model"),
                "image_text": query.value("image_text"),
                "image_creation_type": query.value("image_creation_type"),
                "image_revised_prompt": query.value("image_revised_prompt"),
                "elapsed_time": query.value("elapsed_time"),
                "finish_reason": query.value("finish_reason"),
                "created_at": query.value("created_at")
            }
            image_details_list.append(image_detail)

        return image_details_list

    def insert_image_detail(self, image_main_id, image_type, image_model, image_text,
                            image_creation_type, image_revised_prompt, elapsed_time, finish_reason):
        image_detail_table = f"{self.image_detail_table_name}_{image_main_id}"
        query = QSqlQuery()
        query.prepare(
            f"INSERT INTO {image_detail_table} (image_main_id, image_type, image_model, image_text, "
            f" image_creation_type, image_revised_prompt, elapsed_time, finish_reason) "
            f" VALUES (:image_main_id, :image_type, :image_model, :image_text, "
            f" :image_creation_type, :image_revised_prompt, :elapsed_time, :finish_reason)")
        query.bindValue(":image_main_id", image_main_id)
        query.bindValue(":image_type", image_type)
        query.bindValue(":image_model", image_model)
        query.bindValue(":image_text", image_text)
        query.bindValue(":image_creation_type", image_creation_type)
        query.bindValue(":image_revised_prompt", image_revised_prompt)
        query.bindValue(":elapsed_time", elapsed_time)
        query.bindValue(":finish_reason", finish_reason)
        try:
            if query.exec():
                image_detail_id = query.lastInsertId()
                return f"{image_detail_table}_{image_detail_id}"
            else:
                error = query.lastError()
                print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_INSERT_ERROR} {error.text()}")
                return False
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_INSERT_ERROR} {e}")
            return False

    def create_image_file(self):
        query = QSqlQuery()
        image_detail_file_table = f"{self.image_file_table_name}"
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {image_detail_file_table} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            image_detail_id TEXT, 
                            image_detail_file_data BLOB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_FILE_CREATE_TABLE_ERROR} {e}")

    def get_all_image_details_file_list(self, image_detail_id):
        image_detail_file_table = f"{self.image_file_table_name}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {image_detail_file_table} WHERE image_detail_id = :image_detail_id")
        query.bindValue(":image_detail_id", image_detail_id)

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_FILE_FETCH_ERROR} {image_detail_id}: "
                      f" {query.lastError().text()}")
                return []
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return []

        image_detail_file_list = []
        while query.next():
            image_detail = {
                "id": query.value("id"),
                "image_detail_id": query.value("image_detail_id"),
                "image_detail_file_data": query.value("image_detail_file_data"),
                "created_at": query.value("created_at")
            }
            image_detail_file_list.append(image_detail)

        return image_detail_file_list

    def get_image_detail_file(self, image_detail_id):
        image_detail_file_table = f"{self.image_file_table_name}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {image_detail_file_table} WHERE image_detail_id = :image_detail_id")
        query.bindValue(":image_detail_id", image_detail_id)

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_FILE_FETCH_ERROR} {image_detail_id}: "
                      f" {query.lastError().text()}")
                return None
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return None

        if query.next():
            image_detail = {
                "id": query.value("id"),
                "image_detail_id": query.value("image_detail_id"),
                "image_detail_file_data": query.value("image_detail_file_data"),
                "created_at": query.value("created_at")
            }
            return image_detail
        else:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_FILE_NO_RECORD_ERROR} {image_detail_id}")
            return None

    def insert_image_file(self, image_detail_id, image_detail_file_data):
        image_detail_file_table = f"{self.image_file_table_name}"
        query = QSqlQuery()
        query.prepare(
            f"INSERT INTO {image_detail_file_table} (image_detail_id, image_detail_file_data) "
            f" VALUES (:image_detail_id, :image_detail_file_data)")
        query.bindValue(":image_detail_id", image_detail_id)
        query.bindValue(":image_detail_file_data", image_detail_file_data)
        try:
            success = query.exec()
            if not success:
                print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {query.lastError().text()}")
            return success
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_IMAGE_DETAIL_FILE_INSERT_ERROR} {e}")
            return False

    def create_vision_main(self):
        query = QSqlQuery()
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {self.vision_main_table_name} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_VISION_CREATE_TABLE_ERROR} {e}")

    def add_vision_main(self, title):
        query = QSqlQuery()
        query.prepare(f"INSERT INTO {self.vision_main_table_name} (title) VALUES (:title)")
        query.bindValue(":title", title)
        try:
            if query.exec():
                vision_main_id = query.lastInsertId()
                self.create_vision_detail(vision_main_id)
                return vision_main_id
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_VISION_ADD_ERROR} {e}")
        return None

    def update_vision_main(self, id, title):
        query = QSqlQuery()
        query.prepare(f"UPDATE {self.vision_main_table_name} SET title = :title WHERE id = :id")
        query.bindValue(":title", title)
        query.bindValue(":id", id)
        try:
            if query.exec():
                return True
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_VISION_UPDATE_ERROR} {e}")
        return False

    def delete_vision_main_entry(self, id):
        try:
            query = QSqlQuery()
            query.prepare(f"DELETE FROM {self.vision_main_table_name} WHERE id = :id")
            query.bindValue(":id", id)
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_VISION_MAIN_ENTRY_SUCCESS} {id}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_VISION_MAIN_ENTRY_FAIL} {id}: {e}")
            return False
        return True

    def delete_vision_detail(self, id):
        try:
            query = QSqlQuery()
            table_name = f"{self.vision_detail_table_name}_{id}"
            query.prepare(f"DROP TABLE IF EXISTS {table_name}")
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_DELETE_TABLE_SUCCESS} {table_name}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_DELETE_ERROR} {table_name}: {e}")
            return False
        return True

    def delete_vision_main(self, id):
        try:
            if not self.delete_vision_main_entry(id):
                raise Exception(f"Failed to delete vision main entry for id {id}")
        except Exception as e:
            logging.error(f"Error deleting vision main for id {id}: {e}")
            return False
        return True

    def get_all_vision_main_list(self):
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {self.vision_main_table_name} ORDER BY created_at DESC")
        try:
            if query.exec():
                results = []
                while query.next():
                    id = query.value(0)
                    title = query.value(1)
                    created_at = query.value(2)
                    results.append({'id': id, 'title': title, 'created_at': created_at})
                return results
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_RETRIEVE_DATA_FAIL} {self.vision_main_table_name}: {e}")
        return []

    def create_vision_detail(self, vision_main_id):
        query = QSqlQuery()
        vision_detail_table = f"{self.vision_detail_table_name}_{vision_main_id}"
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {vision_detail_table} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            vision_main_id TEXT, 
                            vision_type TEXT,
                            vision_model TEXT,
                            vision_text TEXT,
                            elapsed_time TEXT, 
                            finish_reason TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                            FOREIGN KEY(vision_main_id) REFERENCES {self.vision_main_table_name}(id) ON DELETE CASCADE
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_VISION_DETAIL_CREATE_TABLE_ERROR} {e}")

    def get_all_vision_details_list(self, vision_main_id):
        vision_detail_table = f"{self.vision_detail_table_name}_{vision_main_id}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {vision_detail_table}")

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_VISION_DETAIL_FETCH_ERROR} {vision_main_id}: {query.lastError().text()}")
                return []
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return []

        vision_details_list = []
        while query.next():
            vision_detail = {
                "id": query.value("id"),
                "vision_main_id": query.value("vision_main_id"),
                "vision_type": query.value("vision_type"),
                "vision_model": query.value("vision_model"),
                "vision_text": query.value("vision_text"),
                "elapsed_time": query.value("elapsed_time"),
                "finish_reason": query.value("finish_reason"),
                "created_at": query.value("created_at")
            }
            vision_details_list.append(vision_detail)

        return vision_details_list

    def insert_vision_detail(self, vision_main_id, vision_type, vision_model, vision_text,
                             elapsed_time, finish_reason):
        vision_detail_table = f"{self.vision_detail_table_name}_{vision_main_id}"
        query = QSqlQuery()
        query.prepare(
            f"INSERT INTO {vision_detail_table} (vision_main_id, vision_type, vision_model, vision_text, "
            f" elapsed_time, finish_reason) "
            f" VALUES (:vision_main_id, :vision_type, :vision_model, :vision_text, "
            f" :elapsed_time, :finish_reason)")
        query.bindValue(":vision_main_id", vision_main_id)
        query.bindValue(":vision_type", vision_type)
        query.bindValue(":vision_model", vision_model)
        query.bindValue(":vision_text", vision_text)
        query.bindValue(":elapsed_time", elapsed_time)
        query.bindValue(":finish_reason", finish_reason)
        try:
            if query.exec():
                vision_detail_id = query.lastInsertId()
                return f"{vision_detail_table}_{vision_detail_id}"
            else:
                error = query.lastError()
                print(f"{DATABASE_MESSAGE.DATABASE_VISION_DETAIL_INSERT_ERROR} {error.text()}")
                return False
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_VISION_DETAIL_INSERT_ERROR} {e}")
            return False

    def create_vision_file(self):
        query = QSqlQuery()
        vision_detail_file_table = f"{self.vision_file_table_name}"
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {vision_detail_file_table} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            vision_detail_id TEXT, 
                            vision_detail_file_data BLOB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_VISION_DETAIL_FILE_CREATE_TABLE_ERROR} {e}")

    def get_all_vision_details_file_list(self, vision_detail_id):
        vision_detail_file_table = f"{self.vision_file_table_name}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {vision_detail_file_table} WHERE vision_detail_id = :vision_detail_id")
        query.bindValue(":vision_detail_id", vision_detail_id)

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_VISION_DETAIL_FILE_FETCH_ERROR} {vision_detail_id}: "
                      f" {query.lastError().text()}")
                return []
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return []

        vision_detail_file_list = []
        while query.next():
            vision_detail = {
                "id": query.value("id"),
                "vision_detail_id": query.value("vision_detail_id"),
                "vision_detail_file_data": query.value("vision_detail_file_data"),
                "created_at": query.value("created_at")
            }
            vision_detail_file_list.append(vision_detail)

        return vision_detail_file_list

    def insert_vision_file(self, vision_detail_id, vision_detail_file_data):
        vision_detail_file_table = f"{self.vision_file_table_name}"
        query = QSqlQuery()
        query.prepare(
            f"INSERT INTO {vision_detail_file_table} (vision_detail_id, vision_detail_file_data) "
            f" VALUES (:vision_detail_id, :vision_detail_file_data)")
        query.bindValue(":vision_detail_id", vision_detail_id)
        query.bindValue(":vision_detail_file_data", vision_detail_file_data)
        try:
            success = query.exec()
            if not success:
                print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {query.lastError().text()}")
            return success
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_VISION_DETAIL_FILE_INSERT_ERROR} {e}")
            return False

    def create_tts_main(self):
        query = QSqlQuery()
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {self.tts_main_table_name} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_TTS_CREATE_TABLE_ERROR} {e}")

    def add_tts_main(self, title):
        query = QSqlQuery()
        query.prepare(f"INSERT INTO {self.tts_main_table_name} (title) VALUES (:title)")
        query.bindValue(":title", title)
        try:
            if query.exec():
                tts_main_id = query.lastInsertId()
                self.create_tts_detail(tts_main_id)
                return tts_main_id
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_TTS_ADD_ERROR} {e}")
        return None

    def update_tts_main(self, id, title):
        query = QSqlQuery()
        query.prepare(f"UPDATE {self.tts_main_table_name} SET title = :title WHERE id = :id")
        query.bindValue(":title", title)
        query.bindValue(":id", id)
        try:
            if query.exec():
                return True
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_TTS_UPDATE_ERROR} {e}")
        return False

    def delete_tts_main_entry(self, id):
        try:
            query = QSqlQuery()
            query.prepare(f"DELETE FROM {self.tts_main_table_name} WHERE id = :id")
            query.bindValue(":id", id)
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_TTS_MAIN_ENTRY_SUCCESS} {id}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_TTS_MAIN_ENTRY_FAIL} {id}: {e}")
            return False
        return True

    def delete_tts_detail(self, id):
        try:
            query = QSqlQuery()
            table_name = f"{self.tts_detail_table_name}_{id}"
            query.prepare(f"DROP TABLE IF EXISTS {table_name}")
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_DELETE_TABLE_SUCCESS} {table_name}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_DELETE_ERROR} {table_name}: {e}")
            return False
        return True

    def delete_tts_main(self, id):
        try:
            if not self.delete_tts_main_entry(id):
                raise Exception(f"Failed to delete tts main entry for id {id}")
        except Exception as e:
            logging.error(f"Error deleting tts main for id {id}: {e}")
            return False
        return True

    def get_all_tts_main_list(self):
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {self.tts_main_table_name} ORDER BY created_at DESC")
        try:
            if query.exec():
                results = []
                while query.next():
                    id = query.value(0)
                    title = query.value(1)
                    created_at = query.value(2)
                    results.append({'id': id, 'title': title, 'created_at': created_at})
                return results
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_RETRIEVE_DATA_FAIL} {self.tts_main_table_name}: {e}")
        return []

    def create_tts_detail(self, tts_main_id):
        query = QSqlQuery()
        tts_detail_table = f"{self.tts_detail_table_name}_{tts_main_id}"
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {tts_detail_table} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            tts_main_id TEXT, 
                            tts_type TEXT,
                            tts_model TEXT,
                            tts_text TEXT,
                            tts_response_format TEXT,  
                            tts_data BLOB,                            
                            elapsed_time TEXT, 
                            finish_reason TEXT,   
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(tts_main_id) REFERENCES {self.tts_main_table_name}(id) ON DELETE CASCADE  
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_TTS_DETAIL_CREATE_TABLE_ERROR} {e}")

    def get_all_tts_details_list(self, tts_main_id):
        tts_detail_table = f"{self.tts_detail_table_name}_{tts_main_id}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {tts_detail_table}")

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_TTS_DETAIL_FETCH_ERROR} {tts_main_id}: {query.lastError().text()}")
                return []
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return []

        tts_details_list = []
        while query.next():
            tts_detail = {
                "id": query.value("id"),
                "tts_main_id": query.value("tts_main_id"),
                "tts_type": query.value("tts_type"),
                "tts_model": query.value("tts_model"),
                "tts_text": query.value("tts_text"),
                "tts_response_format": query.value("tts_response_format"),
                "tts_data": query.value("tts_data"),
                "elapsed_time": query.value("elapsed_time"),
                "finish_reason": query.value("finish_reason"),
                "created_at": query.value("created_at")
            }
            tts_details_list.append(tts_detail)

        return tts_details_list

    def insert_tts_detail(self, tts_main_id, tts_type, tts_model, tts_text, tts_response_format,
                          tts_data, elapsed_time, finish_reason):
        tts_detail_table = f"{self.tts_detail_table_name}_{tts_main_id}"
        query = QSqlQuery()
        query.prepare(
            f"INSERT INTO {tts_detail_table} (tts_main_id, tts_type, tts_model, tts_text, tts_response_format, "
            f" tts_data, elapsed_time, finish_reason) "
            f" VALUES (:tts_main_id, :tts_type, :tts_model, :tts_text, :tts_response_format,"
            f" :tts_data, :elapsed_time, :finish_reason)")
        query.bindValue(":tts_main_id", tts_main_id)
        query.bindValue(":tts_type", tts_type)
        query.bindValue(":tts_model", tts_model)
        query.bindValue(":tts_text", tts_text)
        query.bindValue(":tts_response_format", tts_response_format)
        query.bindValue(":tts_data", tts_data)
        query.bindValue(":elapsed_time", elapsed_time)
        query.bindValue(":finish_reason", finish_reason)
        try:
            if query.exec():
                return True
            else:
                error = query.lastError()
                print(f"{DATABASE_MESSAGE.DATABASE_TTS_DETAIL_INSERT_ERROR} {error.text()}")
                return False
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_TTS_DETAIL_INSERT_ERROR} {e}")
            return False

    def create_stt_main(self):
        query = QSqlQuery()
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {self.stt_main_table_name} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_STT_CREATE_TABLE_ERROR} {e}")

    def add_stt_main(self, title):
        query = QSqlQuery()
        query.prepare(f"INSERT INTO {self.stt_main_table_name} (title) VALUES (:title)")
        query.bindValue(":title", title)
        try:
            if query.exec():
                stt_main_id = query.lastInsertId()
                self.create_stt_detail(stt_main_id)
                return stt_main_id
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_STT_ADD_ERROR} {e}")
        return None

    def update_stt_main(self, id, title):
        query = QSqlQuery()
        query.prepare(f"UPDATE {self.stt_main_table_name} SET title = :title WHERE id = :id")
        query.bindValue(":title", title)
        query.bindValue(":id", id)
        try:
            if query.exec():
                return True
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_STT_UPDATE_ERROR} {e}")
        return False

    def delete_stt_main_entry(self, id):
        try:
            query = QSqlQuery()
            query.prepare(f"DELETE FROM {self.stt_main_table_name} WHERE id = :id")
            query.bindValue(":id", id)
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_STT_MAIN_ENTRY_SUCCESS} {id}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_STT_MAIN_ENTRY_FAIL} {id}: {e}")
            return False
        return True

    def delete_stt_detail(self, id):
        try:
            query = QSqlQuery()
            table_name = f"{self.stt_detail_table_name}_{id}"
            query.prepare(f"DROP TABLE IF EXISTS {table_name}")
            if not query.exec():
                raise Exception(query.lastError().text())
            logging.info(f"{DATABASE_MESSAGE.DATABASE_DELETE_TABLE_SUCCESS} {table_name}")
        except Exception as e:
            logging.error(f"{DATABASE_MESSAGE.DATABASE_CHAT_DETAIL_DELETE_ERROR} {table_name}: {e}")
            return False
        return True

    def delete_stt_main(self, id):
        try:
            if not self.delete_stt_main_entry(id):
                raise Exception(f"Failed to delete stt main entry for id {id}")
        except Exception as e:
            logging.error(f"Error deleting stt main for id {id}: {e}")
            return False
        return True

    def get_all_stt_main_list(self):
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {self.stt_main_table_name} ORDER BY created_at DESC")
        try:
            if query.exec():
                results = []
                while query.next():
                    id = query.value(0)
                    title = query.value(1)
                    created_at = query.value(2)
                    results.append({'id': id, 'title': title, 'created_at': created_at})
                return results
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_RETRIEVE_DATA_FAIL} {self.stt_main_table_name}: {e}")
        return []

    def create_stt_detail(self, stt_main_id):
        query = QSqlQuery()
        stt_detail_table = f"{self.stt_detail_table_name}_{stt_main_id}"
        query_string = f"""
                        CREATE TABLE IF NOT EXISTS {stt_detail_table} 
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            stt_main_id TEXT, 
                            stt_type TEXT,
                            stt_model TEXT,
                            stt_text TEXT,
                            stt_response_format TEXT,  
                            stt_data BLOB,                            
                            elapsed_time TEXT, 
                            finish_reason TEXT, 
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(stt_main_id) REFERENCES {self.stt_main_table_name}(id) ON DELETE CASCADE 
                        )
                        """
        try:
            query.exec(query_string)
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_STT_DETAIL_CREATE_TABLE_ERROR} {e}")

    def get_all_stt_details_list(self, stt_main_id):
        stt_detail_table = f"{self.stt_detail_table_name}_{stt_main_id}"
        query = QSqlQuery()
        query.prepare(f"SELECT * FROM {stt_detail_table}")

        try:
            if not query.exec():
                print(f"{DATABASE_MESSAGE.DATABASE_STT_DETAIL_FETCH_ERROR} {stt_main_id}: {query.lastError().text()}")
                return []
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {e}")
            return []

        stt_details_list = []
        while query.next():
            stt_detail = {
                "id": query.value("id"),
                "stt_main_id": query.value("stt_main_id"),
                "stt_type": query.value("stt_type"),
                "stt_model": query.value("stt_model"),
                "stt_text": query.value("stt_text"),
                "stt_response_format": query.value("stt_response_format"),
                "stt_data": query.value("stt_data"),
                "elapsed_time": query.value("elapsed_time"),
                "finish_reason": query.value("finish_reason"),
                "created_at": query.value("created_at")
            }
            stt_details_list.append(stt_detail)

        return stt_details_list

    def insert_stt_detail(self, stt_main_id, stt_type, stt_model, stt_text, stt_response_format,
                          stt_data, elapsed_time, finish_reason):
        stt_detail_table = f"{self.stt_detail_table_name}_{stt_main_id}"
        query = QSqlQuery()
        query.prepare(
            f"INSERT INTO {stt_detail_table} (stt_main_id, stt_type, stt_model, stt_text, stt_response_format, "
            f" stt_data, elapsed_time, finish_reason) "
            f" VALUES (:stt_main_id, :stt_type, :stt_model, :stt_text, :stt_response_format,"
            f" :stt_data, :elapsed_time, :finish_reason)")
        query.bindValue(":stt_main_id", stt_main_id)
        query.bindValue(":stt_type", stt_type)
        query.bindValue(":stt_model", stt_model)
        query.bindValue(":stt_text", stt_text)
        query.bindValue(":stt_response_format", stt_response_format)
        query.bindValue(":stt_data", stt_data)
        query.bindValue(":elapsed_time", elapsed_time)
        query.bindValue(":finish_reason", finish_reason)
        try:
            success = query.exec()
            if not success:
                print(f"{DATABASE_MESSAGE.DATABASE_EXECUTE_QUERY_ERROR} {query.lastError().text()}")
            return success
        except Exception as e:
            print(f"{DATABASE_MESSAGE.DATABASE_STT_DETAIL_INSERT_ERROR} {e}")
            return False

