from users import forms


def validate_not_empty(value):
    if value == "":
        raise forms.ValidationError(
            "А кто поле заполнять будет, Пушкин?", params={"value": value}
        )
