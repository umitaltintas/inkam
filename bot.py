import logging
import os
import uuid
from dotenv import load_dotenv
from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters,ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

expenses = {}
category_limits = {}
EXPENSE_AMOUNT, EXPENSE_CATEGORY, EXPENSE_DESCRIPTION, EXPENSE_FREQUENCY = range(4)
LIMIT_CATEGORY, LIMIT_AMOUNT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} started the bot")
    keyboard = [
        ['/add', '/addrecurring'],
        ['/delete', '/total'],
        ['/category', '/month'],
        ['/report', '/setlimit'],
        ['/limits', '/clear'],
        ['/help']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Expense Tracker Bot!", reply_markup=reply_markup)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} requested help")
    help_text = "Available commands:\n" \
                "/add <amount> <category> <description> - Add an expense\n" \
                "/addrecurring <amount> <category> <description> <frequency> - Add a recurring expense\n" \
                "/delete <expense_id> - Delete an expense\n" \
                "/total - Get total of all expenses\n" \
                "/category <category> - View expenses for a specific category\n" \
                "/month <month> <year> - View expenses for a specific month\n" \
                "/clear - Clear all expenses\n" \
                "/report - Generate a monthly expense report\n" \
                "/setlimit <category> <limit> - Set a limit for a category\n" \
                "/limits - View current limits for each category"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)
async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the expense amount:")
    return EXPENSE_AMOUNT

