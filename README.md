# Perspectiva sender bot

## ✅ Introduction

This bot allows you to schedule the sending of messages, photos, videos, and GIFs to Telegram channels. It also includes an admin panel for managing schedules and users.

## 🎯 Features
**Schedule Messages:** Easily schedule text messages, photos, videos, and GIFs to be sent to your Telegram channels.

**Admin Panel:** Manage scheduled messages and user permissions from an intuitive admin interface.

**Support for Multiple Media Types:** Send text, images, videos, and GIFs at scheduled times.

**User Permissions:** Control which users are allowed to schedule messages.

## 🛠 Installation

**First step: Clone the Repository**

```
git clone https://github.com/wai-AI/Perspectiva.git
cd Perspectiva 
```

**Second step: Create a Virtual Environment**

```
python -m venv venv
.\venv\Scripts\Activate.ps1 #On Linux use: source venv/bin/activate   
```

**Third step: Install Required Packages**

```
pip install -r requirements.txt
```

**Fourth step: Create a Configuration File**

Create a .json file in the root of your project with the following labels:

```
{
    "TOKEN": "your token",
    "CHANNEL_ID": "your channel id",
    "ALLOWED_USERS": [your users],
    "PATH_TO_PHOTO": "your path to photo",
    "PATH_TO_VIDEO": "your path to video",
    "PATH_TO_GIF": "your path to git",
    "ADMIN_USER": [your id]
}
```

**Fifth step: Set Up Auto-Running Script**

On this project I was using a .bat file, but if you are using Linux - you can write same script on .bash language.

Add this script to the shell:startup :

```
Press Win + R, type shell:startup, and hit Enter.
Copy the .bat script into this folder.
```

## 👣 Usage

### Schedule Messages
Use the /start command to set up a new message.
Specify the date, time, and content (text, photo, video, GIF) of the message.
Confirm the details, and the bot will take care of the rest.

### Admin Panel
The admin can manage all bot`s settings using the /admin command.
Features include editing, rescheduling, or canceling existing messages.
Admin can also manage user permissions, adding or removing users from the ALLOWED_USERS list.

## 👥 Contributing
Feel free to submit issues or pull requests. **Contributions are welcome!**

## 📋 License
This project is licensed under the MIT License - see the LICENSE file for details.
