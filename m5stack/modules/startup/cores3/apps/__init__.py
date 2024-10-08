# SPDX-FileCopyrightText: 2024 M5Stack Technology CO LTD
#
# SPDX-License-Identifier: MIT

_attrs = {
    "ListApp": "app_list",
    "RunApp": "app_run",
    "DevApp": "dev",
    "EzDataApp": "ezdata",
    "SettingsApp": "settings",
    "StatusBarApp": "status_bar",
}


def __getattr__(attr):
    mod = _attrs.get(attr, None)
    if mod is None:
        raise AttributeError(attr)
    value = getattr(__import__(mod, None, None, True, 1), attr)
    globals()[attr] = value
    return value
