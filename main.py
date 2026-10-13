from database import initialize_database
from ui.main_window import MainWindow


def main() -> None:
    db_path = initialize_database()
    app = MainWindow(db_path=db_path)
    app.mainloop()


if __name__ == '__main__':
    main()
