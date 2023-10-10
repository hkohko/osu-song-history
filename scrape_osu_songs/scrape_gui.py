from pathlib import Path

import PySimpleGUI as sG
from threading import Thread

import scrape


def id_exists(values: dict[str, str | bool]):
    user_id, _, _, _ = get_values(values)
    try:
        _ = scrape.make_request(user_id, 100, header=None)
        return True
    except ValueError as err:
        sG.popup(err, title="Error")
        return False


def get_values(values: dict[str, str | bool]):
    user_id = values.get("-ID-")
    idx_start = values.get("-INDEXSTART-")
    idx_stop = values.get("-INDEXSTOP-")
    store_db = values.get("-STOREDB-")
    return user_id, idx_start, idx_stop, store_db


def process_request(values: dict[str, str | bool], window):
    user_id, idx_start, idx_stop, store_db = get_values(values)

    for value in scrape.save_song(
        abs(int(user_id)), abs(int(idx_start)), abs(int(idx_stop))
    ):
        window["-PROGTXT-"].update(
            value=f"Downloading {int(value // 100)} "
            f"of {int(int(idx_stop) // 100)} files"
        )
        window["-PROGRESS-"].update(current_count=value, max=idx_stop)
    window["-PROGTXT-"].update(value="Finished downloading files!")
    if store_db:
        num_file = [filepath for filepath in Path(scrape.SONG_DIR).iterdir()]
        window["-PROGTXTDB-"].update(value="Saving to database...")
        for value in scrape.parse_and_save():
            window["-PROGDB-"].update(current_count=value, max=len(num_file) - 1)
        window["-PROGTXTDB-"].update(value="Database task done!")


def sanitize_input(values: dict[str, str | bool]):
    user_id, idx_start, idx_stop, store_db = get_values(values)
    try:
        _ = int(user_id)
        idx_start = int(idx_start)
        idx_stop = int(idx_stop)
    except (TypeError, ValueError):
        sG.Popup(
            "All input fields only accept integers and must be populated.",
            title="Warning",
        )
        return False
    if idx_start > idx_stop:
        sG.Popup("'start' MUST be smaller than 'stop'", title="Warning")
        return False
    return True


def main():
    sG.theme("SystemDefaultForReal")
    text_id = [sG.Text("ID:")]
    user_id = [sG.InputText("", key="-ID-")]
    start_stop = [
        sG.Text("start:"),
        sG.InputText("0", size=(10, 10), key="-INDEXSTART-"),
        sG.Text("stop:"),
        sG.InputText("", size=(10, 10), key="-INDEXSTOP-"),
    ]
    json_dbstore = [
        sG.Checkbox("Store JSON to Database", default=True, key="-STOREDB-")
    ]
    start_procedure = [sG.Button("Start")]
    text_progress = [sG.Text("No downloads.", key="-PROGTXT-")]
    progress = [sG.ProgressBar(100, orientation="h", size=(30, 10), key="-PROGRESS-")]
    text_progress_db = [sG.Text("No database task.", key="-PROGTXTDB-")]
    progress_db = [sG.ProgressBar(100, orientation="h", size=(30, 10), key="-PROGDB-")]

    layout = [
        text_id,
        user_id,
        start_stop,
        json_dbstore,
        start_procedure,
        text_progress,
        progress,
        text_progress_db,
        progress_db,
    ]

    window = sG.Window("Scrape", layout=layout)

    while True:
        event, values = window.read()
        if event == sG.WIN_CLOSED:
            break
        if event == "Start":
            if sanitize_input(values):
                check = id_exists(values)
                if check:
                    task = Thread(
                        group=None, target=process_request, args=(values, window)
                    )
                    task.start()
        window["-PROGTXT-"].update("No downloads.")
        window["-PROGTXTDB-"].update("No database task.")
        window["-PROGRESS-"].update(current_count=0)
        window["-PROGDB-"].update(current_count=0)
    window.close()


if __name__ == "__main__":
    main()