async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = float(update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the expense category:")
    return EXPENSE_CATEGORY

async def add_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the expense description:")
    return EXPENSE_DESCRIPTION

async def add_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    amount = context.user_data['amount']
    category = context.user_data['category']
    expense_id = str(uuid.uuid4())
    expense = (expense_id, amount, category, description, datetime.now().strftime("%Y-%m"))
    if update.effective_user.id not in expenses:
        expenses[update.effective_user.id] = []
    expenses[update.effective_user.id].append(expense)
    logger.info(f"User {update.effective_user.id} added an expense: {expense}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Expense of {amount} for {description} in category {category} added.")
    if category in category_limits and amount > category_limits[category]:
        logger.warning(f"User {update.effective_user.id} exceeded the limit for category {category}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Warning: Expense exceeds the limit for category {category}!")
    return ConversationHandler.END

async def add_recurring_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the recurring expense amount:")
    return EXPENSE_AMOUNT

async def add_recurring_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = float(update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the recurring expense category:")
    return EXPENSE_CATEGORY

async def add_recurring_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the recurring expense description:")
    return EXPENSE_DESCRIPTION

async def add_recurring_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the recurring expense frequency:")
    return EXPENSE_FREQUENCY

async def add_recurring_expense_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frequency = update.message.text
    amount = context.user_data['amount']
    category = context.user_data['category']
    description = context.user_data['description']
    expense_id = str(uuid.uuid4())
    expense = (expense_id, amount, category, description, datetime.now().strftime("%Y-%m"), frequency)
    if update.effective_user.id not in expenses:
        expenses[update.effective_user.id] = []
    expenses[update.effective_user.id].append(expense)
    logger.info(f"User {update.effective_user.id} added a recurring expense: {expense}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Recurring expense of {amount} for {description} in category {category} added with frequency {frequency}.")
    return ConversationHandler.END

async def set_limit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the category for the limit:")
    return LIMIT_CATEGORY

async def set_limit_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the limit amount:")
    return LIMIT_AMOUNT

async def set_limit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = context.user_data['category']
    limit = float(update.message.text)
    category_limits[category] = limit
    logger.info(f"User {update.effective_user.id} set a limit of {limit} for category {category}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Limit for category {category} set to {limit}.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Operation cancelled.")
    return ConversationHandler.END
async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        category = context.args[1]
        description = ' '.join(context.args[2:])

        expense_id = str(uuid.uuid4())
        expense = (expense_id, amount, category, description, datetime.now().strftime("%Y-%m"))
        
        if update.effective_user.id not in expenses:
            expenses[update.effective_user.id] = []
        expenses[update.effective_user.id].append(expense)
        
        logger.info(f"User {update.effective_user.id} added an expense: {expense}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Expense of {amount} for {description} in category {category} added.")

        if category in category_limits and amount > category_limits[category]:
            logger.warning(f"User {update.effective_user.id} exceeded the limit for category {category}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Warning: Expense exceeds the limit for category {category}!")

    except (IndexError, ValueError):
        logger.error(f"User {update.effective_user.id} provided invalid arguments for /add command")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command format. Use /add <amount> <category> <description>")

async def add_recurring_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(context.args[0])
        category = context.args[1]
        description = ' '.join(context.args[2:-1])
        frequency = context.args[-1]

        expense_id = str(uuid.uuid4())
        expense = (expense_id, amount, category, description, datetime.now().strftime("%Y-%m"), frequency)
        
        if update.effective_user.id not in expenses:
            expenses[update.effective_user.id] = []
        expenses[update.effective_user.id].append(expense)
        
        logger.info(f"User {update.effective_user.id} added a recurring expense: {expense}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Recurring expense of {amount} for {description} in category {category} added with frequency {frequency}.")

    except (IndexError, ValueError):
        logger.error(f"User {update.effective_user.id} provided invalid arguments for /addrecurring command")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command format. Use /addrecurring <amount> <category> <description> <frequency>")

async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        expense_id = context.args[0]
        user_id = update.effective_user.id
        
        if user_id in expenses:
            for expense in expenses[user_id]:
                if expense[0] == expense_id:
                    expenses[user_id].remove(expense)
                    logger.info(f"User {user_id} deleted expense: {expense}")
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Expense with ID {expense_id} deleted.")
                    return
            
            logger.warning(f"User {user_id} tried to delete non-existent expense with ID {expense_id}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Expense with ID {expense_id} not found.")
        else:
            logger.warning(f"User {user_id} tried to delete expense but has no recorded expenses")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no recorded expenses.")

    except IndexError:
        logger.error(f"User {update.effective_user.id} provided invalid arguments for /delete command")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command format. Use /delete <expense_id>")

async def view_category_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        category = context.args[0]
        user_id = update.effective_user.id
        
        if user_id in expenses:
            category_expenses = [expense for expense in expenses[user_id] if expense[2] == category]
            
            if category_expenses:
                report = f"Expenses for category {category}:\n\n"
                for expense in category_expenses:
                    report += f"ID: {expense[0]}, Amount: {expense[1]}, Description: {expense[3]}\n"
                logger.info(f"User {user_id} viewed expenses for category {category}")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=report)
            else:
                logger.info(f"User {user_id} tried to view expenses for category {category} but none found")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"No expenses found for category {category}.")
        else:
            logger.warning(f"User {user_id} tried to view category expenses but has no recorded expenses")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no recorded expenses.")

    except IndexError:
        logger.error(f"User {update.effective_user.id} provided invalid arguments for /category command")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command format. Use /category <category>")

async def view_month_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        month = int(context.args[0])
        year = int(context.args[1])
        user_id = update.effective_user.id
        
        if user_id in expenses:
            month_expenses = [expense for expense in expenses[user_id] if expense[4] == f"{year}-{month:02d}"]
            if month_expenses:
                report = f"Expenses for {year}-{month:02d}:\n\n"
                for expense in month_expenses:
                    report += f"ID: {expense[0]}, Amount: {expense[1]}, Category: {expense[2]}, Description: {expense[3]}\n"
                logger.info(f"User {user_id} viewed expenses for month {year}-{month:02d}")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=report)
            else:
                logger.info(f"User {user_id} tried to view expenses for month {year}-{month:02d} but none found")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"No expenses found for {year}-{month:02d}.")
        else:
            logger.warning(f"User {user_id} tried to view month expenses but has no recorded expenses")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no recorded expenses.")

    except (IndexError, ValueError):
        logger.error(f"User {update.effective_user.id} provided invalid arguments for /month command")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command format. Use /month <month> <year>")

