import discord
from discord.ext import commands
import random
import sqlite3
import datetime
import asyncio
from typing import Optional

# ==========================================
# 🔧 التوكن والإعدادات
# ==========================================
TOKEN = "MTQ1NTU3MzM5ODExNjYzNDczMA.GB-lw3.1QR1CgWsS3aGtkcujBF6LoLLk8wtcPcU4FgsEE"
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ==========================================
# قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    
    # جدول الرصيد الأساسي
    c.execute('''
        CREATE TABLE IF NOT EXISTS economy (
            user_id TEXT,
            guild_id TEXT,
            balance INTEGER DEFAULT 0,
            bank INTEGER DEFAULT 0,
            daily_last TIMESTAMP,
            work_last TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )
    ''')
    
    # جدول المتجر
    c.execute('''
        CREATE TABLE IF NOT EXISTS shop (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            item_name TEXT,
            item_price INTEGER,
            item_description TEXT,
            role_id TEXT
        )
    ''')
    
    # جدول المخزون
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            user_id TEXT,
            guild_id TEXT,
            item_id INTEGER,
            quantity INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, guild_id, item_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ قاعدة البيانات جاهزة")

init_db()

# ==========================================
# دوال مساعدة
# ==========================================
def get_economy(user_id, guild_id):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT balance, bank FROM economy WHERE user_id = ? AND guild_id = ?", (str(user_id), str(guild_id)))
    row = c.fetchone()
    if row:
        result = {'balance': row[0], 'bank': row[1]}
    else:
        c.execute("INSERT INTO economy (user_id, guild_id, balance, bank) VALUES (?, ?, 0, 0)", (str(user_id), str(guild_id)))
        conn.commit()
        result = {'balance': 0, 'bank': 0}
    conn.close()
    return result

def update_economy(user_id, guild_id, balance=None, bank=None):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    if balance is not None:
        c.execute("UPDATE economy SET balance = ? WHERE user_id = ? AND guild_id = ?", (balance, str(user_id), str(guild_id)))
    if bank is not None:
        c.execute("UPDATE economy SET bank = ? WHERE user_id = ? AND guild_id = ?", (bank, str(user_id), str(guild_id)))
    conn.commit()
    conn.close()

def get_last_daily(user_id, guild_id):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT daily_last FROM economy WHERE user_id = ? AND guild_id = ?", (str(user_id), str(guild_id)))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_last_daily(user_id, guild_id):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("UPDATE economy SET daily_last = ? WHERE user_id = ? AND guild_id = ?", (datetime.datetime.now().isoformat(), str(user_id), str(guild_id)))
    conn.commit()
    conn.close()

def get_last_work(user_id, guild_id):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT work_last FROM economy WHERE user_id = ? AND guild_id = ?", (str(user_id), str(guild_id)))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_last_work(user_id, guild_id):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("UPDATE economy SET work_last = ? WHERE user_id = ? AND guild_id = ?", (datetime.datetime.now().isoformat(), str(user_id), str(guild_id)))
    conn.commit()
    conn.close()

# ==========================================
# أحداث البوت
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} متصل!")
    print(f"📊 في {len(bot.guilds)} سيرفر")
    try:
        synced = await bot.tree.sync()
        print(f"✅ تم تسجيل {len(synced)} أمر سلاش")
    except Exception as e:
        print(f"❌ فشل مزامنة الأوامر: {e}")

# ==========================================
# أوامر البنك (سلاش)
# ==========================================

# 1️⃣ عرض الرصيد
@bot.tree.command(name="رصيد", description="💰 عرض رصيدك الحالي")
async def balance(interaction: discord.Interaction, عضو: Optional[discord.Member] = None):
    target = عضو or interaction.user
    eco = get_economy(target.id, interaction.guild.id)
    
    embed = discord.Embed(
        title=f"💰 رصيد {target.name}",
        description=f"**الرصيد:** `{eco['balance']}` نقطة\n**البنك:** `{eco['bank']}` نقطة\n**الإجمالي:** `{eco['balance'] + eco['bank']}` نقطة",
        color=0xFFD700
    )
    await interaction.response.send_message(embed=embed)

