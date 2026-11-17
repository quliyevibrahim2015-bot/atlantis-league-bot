import discord
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timedelta, timezone

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

oyuncu_degerleri = {}
antrenman_ilerleme = {}
kayit_verileri = {}      
gunluk_mesajlar = {}     
toplam_mesajlar = {}     
uyari_verileri = {}      
dondurmaci_kanallari = set()
MAX_DEGER = 450.0
OWNERS = [1568617072882221190, 1540463718394237071]

ANTRENMAN_KANAL_ID = 1570104333259903026
PENALTI_KANAL_ID = 1570104347159953498

# Temel Roller ve Kanallar
ROL_KAYITSIZ = 1569926489665970246
ROL_FUTBOLCU = 1569992725401571329
ROL_TD = 1569926286787223563
ROL_BASKAN = 1571518620750577704
ROL_KAYIT_YETKILISI = 1569926201395511336
KANAL_KAYIT_SOHBET = 1571395577818779678
KANAL_CHAT = 1570104698558615562

# Bildirim Rol ID-leri
ROL_ETKINLIK = 1570018818338726028
ROL_TURNUVA = 1571147749846683771
ROL_HABER = 1570021720046178304
ROL_GUNCELLEME = 1570024617240956961
ROL_MAC = 1570013023341387856

def yetkili_mi(ctx):
    return ctx.author.id in OWNERS or ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_messages

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    uid = message.author.id
    toplam_mesajlar[uid] = toplam_mesajlar.get(uid, 0) + 1
    gunluk_mesajlar[uid] = gunluk_mesajlar.get(uid, 0) + 1
    await bot.process_commands(message)

@tasks.loop(hours=24)
async def gunluk_mesaj_sifirla():
    gunluk_mesajlar.clear()

@gunluk_mesaj_sifirla.before_loop
async def before_gunluk_sifirla():
    now = datetime.now()
    target = datetime(now.year, now.month, now.day) + timedelta(days=1)
    diff = (target - now).total_seconds()
    await asyncio.sleep(diff)
class DondurmaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=15)
        self.yenildi = False

    @discord.ui.button(label="Dondurmayi Ye!", style=discord.ButtonStyle.success, emoji="<a:LL_icecream:1571372896402546758>", custom_id="dondurma_yi_btn")
    async def dondurma_yi(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.yenildi:
            return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Bu dondurma çoktan yenildi!", ephemeral=True)
        self.yenildi = True
        for item in self.children: item.disabled = True
        embed = discord.Embed(title="<a:ATLS_pepe:1571131663788937326> Dondurma Yenildi!", description=f"<a:dogru:1571567011224617081> İlk kapıp **{interaction.user.mention}** yedi! Afiyet olsun!", color=discord.Color.green())
        embed.set_footer(text="Atlantis League • Dondurmacı Sistemi")
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"<a:ATLS_rocket:1571132526511132763> Tebrikler, dondurmayı kaptın!", ephemeral=True)
        self.stop()

    async def on_timeout(self):
        if not self.yenildi:
            for item in self.children: item.disabled = True
            try:
                embed = discord.Embed(title="<a:ATLS_yanlis:1571131131657584712> Dondurma Eridi / Gitti!", description="15 saniye içinde kimse yiyemediği için dondurmacı gitti...", color=discord.Color.red())
                await self.message.edit(embed=embed, view=self)
            except: pass

@tasks.loop(minutes=10)
async def dondurmaci_dongusu():
    for kanal_id in list(dondurmaci_kanallari):
        kanal = bot.get_channel(kanal_id)
        if kanal:
            try:
                embed = discord.Embed(title="<a:LL_icecream:1571372896402546758> Dondurmacı Geldi!", description="Sokaktan taze dondurma geldi! <a:ATLS_rocket:1571132526511132763>\n\n<a:hedef:1571436272881508442> **15 saniyen var!**", color=discord.Color.gold())
                view = DondurmaView()
                msg = await kanal.send(embed=embed, view=view)
                view.message = msg
            except: pass

