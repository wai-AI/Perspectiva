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

### Message Scheduling

Use the ```/start``` command to set up a new message. Specify the date, time, and content of the message (text, photo, video, or GIF). Confirm the details, and the bot will take care of the rest. If you want to cancel your actions, use the ```/cancel``` command.

You can schedule messages with or without media files. To schedule a message, after using the ```/start``` command, press the **"✍️Create Post"** button, then send the text of the message you want to send (but it should not contain special characters /$%^\[]+=`~<>|).

After this, if you want to attach a media file to the message, simply send it to the bot and it will be attached to the post. If you don't need a media file, press the **"Skip"** button.

After this step, you will need to enter the date in the format **"day month hour minute"** (e.g., 10 08 10 00 - which is August 10 at 10:00). The message publication time must be at least 1 minute later than the current time.

Finally, the bot will show you the message as it will be published in your chosen channel. If everything is satisfactory, press the **"✅All Correct"** button, and the publication will be successfully scheduled for your desired time. If something is not right, press **"❌Fill Out Again,"** and the entire process will start over.

At least, you can use ```/help``` command for reading documentation.

### Checking Scheduled Messages

If you want to check scheduled messages, press the **"📜Scheduled Messages"** button to view the list of messages you have scheduled and to be able to manipulate them. If something was scheduled incorrectly or by mistake, you will always be able to delete them before the publication time.

### Administrative Panel

The administrator can manage all bot settings using the ```/admin command.``` Capabilities include adding new users to manage the bot, removing unnecessary users, changing the channel for message publication, configuring all available media storage paths (photos/videos/GIFs), and restarting the server for remote updates.

## 👥 Contributing
A special thanks goes to the people who helped test this bot and find seemingly insignificant but critical bugs. And if you happen to find an error or have an idea on how to improve this bot, **don't hesitate to reach out!**

## 📋 License
This project is licensed under the MIT License - see the **[LICENSE](https://github.com/wai-AI/Perspectiva/blob/main/LICENSE)** file for details.
