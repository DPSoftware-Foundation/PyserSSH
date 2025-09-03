from PyserSSH.extensions.XHandler import Division
from PyserSSH.extensions.dialogplus import Window, TextWidget, Dialog, MenuWidget, TextInputWidget
from PyserSSH.system.clientype import Client

div = Division("dialogplus", "Test command for dialog+ extension module", category="Test Function (Dialog+)")

@div.command("dialogplus")
def dialogplus_text(client: Client):
    window = Window(title="Information", border=True)
    window.add_widget(TextWidget(text="Hello World!"), x=0, y=0)

    dialog = Dialog(client, window)
    dialog.show()

@div.command("dialogplus_menu")
def dialogplus_menu(client: Client):
    window = Window(title="Choose Option", border=True)

    description = "Please choose the options"

    window.add_widget(TextWidget(text=description), x=0, y=0)
    menu_y = len(description.split('\n')) + 1

    window.add_widget(MenuWidget(items=["Option 1", "Option 2", "Option 3"]), x=0, y=menu_y)

    dialog = Dialog(client, window)
    result = dialog.show()
    if result:
        client.sendln(f"Selected: {result['item']} at index {result['index']}")

@div.command("dialogplus_input")
def dialogplus_input(client: Client):
    window = Window(title="User Input", border=True)

    window.add_widget(TextWidget(text="Enter your name:"), x=0, y=0)
    window.add_widget(TextInputWidget(password=False, max_length=None), x=0, y=2)

    dialog = Dialog(client, window)
    result = dialog.show()

    if result:
        client.sendln(f"Selected: {result['item']} at index {result['index']}")

@div.command("dialogplus_form")
def dialogplus_form(client: Client):
    window = Window(title="User Registration Form", border=True)

    # Add form fields
    window.add_widget(TextWidget(text="Please fill out the registration form:"), x=0, y=0)

    window.add_widget(TextWidget(text="Username:"), x=0, y=2)
    username_input = window.add_widget(TextInputWidget(placeholder="Enter username"), x=0, y=3)

    window.add_widget(TextWidget(text="Password:"), x=0, y=5)
    password_input = window.add_widget(TextInputWidget(password=True, placeholder="Enter password"), x=0, y=6)

    window.add_widget(TextWidget(text="User Type:"), x=0, y=8)
    user_type_menu = window.add_widget(MenuWidget(items=["Regular User", "Administrator", "Guest"]), x=0, y=9)

    # Custom dialog handling
    dialog = Dialog(client, window)
    result = dialog.show()

    if result:
        # Collect all form data
        form_data = {
            'username': username_input.get_text(),
            'password': password_input.get_text(),
            'user_type': user_type_menu.get_selected_item()
        }
        client.sendln(str(form_data))

