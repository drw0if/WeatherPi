import sqlite3
import os
import typing as t

class DBException(Exception):
    pass


class DB:
    DBNAME : str = os.environ.get('DATABASE_NAME', 'db/database.db')
    INSTANCE : "DB" = None

    @staticmethod
    def get_instance() -> "DB":
        if DB.INSTANCE is None:
            DB.INSTANCE = DB()
        
        return DB.INSTANCE


    def __init__(self):
        try:
            self.con = sqlite3.connect(DB.DBNAME)
            self.con.row_factory = sqlite3.Row
        except sqlite3.DatabaseError as err:
            raise DBException("Error on database connection")

    def __del__(self):
        self.con.close()

    def get_cursor(self):
        return self.con.cursor()
    
    def commit(self):
        return self.con.commit()

    def get_station_by_token(self, token) -> t.Any:
        cursor = self.get_cursor()
        res = cursor.execute('SELECT * FROM station WHERE api_token = ?', (token,))
        return res.fetchone()


    def add_record(self, data, station) -> int:
        cursor = self.get_cursor()
        res = cursor.execute("""
            INSERT INTO record(broadcasted_station_id, battery, timestamp, temperature, humidity, wind_speed, wind_dir, wind_gust, rain, station_id)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (data['broadcasted_station_id'], data['battery'], data['timestamp'], data["temperature"], data["humidity"], data["wind_speed"], data["wind_dir"], data["wind_gust"], data["rain"], station["id"]))

        self.commit()
        return res.lastrowid


    def get_last_record(self, station_id):
        cursor = self.get_cursor()
        res = cursor.execute("""
            SELECT *
            FROM record r
            WHERE r.station_id = ?
            ORDER BY timestamp DESC
            LIMIT 1;
        """, (station_id,))

        record = res.fetchone()
        return dict(record) if record else record


if __name__ == "__main__":
    print("Going to install the database")

    db = DB.get_instance()

    cursor = db.get_cursor()

    cursor.execute("""
        CREATE TABLE station(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            description TEXT,
            
            api_token VARCHAR(32)
        );
    """)

    cursor.execute("""
        CREATE TABLE record(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            broadcasted_station_id INTEGER,
            battery BOOL,
            timestamp INTEGER,
            temperature DECIMAL(3, 2),
            humidity INTEGER,
            wind_speed DECIMAL(5, 2),
            wind_dir INTEGER,
            wind_gust DECIMAL(5, 2),
            rain DECIMAL(8, 2),
                   
            station_id INTEGER,
            FOREIGN KEY(station_id) REFERENCES station(id)
        );
    """)

    import random

    name = "weather-pi@home"
    description = "Bresser 6 in 1 weather station @ Home"
    first_station_api_key = ''.join(random.choices('0123456789abcdef', k=32))

    cursor.execute("""
        INSERT INTO station (name, description, api_token)
        VALUES (?, ?, ?);
    """, (name, description, first_station_api_key))

    db.commit()

    print(f"Created {name} for {description} with api token: {first_station_api_key}")

