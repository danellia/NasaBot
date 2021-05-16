import requests
import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

def start(update: Update, _: CallbackContext) -> None:
  update.message.reply_text("hi! this bot will send you nasa's picture of the day. \n\nsend the time you want to receive messages at daily using /set <hh:mm>\n\nor /unset to cancel notifications")

def alarm(context: CallbackContext) -> None:
  job = context.job
  response = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY")
  responseJson = response.json()
  photo = responseJson["hdurl"]
  name = responseJson["title"]
  explanation = responseJson["explanation"]
  try:
    author = responseJson["copyright"]
    photoInfo = name + " by " + author + "\n\n" + explanation
  except KeyError:
    photoInfo = name + "\n\n" + explanation
  context.bot.send_photo(job.context, photo)
  context.bot.send_message(job.context, photoInfo)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
  current_jobs = context.job_queue.get_jobs_by_name(name)
  if not current_jobs:
    return False
  for job in current_jobs:
    job.schedule_removal()
  return True


def set_notification(update: Update, context: CallbackContext) -> None:
  chat_id = update.message.chat_id
  try:
    time_str = context.args[0]
    daily_at = datetime.datetime.combine(datetime.datetime.today().date(), datetime.time.fromisoformat(time_str))
    hour_to_utc = daily_at.hour - 7
    daily_at_utc = daily_at.replace(hour = hour_to_utc)
    now = datetime.datetime.now()
    daily_at_utc_sec = (daily_at_utc - now).total_seconds()
    day = 24 * 60 * 60
    #print(time_str, daily_at_utc.day, daily_at_utc.hour, daily_at_utc.minute, daily_at_utc.second, daily_at_utc.microsecond, daily_at_utc.tzinfo, daily_at_utc_sec)

    job_removed = remove_job_if_exists(str(chat_id), context)
    context.job_queue.run_repeating(alarm, day, daily_at_utc_sec, context = chat_id, name = str(chat_id))

    text = 'notifications successfully set!'
    if job_removed:
      text += ' old one was removed.'
    update.message.reply_text(text)

  except (IndexError, ValueError):
    update.message.reply_text('hey! /set <hh:mm>')

def unset(update: Update, context: CallbackContext) -> None:
  chat_id = update.message.chat_id
  job_removed = remove_job_if_exists(str(chat_id), context)
  text = 'notifications successfully cancelled!' if job_removed else 'you have no active notifs.'
  update.message.reply_text(text)


def main() -> None:
  updater = Updater("TOKEN")
  dispatcher = updater.dispatcher

  dispatcher.add_handler(CommandHandler("start", start))
  dispatcher.add_handler(CommandHandler("help", start))
  dispatcher.add_handler(CommandHandler("set", set_notification))
  dispatcher.add_handler(CommandHandler("unset", unset))

  updater.start_polling()
  updater.idle()

if __name__ == '__main__':
  main()