@bot.command(name="dondurmaciac")
async def dondurmaciac(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Bu komutu kullanmak için Administrator yetkin olmalı!", ephemeral=True)
    dondurmaci_kanallari.add(ctx.channel.id)
    await ctx.send(f"<a:dogru:1571567011224617081> Bu kanal ({ctx.channel.mention}) dondurmacı listesine eklendi!")

@bot.command(name="dondurmacikapat")
async def dondurmacikapat(ctx):
    if not ctx.author.guild_permissions.administrator:
        return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Bu komutu kullanmak için Administrator yetkin olmalı!", ephemeral=True)
    if ctx.channel.id in dondurmaci_kanallari:
        dondurmaci_kanallari.remove(ctx.channel.id)
        await ctx.send(f"<a:ATLS_yanlis:1571131131657584712> Bu kanal ({ctx.channel.mention}) dondurmacı listesinden çıkarıldı.")
    else:
        await ctx.send("<a:ATLS_yanlis:1571131131657584712> Bu kanal zaten dondurmacı listesinde ekli değil!")

class RolSecimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="Bildirim rollerini seçmek veya kaldırmak için tıkla...",
        min_values=1, max_values=1,
        options=[
            discord.SelectOption(label="Etkinlik Bildirim", description="Çekiliş ve etkinliklerden haberdar ol", emoji="<a:ATLS_dansedenmaymun:1571133976612049056>", value="etkinlik"),
            discord.SelectOption(label="Turnuva Bildirim", description="Turnuva duyurularını kaçırma", emoji="<a:lorex_futboltopu:1571500016382644274>", value="turnuva"),
            discord.SelectOption(label="Haber Bildirimi", description="Ligden güncel haberleri takip et", emoji="<a:bilgi:1571085351164842054>", value="haber"),
            discord.SelectOption(label="Güncelleme Bildirimi", description="Bot ve sistem yeniliklerinden haberdar ol", emoji="<a:ATLS_rocket:1571132526511132763>", value="guncelleme"),
            discord.SelectOption(label="Maç Bildirimi", description="Maç yayınları ve saatlerini kaçırma", emoji="<a:lorex_futboltopu:1571500016382644274>", value="mac")
        ],
        custom_id="persistent_rol_select"
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        role_map = {"etkinlik": ROL_ETKINLIK, "turnuva": ROL_TURNUVA, "haber": ROL_HABER, "guncelleme": ROL_GUNCELLEME, "mac": ROL_MAC}
        role = interaction.guild.get_role(role_map.get(select.values[0]))
        if not role: return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Rol sunucuda bulunamadı!", ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"<a:ATLS_yanlis:1571131131657584712> Başarıyla **{role.name}** üzerinizden alındı!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"<a:dogru:1571567011224617081> Başarıyla **{role.name}** tarafınıza verildi!", ephemeral=True)

class HosGeldinButonlari(discord.ui.View):
    def __init__(self, yeni_uye: discord.Member):
        super().__init__(timeout=None)
        self.yeni_uye = yeni_uye
        self.ustlenen = None

    @discord.ui.button(label="Üstlen", style=discord.ButtonStyle.secondary, emoji="<a:ATLS_yetkili:1571131803773968444>")
    async def ustlen_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        yetkili_rol = interaction.guild.get_role(ROL_KAYIT_YETKILISI)
        if yetkili_rol not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Bu kaydı sadece Kayıt Yetkilileri üstlenebilir!", ephemeral=True)

        if self.ustlenen:
            return await interaction.response.send_message(f"<a:ATLS_yanlis:1571131131657584712> Bu kayıt zaten {self.ustlenen.mention} tarafından üstlenilmiş!", ephemeral=True)

        self.ustlenen = interaction.user
        button.label = f"{interaction.user.display_name} Üstlendi"
        button.style = discord.ButtonStyle.success
        button.disabled = True

        await interaction.response.edit_message(view=self)
        await interaction.channel.send(f"<a:dogru:1571567011224617081> {interaction.user.mention} yetkilisi {self.yeni_uye.mention} üyesinin kaydını üstlendi!")