# 2️⃣ راتب يومي
@bot.tree.command(name="راتب", description="📅 احصل على راتبك اليومي")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    guild_id = interaction.guild.id
    
    last_daily = get_last_daily(user_id, guild_id)
    now = datetime.datetime.now()
    
    if last_daily:
        last = datetime.datetime.fromisoformat(last_daily)
        if (now - last).days < 1:
            next_time = last + datetime.timedelta(days=1)
            remaining = next_time - now
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            await interaction.response.send_message(f"❌ انتظر {hours} ساعة و {minutes} دقيقة للمكافأة التالية")
            return
    
    eco = get_economy(user_id, guild_id)
    reward = random.randint(500, 1000)
    update_economy(user_id, guild_id, balance=eco['balance'] + reward)
    set_last_daily(user_id, guild_id)
    
    embed = discord.Embed(
        title="📅 **الراتب اليومي**",
        description=f"✅ حصلت على **{reward}** نقطة\n💰 رصيدك الحالي: `{eco['balance'] + reward}` نقطة",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

# 3️⃣ تحويل نقاط
@bot.tree.command(name="تحويل", description="💸 تحويل نقاط لعضو آخر")
async def transfer(interaction: discord.Interaction, عضو: discord.Member, المبلغ: int):
    if المبلغ <= 0:
        await interaction.response.send_message("❌ المبلغ يجب أن يكون أكبر من 0", ephemeral=True)
        return
    
    if عضو.id == interaction.user.id:
        await interaction.response.send_message("❌ لا يمكنك التحويل لنفسك", ephemeral=True)
        return
    
    sender = get_economy(interaction.user.id, interaction.guild.id)
    if sender['balance'] < المبلغ:
        await interaction.response.send_message(f"❌ رصيدك غير كافٍ! لديك {sender['balance']} نقطة فقط", ephemeral=True)
        return
    
    receiver = get_economy(عضو.id, interaction.guild.id)
    update_economy(interaction.user.id, interaction.guild.id, balance=sender['balance'] - المبلغ)
    update_economy(عضو.id, interaction.guild.id, balance=receiver['balance'] + المبلغ)
    
    embed = discord.Embed(
        title="💸 **تحويل نقاط**",
        description=f"✅ تم تحويل **{المبلغ}** نقطة إلى {عضو.mention}\n💰 رصيدك الآن: `{sender['balance'] - المبلغ}` نقطة",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

# 4️⃣ إيداع في البنك
@bot.tree.command(name="ايداع", description="🏦 إيداع نقاط في البنك")
async def deposit(interaction: discord.Interaction, المبلغ: int):
    eco = get_economy(interaction.user.id, interaction.guild.id)
    
    if المبلغ == -1:
        المبلغ = eco['balance']
    
    if المبلغ <= 0:
        await interaction.response.send_message("❌ المبلغ يجب أن يكون أكبر من 0", ephemeral=True)
        return
    
    if eco['balance'] < المبلغ:
        await interaction.response.send_message(f"❌ رصيدك غير كافٍ! لديك {eco['balance']} نقطة فقط", ephemeral=True)
        return
    
    update_economy(interaction.user.id, interaction.guild.id, balance=eco['balance'] - المبلغ, bank=eco['bank'] + المبلغ)
    
    embed = discord.Embed(
        title="🏦 **إيداع في البنك**",
        description=f"✅ تم إيداع **{المبلغ}** نقطة في البنك\n💰 رصيدك: `{eco['balance'] - المبلغ}` نقطة\n🏦 رصيد البنك: `{eco['bank'] + المبلغ}` نقطة",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

# 5️⃣ سحب من البنك
@bot.tree.command(name="سحب", description="🏦 سحب نقاط من البنك")
async def withdraw(interaction: discord.Interaction, المبلغ: int):
    eco = get_economy(interaction.user.id, interaction.guild.id)
    
    if المبلغ == -1:
        المبلغ = eco['bank']
    
    if المبلغ <= 0:
        await interaction.response.send_message("❌ المبلغ يجب أن يكون أكبر من 0", ephemeral=True)
        return
    
    if eco['bank'] < المبلغ:
        await interaction.response.send_message(f"❌ رصيد البنك غير كافٍ! لديك {eco['bank']} نقطة فقط", ephemeral=True)
        return
    
    update_economy(interaction.user.id, interaction.guild.id, balance=eco['balance'] + المبلغ, bank=eco['bank'] - المبلغ)
    
    embed = discord.Embed(
        title="🏦 **سحب من البنك**",
        description=f"✅ تم سحب **{المبلغ}** نقطة من البنك\n💰 رصيدك: `{eco['balance'] + المبلغ}` نقطة\n🏦 رصيد البنك: `{eco['bank'] - المبلغ}` نقطة",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

# 6️⃣ العمل (شغل، صيد، تعدين)
work_jobs = [
    {"name": "مبرمج", "min": 80, "max": 150},
    {"name": "مصمم جرافيك", "min": 70, "max": 120},
    {"name": "صياد سمك", "min": 50, "max": 100},
    {"name": "تاجر أسماك", "min": 60, "max": 110},
    {"name": "عامل منجم", "min": 90, "max": 160},
    {"name": "سائق شاحنة", "min": 70, "max": 130}
]

@bot.tree.command(name="شغل", description="💼 اعمل وكسب نقاط")
async def work(interaction: discord.Interaction):
    user_id = interaction.user.id
    guild_id = interaction.guild.id
    
    last_work = get_last_work(user_id, guild_id)
    now = datetime.datetime.now()
    
    if last_work:
        last = datetime.datetime.fromisoformat(last_work)
        if (now - last).seconds < 3600:  # مرة كل ساعة
            remaining = 3600 - (now - last).seconds
            minutes = remaining // 60
            seconds = remaining % 60
            await interaction.response.send_message(f"❌ انتظر {minutes} دقيقة و {seconds} ثانية للعمل مرة أخرى")
            return
    
    job = random.choice(work_jobs)
    earning = random.randint(job["min"], job["max"])
    
    eco = get_economy(user_id, guild_id)
    update_economy(user_id, guild_id, balance=eco['balance'] + earning)
    set_last_work(user_id, guild_id)
    
    embed = discord.Embed(
        title="💼 **العمل**",
        description=f"✅ عملت كـ **{job['name']}** وحصلت على **{earning}** نقطة\n💰 رصيدك الحالي: `{eco['balance'] + earning}` نقطة",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

# 7️⃣ توب (قائمة الأغنياء)
@bot.tree.command(name="توب", description="🏆 قائمة أغنى الأعضاء")
async def top(interaction: discord.Interaction):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT user_id, balance, bank FROM economy WHERE guild_id = ? ORDER BY (balance + bank) DESC LIMIT 10", (str(interaction.guild.id),))
    rows = c.fetchall()
    conn.close()
    
    embed = discord.Embed(title="🏆 **أغنى الأعضاء**", color=0xFFD700)
    description = ""
    for i, (user_id, balance, bank) in enumerate(rows, 1):
        user = bot.get_user(int(user_id))
        total = balance + bank
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        description += f"{medal} {user.mention if user else 'غير معروف'} – `{total}` نقطة\n"
    
    if not description:
        description = "لا توجد بيانات كافية"
    
    embed.description = description
    await interaction.response.send_message(embed=embed)

# 8️⃣ إضافة عنصر للمتجر (للأدمن)
@bot.tree.command(name="اضف_عنصر", description="🛒 إضافة عنصر للمتجر (للأدمن)")
@app_commands.default_permissions(administrator=True)
async def add_shop_item(interaction: discord.Interaction, الاسم: str, السعر: int, الوصف: str, الرتبة: Optional[discord.Role] = None):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    role_id = str(الرتبة.id) if الرتبة else None
    c.execute("INSERT INTO shop (guild_id, item_name, item_price, item_description, role_id) VALUES (?, ?, ?, ?, ?)",
              (str(interaction.guild.id), الاسم, السعر, الوصف, role_id))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(f"✅ تمت إضافة **{الاسم}** إلى المتجر بسعر `{السعر}` نقطة", ephemeral=True)

# 9️⃣ عرض المتجر
@bot.tree.command(name="متجر", description="🛒 عرض عناصر المتجر")
async def shop(interaction: discord.Interaction):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT id, item_name, item_price, item_description FROM shop WHERE guild_id = ?", (str(interaction.guild.id),))
    items = c.fetchall()
    conn.close()
    
    embed = discord.Embed(title="🛒 **المتجر**", color=0xFFD700)
    
    if not items:
        embed.description = "لا توجد عناصر في المتجر حالياً"
    else:
        for item_id, name, price, desc in items:
            embed.add_field(name=f"{name} - {price} نقطة", value=desc, inline=False)
    
    await interaction.response.send_message(embed=embed)

# 🔟 شراء عنصر من المتجر
@bot.tree.command(name="شراء", description="🛍️ شراء عنصر من المتجر")
async def buy(interaction: discord.Interaction, العنصر: str):
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("SELECT id, item_price, role_id FROM shop WHERE guild_id = ? AND item_name = ?", (str(interaction.guild.id), العنصر))
    item = c.fetchone()
    conn.close()
    
    if not item:
        await interaction.response.send_message(f"❌ العنصر `{العنصر}` غير موجود في المتجر", ephemeral=True)
        return
    
    item_id, price, role_id = item
    eco = get_economy(interaction.user.id, interaction.guild.id)
    
    if eco['balance'] < price:
        await interaction.response.send_message(f"❌ رصيدك غير كافٍ! تحتاج `{price}` نقطة", ephemeral=True)
        return
    
    # خصم النقاط
    update_economy(interaction.user.id, interaction.guild.id, balance=eco['balance'] - price)
    
    # إضافة الرتبة إذا كانت موجودة
    if role_id:
        role = interaction.guild.get_role(int(role_id))
        if role:
            await interaction.user.add_roles(role)
    
    # إضافة للمخزون
    conn = sqlite3.connect('bank.db')
    c = conn.cursor()
    c.execute("INSERT INTO inventory (user_id, guild_id, item_id) VALUES (?, ?, ?) ON CONFLICT(user_id, guild_id, item_id) DO UPDATE SET quantity = quantity + 1",
              (str(interaction.user.id), str(interaction.guild.id), item_id))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(
        title="🛍️ **شراء ناجح**",
        description=f"✅ تم شراء **{العنصر}** بـ `{price}` نقطة\n💰 رصيدك المتبقي: `{eco['balance'] - price}` نقطة",
        color=0x00FF00
    )
    await interaction.response.send_message(embed=embed)

# 1️⃣1️⃣ هدية (إرسال نقاط مع رسالة)
@bot.tree.command(name="هدية", description="🎁 إرسال هدية مالية مع رسالة")
async def gift(interaction: discord.Interaction, عضو: discord.Member, المبلغ: int, رسالة: str = "🎁 هدية مني لك!"):
    if المبلغ <= 0:
        await interaction.response.send_message("❌ المبلغ يجب أن يكون أكبر من 0", ephemeral=True)
        return
    
    if عضو.id == interaction.user.id:
        await interaction.response.send_message("❌ لا يمكنك إرسال هدية لنفسك", ephemeral=True)
        return
    
    sender = get_economy(interaction.user.id, interaction.guild.id)
    if sender['balance'] < المبلغ:
        await interaction.response.send_message(f"❌ رصيدك غير كافٍ! لديك {sender['balance']} نقطة فقط", ephemeral=True)
        return
    
    receiver = get_economy(عضو.id, interaction.guild.id)
    update_economy(interaction.user.id, interaction.guild.id, balance=sender['balance'] - المبلغ)
    update_economy(عضو.id, interaction.guild.id, balance=receiver['balance'] + المبلغ)
    
    embed = discord.Embed(
        title="🎁 **هدية**",
        description=f"{interaction.user.mention} أرسل هدية إلى {عضو.mention}\n**المبلغ:** `{المبلغ}` نقطة\n**الرسالة:** {رسالة}",
        color=0xFF69B4
    )
    await interaction.response.send_message(embed=embed)

# ==========================================
# تشغيل البوت
# ==========================================
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ خطأ: {e}")