async def total_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in expenses:
        total = sum(expense[1] for expense in expenses[user_id])
        logger.info(f"User {user_id} viewed total expenses: {total}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your total expenses: {total}")
    else:
        logger.warning(f"User {user_id} tried to view total expenses but has no recorded expenses")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no recorded expenses.")

async def clear_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in expenses:
        expenses[user_id] = []
        logger.info(f"User {user_id} cleared all expenses")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="All expenses cleared.")
    else:
        logger.warning(f"User {user_id} tried to clear expenses but has no recorded expenses")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no recorded expenses.")     

async def generate_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in expenses:
        report = "Monthly Expense Report:\n\n"
        monthly_expenses = {}
        for expense in expenses[user_id]:
            month = expense[4]
            if month not in monthly_expenses:
                monthly_expenses[month] = []
            monthly_expenses[month].append(expense)

        for month, month_expenses in monthly_expenses.items():
            report += f"Month: {month}\n"
            category_totals = {}
            for expense in month_expenses:
                category = expense[2]
                if category not in category_totals:
                    category_totals[category] = 0
                category_totals[category] += expense[1]
            
            for category, total in category_totals.items():
                report += f"{category}: {total}\n"
            report += "\n"
        
        logger.info(f"User {user_id} generated an expense report")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=report)
    else:
        logger.warning(f"User {user_id} tried to generate a report but has no recorded expenses")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You have no recorded expenses.")

async def set_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        category = context.args[0]
        limit = float(context.args[1])
        category_limits[category] = limit
        logger.info(f"User {update.effective_user.id} set a limit of {limit} for category {category}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Limit for category {category} set to {limit}.")
    except (IndexError, ValueError):
        logger.error(f"User {update.effective_user.id} provided invalid arguments for /setlimit command")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid command format. Use /setlimit <category> <limit>")

async def view_limits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if category_limits:
        limits_text = "Current category limits:\n"
        for category, limit in category_limits.items():
            limits_text += f"{category}: {limit}\n"
        logger.info(f"User {update.effective_user.id} viewed category limits")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=limits_text)
    else:
        logger.info(f"User {update.effective_user.id} tried to view category limits but none are set")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="No category limits set.")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.warning(f"User {update.effective_user.id} sent an unknown command")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command. Use /help to see available commands.")

if __name__ == '__main__':
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable not set.")

    application = ApplicationBuilder().token(bot_token).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    add_expense_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_expense_start)],
        states={
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_amount)],
            EXPENSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_category)],
            EXPENSE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_description)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(add_expense_conv_handler)

    add_recurring_expense_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addrecurring', add_recurring_expense_start)],
        states={
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_recurring_expense_amount)],
            EXPENSE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_recurring_expense_category)],
            EXPENSE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_recurring_expense_description)],
            EXPENSE_FREQUENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_recurring_expense_frequency)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(add_recurring_expense_conv_handler)

    set_limit_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setlimit', set_limit_start)],
        states={
            LIMIT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_limit_category)],
            LIMIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_limit_amount)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(set_limit_conv_handler)
  


    delete_expense_handler = CommandHandler('delete', delete_expense)
    application.add_handler(delete_expense_handler)

    category_expenses_handler = CommandHandler('category', view_category_expenses)
    application.add_handler(category_expenses_handler)

    month_expenses_handler = CommandHandler('month', view_month_expenses)
    application.add_handler(month_expenses_handler)

    total_expenses_handler = CommandHandler('total', total_expenses)
    application.add_handler(total_expenses_handler)

    clear_expenses_handler = CommandHandler('clear', clear_expenses)
    application.add_handler(clear_expenses_handler)

    report_handler = CommandHandler('report', generate_report) 
    application.add_handler(report_handler)

    set_limit_handler = CommandHandler('setlimit', set_limit)
    application.add_handler(set_limit_handler)

    view_limits_handler = CommandHandler('limits', view_limits)  
    application.add_handler(view_limits_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    logger.info("Expense Tracker Bot started")
    application.run_polling()