@bot.event
async def on_member_join(member: discord.Member):
    kayitsiz_rol = member.guild.get_role(ROL_KAYITSIZ)
    if kayitsiz_rol:
        try: await member.add_roles(kayitsiz_rol)
        except: pass

    kanal = member.guild.get_channel(KANAL_KAYIT_SOHBET)
    if not kanal: return

    embed = discord.Embed(
        title="<a:ATLS_hosgeldin:1571135479120924712> ATLANTIS LEAGUE | Hoş Geldin",
        description=f"Merhaba **{member.name}**, sunucumuza hoş geldiniz!",
        color=0x00FFCC
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await kanal.send(content=f"<@&{ROL_KAYIT_YETKILISI}> | {member.mention}", embed=embed, view=HosGeldinButonlari(member))
class KayitButonlari(discord.ui.View):
    def __init__(self, hedef_uye, yetkili, ozel_isim: str = None):
        super().__init__(timeout=60)
        self.hedef_uye = hedef_uye
        self.yetkili = yetkili
        self.ozel_isim = ozel_isim

    async def rol_ver_islem(self, interaction: discord.Interaction, rol_id: int, rol_adi: str, emoji: str):
        if interaction.user != self.yetkili and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Bu butonları sadece komutu yazan yetkili kullanabilir!", ephemeral=True)

        guild = interaction.guild
        kayitsiz_rol = guild.get_role(ROL_KAYITSIZ)
        verilecek_rol = guild.get_role(rol_id)

        try:
            if kayitsiz_rol and kayitsiz_rol in self.hedef_uye.roles:
                await self.hedef_uye.remove_roles(kayitsiz_rol)
            if verilecek_rol:
                await self.hedef_uye.add_roles(verilecek_rol)
        except Exception as e:
            return await interaction.response.send_message(f"<a:ATLS_yanlis:1571131131657584712> Hata: {e}", ephemeral=True)

        # Eğer komutta isim yazıldıysa onu baz al, yoksa mevcut adını koru
        if self.ozel_isim:
            temel_isim = self.ozel_isim
        else:
            temel_isim = self.hedef_uye.display_name

        if "M€" in temel_isim:
            import re
            yeni_isim = re.sub(r'\d+(\.\d+)?M€', '1M€', temel_isim)
        else:
            yeni_isim = f"{temel_isim} | 1M€"

        try:
            await self.hedef_uye.edit(nick=yeni_isim)
        except Exception as e:
            print(f"İsim değiştirilemedi: {e}")

        guild_id = guild.id
        u_id = self.yetkili.id
        if guild_id not in kayit_verileri: kayit_verileri[guild_id] = {}
        if u_id not in kayit_verileri[guild_id]: kayit_verileri[guild_id][u_id] = 0
        kayit_verileri[guild_id][u_id] += 1

        embed = discord.Embed(
            title="<a:dogru:1571567011224617081> Başarılı Kayıt İşlemi!",
            description=f"{emoji} {self.hedef_uye.mention} üyesi **{rol_adi}** olarak başarıyla kayıt edildi ve ismi `{yeni_isim}` yapıldı!",
            color=0x00FF00
        )
        await interaction.response.edit_message(embed=embed, view=None)

        chat_kanali = guild.get_channel(KANAL_CHAT)
        if chat_kanali:
            selam_embed = discord.Embed(
                title="<a:ATLS_hosgeldin:1571135479120924712> Aramıza Hoş Geldin!",
                description=f"<a:ATLS_rocket:1571132526511132763> {self.hedef_uye.mention} başarıyla **{rol_adi}** rolüyle aramızda yerini aldı! <a:lorex_futboltopu:1571500016382644274>",
                color=0xFFD700
            )
            selam_embed.set_thumbnail(url=self.hedef_uye.display_avatar.url)
            await chat_kanali.send(embed=selam_embed)

    @discord.ui.button(label="Futbolcu", style=discord.ButtonStyle.primary, emoji="<:ATLS_Futbolcu:1570109561354985492>")
    async def futbolcu_tikla(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rol_ver_islem(interaction, ROL_FUTBOLCU, "Futbolcu", "<:ATLS_Futbolcu:1570109561354985492>")

    @discord.ui.button(label="Teknik Direktör", style=discord.ButtonStyle.success, emoji="<:ATLS_spiker:1570109151743320246>")
    async def td_tikla(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rol_ver_islem(interaction, ROL_TD, "Teknik Direktör", "<:ATLS_spiker:1570109151743320246>")

    @discord.ui.button(label="Klüp Başkanı", style=discord.ButtonStyle.danger, emoji="<:baskan:1571562225628614759>")
    async def baskan_tikla(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.rol_ver_islem(interaction, ROL_BASKAN, "Klüp Başkanı", "<:baskan:1571562225628614759>")

    @discord.ui.button(label="İptal", style=discord.ButtonStyle.secondary, emoji="<a:ATLS_yanlis:1571131131657584712>")
    async def iptal_tikla(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.yetkili: return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Yetkin yok!", ephemeral=True)
        await interaction.response.edit_message(embed=discord.Embed(title="<a:ATLS_yanlis:1571131131657584712> İptal Edildi", color=discord.Color.red()), view=None)

@bot.command(name="k")
async def kayit_et(ctx, uye: discord.Member = None, *, yeni_isim: str = None):
    if not yetkili_mi(ctx): return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Yetkin yok!")
    if not uye: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Doğrusu: `.k @Kullanici Ad | 1M`")
    embed = discord.Embed(title="<a:hedef:1571436272881508442> Kayıt İşlemi", description=f"<a:hedef:1571436272881508442> {uye.mention} için rol seçin:", color=0xFFD700)
    await ctx.send(embed=embed, view=KayitButonlari(uye, ctx.author, yeni_isim))

@bot.command(name="kver")
async def kayitsiz_ver(ctx, uye: discord.Member = None):
    if not yetkili_mi(ctx): return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Yetkin yok!")
    if not uye: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Doğrusu: `.kver @Kullanici`")
    rol = ctx.guild.get_role(ROL_KAYITSIZ)
    if rol:
        try: await uye.add_roles(rol); await ctx.send(f"<a:dogru:1571567011224617081> {uye.mention} kullanıcısına kayıtsız rolü verildi.")
        except Exception as e: await ctx.send(f"<a:ATLS_yanlis:1571131131657584712> Hata: {e}")

@bot.command(name="ara")
async def uye_ara(ctx, *, aranan_isim: str = None):
    if not aranan_isim: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Doğrusu: `.ara İsim`")
    bulunanlar = [m for m in ctx.guild.members if aranan_isim.lower() in m.display_name.lower()]
    if bulunanlar:
        liste = "\n".join([f"• {m.mention} (`{m.display_name}`)" for m in bulunanlar[:10]])
        await ctx.send(embed=discord.Embed(title=f"<a:bilgi:1571085351164842054> Arama: {aranan_isim}", description=liste, color=0x00FFCC))
    else: await ctx.send("<a:ATLS_yanlis:1571131131657584712> Kimse bulunamadı!")

@bot.command(name="kbilgi")
async def kayit_bilgi(ctx, uye: discord.Member = None):
    hedef = uye or ctx.author
    sayi = kayit_verileri.get(ctx.guild.id, {}).get(hedef.id, 0)
    deg = oyuncu_degerleri.get(hedef.id, 1.0)
    embed = discord.Embed(title="<a:bilgi:1571085351164842054> Kullanıcı Bilgi", description=f"👤 **Kullanıcı:** {hedef.mention}\n📊 **Kayıt Sayısı:** `{sayi}`\n<:ATLS_para:1570109603830567053> **Değer:** `{deg}M€`", color=0x00FFCC)
    embed.set_thumbnail(url=hedef.display_avatar.url)
    await ctx.send(embed=embed)

class KayitSayfaView(discord.ui.View):
    def __init__(self, veri_listesi):
        super().__init__(timeout=60)
        self.veri_listesi = veri_listesi
        self.current_page = 0
        self.max_page = (len(veri_listesi) - 1) // 10

    def get_embed(self):
        start = self.current_page * 10
        sayfa_verisi = self.veri_listesi[start:start+10]
        desc = "".join([f"**{idx}.** <@{u_id}> — **{sayi}** Kayıt\n" for idx, (u_id, sayi) in enumerate(sayfa_verisi, start=start+1)])
        embed = discord.Embed(title="<a:ATLS_dansedenmaymun:1571133976612049056> TOP 30 | Kayıt Liderliği", description=desc or "Yetkili yok.", color=0xFFD700)
        embed.set_footer(text=f"Sayfa {self.current_page + 1} / {self.max_page + 1}")
        return embed

    @discord.ui.button(label="◀ Geri", style=discord.ButtonStyle.blurple)
    async def geri(self, i: discord.Interaction, b: discord.ui.Button):
        if self.current_page > 0: self.current_page -= 1; await i.response.edit_message(embed=self.get_embed(), view=self)
        else: await i.response.defer()

    @discord.ui.button(label="İleri ▶", style=discord.ButtonStyle.blurple)
    async def ileri(self, i: discord.Interaction, b: discord.ui.Button):
        if self.current_page < self.max_page: self.current_page += 1; await i.response.edit_message(embed=self.get_embed(), view=self)
        else: await i.response.defer()

@bot.command(name="ksayı")
async def ksayi(ctx):
    g_id = ctx.guild.id
    if g_id not in kayit_verileri or not kayit_verileri[g_id]: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Kayıt yapan yok!")
    sirali = sorted(kayit_verileri[g_id].items(), key=lambda x: x[1], reverse=True)[:30]
    await ctx.send(embed=KayitSayfaView(sirali).get_embed(), view=KayitSayfaView(sirali))

@bot.command(name="şart")
async def sart(ctx):
    embed = discord.Embed(
        title="<a:ATLS_simsekirmizi:1571131025306685532> ATLANTIS LEAGUE | Kayıt Şartları",
        description="<a:hedef:1571436272881508442> **Kayıt olmak için bu 2 şeyi yapın:**\n\n1️⃣ <#1570103439189610596> Kalıcı tik kanalından tike basın.\n2️⃣ <#1570104089268723742> Rol Al kanalından en az 3 rol alın.",
        color=0xFFD700
    )
    await ctx.send(embed=embed)
class PenaltiView(discord.ui.View):
    def __init__(self, atici: discord.Member):
        super().__init__(timeout=30)
        self.atici = atici
        self.secim = None

    @discord.ui.button(label="Sol Köşe", style=discord.ButtonStyle.primary, emoji="⚡")
    async def sol(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.atici: return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Sen atamazsın!", ephemeral=True)
        self.secim = "Sol Köşe"; self.stop(); await interaction.response.defer()

    @discord.ui.button(label="Orta (Üst)", style=discord.ButtonStyle.secondary, emoji="⚽")
    async def orta(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.atici: return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Sen atamazsın!", ephemeral=True)
        self.secim = "Orta (Üst)"; self.stop(); await interaction.response.defer()

    @discord.ui.button(label="Sağ Köşe", style=discord.ButtonStyle.danger, emoji="⚡")
    async def sag(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.atici: return await interaction.response.send_message("<a:ATLS_yanlis:1571131131657584712> Sen atamazsın!", ephemeral=True)
        self.secim = "Sağ Köşe"; self.stop(); await interaction.response.defer()

@bot.command(name="pen")
async def penalti(ctx):
    if ctx.channel.id != PENALTI_KANAL_ID:
        return await ctx.send(f"<a:ATLS_yanlis:1571131131657584712> Lütfen <#{PENALTI_KANAL_ID}> kanalında kullan!")

    view = PenaltiView(ctx.author)
    embed = discord.Embed(title="<a:ATLS_rocket:1571132526511132763> Penaltı Atışı • Atlantis League", description=f"<a:hedef:1571436272881508442> {ctx.author.mention}, nereye vurmak istersin?", color=0xFFD700)
    msg = await ctx.send(embed=embed, view=view)
    
    await view.wait()
    if view.secim is None:
        for child in view.children: child.disabled = True
        return await msg.edit(content="<a:ATLS_yanlis:1571131131657584712> Süre bitti!", view=view)

    sonuclar = ["Gol! ⚽", "Kaleci Kurtardı! 🧤", "Aut! ❌", "Direkten Döndü! 💥"]
    sonuc = random.choice(sonuclar)

    uid = ctx.author.id
    eski_deg = oyuncu_degerleri.get(uid, 1.0)
    degisim_metni = "Değişmedi"

    if "Gol" in sonuc:
        yeni_deg = min(MAX_DEGER, round(eski_deg + 1.0, 2))
        oyuncu_degerleri[uid] = yeni_deg
        degisim_metni = f"+1.0M€ ({eski_deg}M > {yeni_deg}M)"
    
    sonuc_embed = discord.Embed(
        title="<a:lorex_futboltopu:1571500016382644274> Penaltı Sonucu • Atlantis League",
        description=f"**Atıcı:** {ctx.author.mention}\n\n🎯 **Sonuç:** {sonuc}\n📌 **Tercihin:** `{view.secim}`\n\n<:ATLS_para:1570109603830567053> **Değer Değişimi:** {degisim_metni}",
        color=discord.Color.green() if "Gol" in sonuc else discord.Color.red()
    )
    for child in view.children: child.disabled = True
    await msg.edit(embed=sonuc_embed, view=view)

async def deger_ekle(user_id, miktar):
    mevcut = oyuncu_degerleri.get(user_id, 1.0)
    yeni = min(MAX_DEGER, mevcut + miktar)
    oyuncu_degerleri[user_id] = round(yeni, 2)
    return oyuncu_degerleri[user_id]

@bot.command(name="antrenman", aliases=["ant"])
async def antrenman(ctx):
    if ctx.channel.id != ANTRENMAN_KANAL_ID:
        return await ctx.send(f"<a:ATLS_yanlis:1571131131657584712> Lütfen <#{ANTRENMAN_KANAL_ID}> kanalında dene!")
    
    uid = ctx.author.id
    mevcut_adim = antrenman_ilerleme.get(uid, 0) + 1
    antrenman_ilerleme[uid] = mevcut_adim  
    
    if mevcut_adim >= 10:
        antrenman_ilerleme[uid] = 0
        yeni_deg = await deger_ekle(uid, round(random.uniform(5.0, 15.0), 2))
        bar = "<a:ATLS_barbaslangic:1571132296772460575>" + ("<a:ATLS_barorta:1571132350593769614>" * 10) + "<a:ATLS_barson:1571132377902874625>"
        
        embed = discord.Embed(
            title="<a:dogru:1571567011224617081> Antrenman Tamamlandı (10/10)!",
            description=f"{ctx.author.mention} 10/10 antrenmanını tamamladı! <a:ATLS_rocket:1571132526511132763>\n\n**İlerleme Barı:**\n{bar} **%100**\n\n<:ATLS_para:1570109603830567053> Güncel Değeriniz: **{yeni_deg}M€**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        yuzde = mevcut_adim * 10
        aktif_orta = "<a:ATLS_barorta:1571132350593769614>" * mevcut_adim
        bos_orta = "<:barbos:1571386251947417741>" * (10 - mevcut_adim)
        son_bosluk = "<:barbos:1571386305110085682>"
        bar = "<a:ATLS_barbaslangic:1571132296772460575>" + aktif_orta + bos_orta + son_bosluk
        
        embed = discord.Embed(
            title="<a:ATLS_rocket:1571132526511132763> Antrenman Devam Ediyor",
            description=f"{ctx.author.mention} antrenmana devam ediyor! ({mevcut_adim}/10) <a:lorex_futboltopu:1571500016382644274>\n\n**İlerleme Barı:**\n{bar} **%{yuzde}**",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

DEGER_YETKILI_ROL_ID = 1569926195099730051
LOG_YETKILI_ROL_ID = 1569926072026402909
DEGER_ARTIS_LOG_KANAL_ID = 1570104305128706198
DEGER_DUSUS_LOG_KANAL_ID = 1571928849758027877

yetkili_istatistik = {}
deger_log_aktif = True

def deger_yetkilisi_mi(member): return member.guild_permissions.administrator or any(r.id == DEGER_YETKILI_ROL_ID for r in member.roles)
def log_yetkilisi_mi(member): return member.guild_permissions.administrator or any(r.id == LOG_YETKILI_ROL_ID for r in member.roles)

async def deger_islemi(ctx, hedef, miktar, sebep, is_artis):
    global deger_log_aktif
    if not deger_yetkilisi_mi(ctx.author):
        return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Bu komut için yetkili rolün yok!", ephemeral=True)
    
    uid = hedef.id
    eski_deg = oyuncu_degerleri.get(uid, 1.0)
    yetkili = ctx.author
    if yetkili.id not in yetkili_istatistik: yetkili_istatistik[yetkili.id] = {"verme_sayisi": 0, "silme_sayisi": 0, "toplam_islem_m": 0.0}

    if is_artis:
        yeni_deg = round(eski_deg + miktar, 2)
        renk, log_Kanal, baslik = discord.Color.green(), DEGER_ARTIS_LOG_KANAL_ID, "Değer Verildi"
        yetkili_istatistik[yetkili.id]["verme_sayisi"] += 1
    else:
        yeni_deg = max(0.0, round(eski_deg - miktar, 2))
        renk, log_Kanal, baslik = discord.Color.red(), DEGER_DUSUS_LOG_KANAL_ID, "Değer Düşürüldü"
        yetkili_istatistik[yetkili.id]["silme_sayisi"] += 1

    yetkili_istatistik[yetkili.id]["toplam_islem_m"] += miktar
    oyuncu_degerleri[uid] = yeni_deg

    mevsim = hedef.display_name
    if f"{eski_deg}M€" in mevsim: yeni_isim = mevsim.replace(f"{eski_deg}M€", f"{yeni_deg}M€")
    elif "M€" in mevsim:
        import re
        yeni_isim = re.sub(r'\d+(\.\d+)?M€', f"{yeni_deg}M€", mevsim)
    else: yeni_isim = f"{mevsim} | {yeni_deg}M€"

    try: await hedef.edit(nick=yeni_isim)
    except: pass

    await ctx.send(embed=discord.Embed(title=f"<:market:1571203690629435463> {hedef.display_name} | M€", description=f"<a:dogru:1571567011224617081> Değer güncellendi: **{eski_deg}M > {yeni_deg}M**", color=renk))
    if deger_log_aktif:
        log_k = ctx.guild.get_channel(log_Kanal)
        if log_k: await log_k.send(embed=discord.Embed(title=f"💾 {baslik}", description=f"{hedef.mention} değeri **{eski_deg}M > {yeni_deg}M** oldu.\nSebep: {sebep}", color=renk))

@bot.command(name="dver")
async def dver(ctx, hedef: discord.Member = None, miktar: float = None, *, sebep: str = "Belirtilmemiş"):
    if not hedef or miktar is None: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Yanlış kullanım doğrusu .dver @Kullanici adi [Miktar] [Sebep] yazsın")
    await deger_islemi(ctx, hedef, miktar, sebep, True)

@bot.command(name="dsil")
async def dsil(ctx, hedef: discord.Member = None, miktar: float = None, *, sebep: str = "Belirtilmemiş"):
    if not hedef or miktar is None: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Yanlış kullanım doğrusu .dsil @Kullanici adi [Miktar] [Sebep] yazsın")
    await deger_islemi(ctx, hedef, miktar, sebep, False)

@bot.command(name="dbilgi")
async def dbilgi(ctx, uye: discord.Member = None):
    hedef = uye or ctx.author
    i = yetkili_istatistik.get(hedef.id, {"verme_sayisi": 0, "silme_sayisi": 0, "toplam_islem_m": 0.0})
    await ctx.send(embed=discord.Embed(title=f"<:market:1571203690629435463> {hedef.name} İstatistikleri", description=f"<a:dogru:1571567011224617081> Verdiği: `{i['verme_sayisi']}`\n<a:ATLS_yanlis:1571131131657584712> Sildiği: `{i['silme_sayisi']}`\n<:market:1571203690629435463> Toplam: `{i['toplam_islem_m']}M€`", color=0x00FFCC))

@bot.command(name="dlogac")
async def dlogac(ctx):
    global deger_log_aktif
    if not log_yetkilisi_mi(ctx.author): return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Yetkin yok!")
    deger_log_aktif = True; await ctx.send("<a:dogru:1571567011224617081> Değer log açıldı.")

@bot.command(name="dlogkapat")
async def dlogkapat(ctx):
    global deger_log_aktif
    if not log_yetkilisi_mi(ctx.author): return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Yetkin yok!")
    deger_log_aktif = False; await ctx.send("<a:ATLS_yanlis:1571131131657584712> Değer log kapatıldı.")
class YetkiliDsayiPaginationView(discord.ui.View):
    def __init__(self, veri_listesi):
        super().__init__(timeout=120)
        self.veri_listesi = veri_listesi
        self.current_page = 0
        self.max_page = (len(veri_listesi) - 1) // 10

    def get_embed(self):
        start = self.current_page * 10
        sayfa_verisi = self.veri_listesi[start:start+10]
        desc = "".join([f"**{idx}.** <@{uid}> — Verilen: `{v['verme_sayisi']}` | Silinen: `{v['silme_sayisi']}`\n" for idx, (uid, v) in enumerate(sayfa_verisi, start=start+1)])
        embed = discord.Embed(title="<:market:1571203690629435463> En Çok İşlem Yapan Yetkililer (Top 30)", description=desc or "Veri yok.", color=0xFFD700)
        embed.set_footer(text=f"Sayfa {self.current_page + 1} / {self.max_page + 1}")
        return embed

    @discord.ui.button(label="◀ Geri", style=discord.ButtonStyle.blurple)
    async def geri(self, i, b):
        if self.current_page > 0: self.current_page -= 1; await i.response.edit_message(embed=self.get_embed(), view=self)
        else: await i.response.defer()

    @discord.ui.button(label="İleri ▶", style=discord.ButtonStyle.blurple)
    async def ileri(self, i, b):
        if self.current_page < self.max_page: self.current_page += 1; await i.response.edit_message(embed=self.get_embed(), view=self)
        else: await i.response.defer()

@bot.command(name="dsayı")
async def dsayi(ctx):
    if not yetkili_istatistik: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Veri bulunmuyor!")
    sirali = sorted(yetkili_istatistik.items(), key=lambda x: x[1]["toplam_islem_m"], reverse=True)[:30]
    await ctx.send(embed=YetkiliDsayiPaginationView(sirali).get_embed(), view=YetkiliDsayiPaginationView(sirali))

# Ticket Sistemi
TICKET_KATEGORI_ID = 1570104193195311194
TICKET_YETKILI_ROL_ID = 1569926208987340822
ticket_sayac = 0

class TicketModal(discord.ui.Modal, title="Destek Talebi Oluştur"):
    def __init__(self, kat): super().__init__(); self.kat = kat
    sorun = discord.ui.TextInput(label="Sorununuz Nedir?", style=discord.TextStyle.short, required=True)
    detay = discord.ui.TextInput(label="Detay", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global ticket_sayac
        guild = interaction.guild
        kategori = guild.get_channel(TICKET_KATEGORI_ID)
        yetkili_rol = guild.get_role(TICKET_YETKILI_ROL_ID)
        ticket_sayac += 1
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        if yetkili_rol: overwrites[yetkili_rol] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        
        kanal = await guild.create_text_channel(f"ticket-{ticket_sayac}", category=kategori, overwrites=overwrites)
        embed = discord.Embed(title=f"<:market:1571203690629435463> Talep #{ticket_sayac} — {self.kat}", description=f"**Sorun:** {self.sorun.value}\n**Detay:** {self.detay.value}", color=0xFFD700)
        
        view = TicketControlView(interaction.user)
        msg = await kanal.send(content=f"{interaction.user.mention} {yetkili_rol.mention if yetkili_rol else ''}", embed=embed, view=view)
        view.message = msg
        await interaction.response.send_message(f"<a:dogru:1571567011224617081> Destek talebin oluşturuldu: {kanal.mention}", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self, sahibi): super().__init__(timeout=None); self.sahibi = sahibi

    @discord.ui.button(label="Üstlen", style=discord.ButtonStyle.primary, emoji="<:yetkili:1571204506774020103>", custom_id="t_ustlen")
    async def ustlen(self, i, b):
        b.label = f"{i.user.display_name} Üstlendi"; b.style = discord.ButtonStyle.success; b.disabled = True
        await i.message.edit(view=self)
        await i.channel.send(f"<:yetkili:1571204506774020103> Talep **{i.user.mention}** tarafından üstlenildi!")

    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="<a:ATLS_yanlis:1571131131657584712>", custom_id="t_kapat")
    async def kapat(self, i, b):
        await i.response.send_message("<:sebep:1571203951808872668> Talep kapatılıyor...")
        await asyncio.sleep(3); await i.channel.delete()

class TicketSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(placeholder="Kategori seçin...", options=[
            discord.SelectOption(label="Genel Sorunlar", emoji="<:genel:1571203823840796759>"),
            discord.SelectOption(label="Teknik Sorunlar", emoji="<:yetkili:1571204506774020103>"),
            discord.SelectOption(label="Ödeme / Satın Alım", emoji="<:market:1571203690629435463>"),
            discord.SelectOption(label="Diğer", emoji="<:sebep:1571203951808872668>")
        ], custom_id="t_select")
    async def callback(self, i): await i.response.send_modal(TicketModal(self.values[0]))

class TicketPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None); self.add_item(TicketSelect())

@bot.command(name="tsistem")
async def tsistem(ctx):
    if not ctx.author.guild_permissions.administrator: return await ctx.send("<a:ATLS_yanlis:1571131131657584712> Yetkin yok!", ephemeral=True)
    embed = discord.Embed(title="Destek Sistemi", description="Aşağıdaki menüden talep oluşturabilirsin.", color=0xFFD700)
    await ctx.send(embed=embed, view=TicketPanelView())

@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    if not dondurmaci_dongusu.is_running(): dondurmaci_dongusu.start()
    print(f"{bot.user.name} aktif ve tüm komutlar/token sorunsuz yüklendi!")

# Bot Tokeni
bot.run("DISCORD_TOKEN")
