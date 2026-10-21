# Wish List

A Flask web application for creating gift wish lists for any occasion. A registered user creates events (a birthday, a wedding, New Year), fills each event with gifts, and shares a single private link with friends and family. Guests do not need an account: they open the link, see the list, and reserve the gift they plan to give, so nobody ends up with duplicates and the owner keeps the surprise.

## Why this project

Wish lists are usually shared in chats as plain text, and people end up buying the same present twice or asking "has anyone already taken this?" This project solves it with a small, focused tool:

- the owner manages everything behind a login;
- guests only need a link;
- every reservation is final and visible to other guests, but hidden from the owner.

It was also built as a learning project to practise a full Flask workflow: database design, authentication, forms, templates, security basics, email, and publishing the code on GitHub.

## Features

**For the owner (requires an account)**

- Register, log in and log out.
- Create several events, each with a title and a date.
- Rename an event directly from its card, or delete it together with all of its gifts.
- Add gifts to an event with a title and an optional link to the shop.
- Edit or remove any gift.
- Get a unique share link for each event and copy it with one click.

**For guests (no account needed)**

- Open the shared link and see the event name, the date and the list of gifts.
- Follow the link to the product in a new tab.
- Press **Reserve** on a gift that is still free. A modal window appears and offers to send the gift details by email. The email is optional: a guest can reserve without leaving an address.
- Gifts that are already taken are clearly marked as reserved and cannot be taken twice.

## What was implemented

### 1. Data model

The database is SQLite, accessed through SQLAlchemy. The structure is a simple chain:

`User` → many `Event` → many `Item`

| Model | Main fields |
|-------|-------------|
| `User` | `id`, `name` (unique), `password_hash` |
| `Event` | `id`, `user_id`, `title`, `date`, `share_token` (unique, random) |
| `Item` | `id`, `event_id`, `title`, `link` (optional), `is_reserved` |

Relationships use `cascade="all, delete-orphan"`, so deleting an event removes its gifts, and deleting a user removes their events. Passwords are never stored in plain text: they are hashed with Werkzeug before saving.

### 2. Private links for guests

The share link does not contain a database id, because ids such as `/list/1`, `/list/2` are easy to guess. Each event gets a random token generated with `secrets.token_urlsafe(16)`, which has about 128 bits of randomness and cannot be brute-forced. If a token does not exist, the application returns a 404 page.

### 3. Authentication and access control

- **Flask-Login** keeps the user signed in between requests; owner pages are protected with `@login_required`.
- Every owner action looks up the record by both its id and the current user (for example, `Event.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()`), so one user cannot open, edit or delete another user's data by changing a number in the address bar.
- For gifts, ownership is checked through the parent event.

### 4. Forms and security

- Registration, login, new event and gift forms are built with **Flask-WTF** and rendered with Bootstrap-Flask.
- **CSRF protection** is enabled.
- Secrets (the Gmail address and app password) are read from environment variables loaded from a `.env` file that is excluded from Git.

### 5. Reserving a gift safely

When two guests press **Reserve** at almost the same moment, a simple "check, then save" approach could confirm both. The reservation is therefore a single conditional SQL update: it changes the row only if `is_reserved` is still false. The first guest wins, and the second one sees a message that the gift has already been taken.

The owner's own page deliberately does not show the reservation status, so the surprise is preserved.

### 6. Email notification

If a guest enters an address in the modal window, the application sends a short confirmation with the gift title and the link to the product. Emails are sent over SSL through Gmail SMTP using an app password and Python's `smtplib` with `EmailMessage`, which handles Ukrainian and other non-ASCII text correctly. If sending fails, the reservation is still saved and the guest sees a friendly message instead of an error.

### 7. Interface

The interface is built with Bootstrap 5 and a custom green theme with the Roboto Mono font. It includes responsive event cards, a gift table, a navigation bar with the menu split between left and right sides, a modal window for reserving, flash messages, and a landing page with an illustration. The layout adapts to phones and desktops.

## Project structure

```
wish_list/
├── main.py              # application, models, routes, email helper
├── forms.py             # Flask-WTF form classes
├── requirements.txt     # Python dependencies
├── .env                 # local secrets (not committed)
├── static/
│   └── people.jpg       # landing page illustration
├── templates/
│   ├── index.html       # base layout, event list, welcome page
│   ├── register.html
│   ├── login.html
│   ├── new_event.html
│   ├── edit_event.html
│   ├── add_gifts.html   # gifts of one event and the share link
│   ├── edit_gift.html
│   └── guest_list.html  # public page for guests
└── instance/
    └── wishlist.db      # SQLite database (not committed)
```

## Tech stack

- Python 3
- Flask
- Flask-SQLAlchemy and SQLite
- Flask-Login
- Flask-WTF (forms and CSRF protection)
- Bootstrap-Flask (Bootstrap 5)
- python-dotenv
- `smtplib` for email

## Getting started

1. Clone the repository and open the project folder.

2. Create and activate a virtual environment:

   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   ```

3. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:

   ```
   my_email = "your_address@gmail.com"
   app_password = "your16letterapppassword"
   ```

   Gmail does not accept the normal account password for SMTP. Turn on 2-Step Verification in your Google account, create an **app password**, and paste its 16 letters without spaces. Also set a long random `SECRET_KEY` for the application.

5. Run the application:

   ```
   python main.py
   ```

   Open the address printed in the console (for example `http://127.0.0.1:5002`). The database file is created in the `instance` folder on the first run.

## How to use

1. Register an account and log in.
2. Press **New Event**, enter a title and a date.
3. Open the event with **Gifts** and add a few items.
4. Press **Generate Link**, copy the address and send it to your guests.
5. Guests open the link, press **Reserve**, and optionally enter an email to receive the details.

## Challenges and lessons learned

- **Bootstrap versions.** Classes from the Bootstrap 6 documentation (such as `theme-success`) did nothing, because the application loads Bootstrap 5. Documentation must match the installed version.
- **Bootstrap JavaScript.** Components such as modal windows and collapse panels only work after `bootstrap.load_js()` is added to the base template.
- **Foreign keys in SQLite.** SQLite does not enforce foreign keys by default, so deleting a user directly in SQL left orphan events. Deleting through the ORM, with cascades, avoids this.
- **Gmail and app passwords.** The ordinary password is rejected, and port 465 requires `SMTP_SSL` rather than `SMTP` with `starttls`.
- **Post/Redirect/Get.** Redirecting after a successful form submit clears the fields and prevents duplicate submissions on refresh.

## Possible improvements

- Cancel a reservation (store a guest name or an anonymous token).
- Database migrations with Flask-Migrate.
- Deployment to a hosting service with a production server such as Gunicorn and a persistent database.
- Automated tests for the routes and the reservation logic.
- Interface language switching and a password reset by email.
