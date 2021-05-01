def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu

def log(chat_id, data, func, level):
    # Logging function
    
    timestamp = datetime.now()
    logs.insert_one({"timestamp": timestamp, "chat_id": chat_id, "func": func, "data": data, "level": level})
