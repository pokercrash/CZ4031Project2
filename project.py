import json
import tkinter as tk
from tkinter import font, ttk, messagebox
from typing import Text
import interface
from node_types import ATTRIBUTE
import sqlparse
import node_types
import psycopg2
import annotation


def retrieveInput():
    inputValue = query_text.get('1.0', 'end-1c')
    return inputValue


if __name__ == '__main__':

    root = tk.Tk()
    root.title('Input Query')
    root.iconphoto(False, tk.PhotoImage(file='tree.png'))

    button_font = font.Font(
        family='Google Sans Display', size=12, weight='bold')
    text_font = font.Font(family='Fira Code Retina', size=12)
    label_font = font.Font(family='Google Sans Display', size=12)

    query_label = tk.Label(
        root, text='Enter your SQL query here', font=label_font)
    query_text = tk.Text(root, font=text_font, height=20)

    # drawing the execute button
    execute_button = tk.Button(root, text='EXECUTE', padx=12, bg='#7d8ed1', fg='white', font=button_font,
                               anchor='center', command=lambda: interface.get_json(retrieveInput()))

    # button execution to execute function
    execute_button.bind(
        '<Button-1>', lambda event: interface.execute_query(root, retrieveInput()))

    query_scrollbar = tk.Scrollbar(
        root, orient='vertical', command=query_text.yview)

    query_text.configure(yscrollcommand=query_scrollbar.set)

    query_label.grid(row=0, sticky='w', padx=12, pady=(12, 0))
    query_text.grid(row=1, padx=(12, 0))
    query_scrollbar.grid(row=1, column=1, sticky='ns', padx=(0, 12))

    execute_button.grid(row=4, sticky='e', padx=12, pady=12)

    root.mainloop()
