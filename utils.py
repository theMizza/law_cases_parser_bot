from bot_db_connector import *


@with_db_connection(db)
def create_tables():
    try:
        db.create_tables([Users, Cases, CaseData, CaseMovements, CaseSides, ExecutiveLists])
    except Exception as e:
        print(e)


if __name__ == '__main__':
    create_tables()
