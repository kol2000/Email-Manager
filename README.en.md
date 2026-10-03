# Email Manager — Russian / English

Version 1.3.0 replaces the incomplete Chinese/English interface with Russian and English localization, including menus, dialogs, notifications and errors.

## Windows

Extract the entire ZIP and run `EmailManager.exe`. Keep `_internal` next to the executable. No separate Python installation is needed. The executable is unsigned.

Russian is the default. Use **RU / EN** in the lower-left corner or **Settings → Language** to switch. Finish active operations before switching languages.

## Import

Click **Import**. One account per line: `email----password----client_id----refresh_token`.

Password-only IMAP accounts use `email----password`. Delimiters are four hyphens. No real account credentials are included.

The upstream token implementation uses Microsoft Graph/Outlook APIs. IMAP-only refresh tokens may not work. This localization does not change authentication or guarantee availability of legacy Outlook REST endpoints.

## Existing data

Close the old app, back up its `data` folder, and copy that folder next to the new executable. Built-in legacy status values and the default group are migrated automatically. Custom groups, notes, message content and credentials remain intact.

As in the original application, `data/emails.db` stores passwords and refresh tokens without encryption. Do not upload this file to GitHub or distribute it with the app. Settings displays the actual database location.

## Build and test

Windows x64, Python 3.10:

```powershell
py -3.10 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app\main.py
.venv\Scripts\python.exe -m unittest discover -s tests -v
.\build.ps1
```

Output: `dist/EmailManager` and `dist/EmailManager-Windows-x64.zip`.

Tests cover language switching, catalog parity, interpolation fields, legacy database migration, synthetic account import and mocked refresh-token rotation. Both languages were visually checked, and the packaged Windows executable was launched. No live mailbox access or sending was tested.

Forked from [jkcDD/Email-Manager](https://github.com/jkcDD/Email-Manager), commit `9b1ecc1276adce2548138b106402525f0b561ded`. The upstream copyright notice is preserved in [LICENSE](LICENSE). Dependency licenses apply separately.
