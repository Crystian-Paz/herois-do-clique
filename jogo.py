import pygame
import sys
import random
import os
import math
import numpy as np

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

WIDTH, HEIGHT = 800, 520
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Heróis do Clique")
clock = pygame.time.Clock()
FPS = 60

font       = pygame.font.SysFont("arial", 22)
small_font = pygame.font.SysFont("arial", 16)
big_font   = pygame.font.SysFont("arial", 40, bold=True)
title_font = pygame.font.SysFont("arial", 54, bold=True)
tiny_font  = pygame.font.SysFont("arial", 13)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS   = os.path.join(BASE_DIR, "assets")

def load_img(name, size=None):
    img = pygame.image.load(os.path.join(ASSETS, name)).convert_alpha()
    return pygame.transform.scale(img, size) if size else img

def load_bg(name):
    img = pygame.image.load(os.path.join(ASSETS, name)).convert()
    return pygame.transform.scale(img, (WIDTH, HEIGHT))

bg_forest = load_bg("forest.png")
bg_lava   = load_bg("lava.png")
bg_lair   = load_bg("lair.png")

slime_img  = load_img("slime.png",  (160, 160))
goblin_img = load_img("goblin.png", (130, 130))
orc_img    = load_img("orc.png",    (170, 170))
demon_img  = load_img("demon.png",  (190, 190))
dragon_img = load_img("dragon.png", (220, 220))

# ==================================================
# SÍNTESE DE SOM
# ==================================================
SAMPLE_RATE = 44100

def make_sound(freq=440, duration=0.12, wave="square", volume=0.3, decay=True):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    if wave == "square":
        v = np.sign(np.sin(2 * np.pi * freq * t)).astype(np.float32)
    elif wave == "sawtooth":
        v = (2 * ((freq * t) % 1) - 1).astype(np.float32)
    elif wave == "sine":
        v = np.sin(2 * np.pi * freq * t).astype(np.float32)
    else:
        v = np.random.uniform(-1, 1, n).astype(np.float32)
    env = (1 - np.linspace(0, 1, n)).astype(np.float32) if decay else np.ones(n, np.float32)
    samples = (v * env * volume * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([samples, samples]))

def make_music_loop(bpm=120, bars=4, style="forest"):
    beat = 60 / bpm
    n    = int(SAMPLE_RATE * beat * bars * 4)
    buf  = np.zeros((n, 2), dtype=np.float32)
    bs   = int(SAMPLE_RATE * beat)

    melodies = {
        "forest": ([261,293,329,349,392,349,329,293], [130,130,196,196]),
        "lava":   ([220,246,220,196,220,246,261,246], [110,146,110,123]),
        "lair":   ([185,196,185,174,164,174,185,196], [92, 92, 98, 87]),
    }
    melody, bass = melodies.get(style, melodies["forest"])

    def add(freq, start, dur, vol, wave="sine"):
        ns  = int(SAMPLE_RATE * dur)
        end = min(start + ns, n)
        ns  = end - start
        if ns <= 0: return
        t = np.linspace(0, dur, ns, endpoint=False)
        if wave == "sine":     v = np.sin(2*np.pi*freq*t)
        elif wave == "square": v = np.sign(np.sin(2*np.pi*freq*t)).astype(np.float32)
        elif wave == "saw":    v = 2*((freq*t)%1)-1
        else:                  v = np.random.uniform(-1,1,ns)
        s = (v * np.linspace(1,0,ns) * vol).astype(np.float32)
        buf[start:end, 0] += s
        buf[start:end, 1] += s

    for step in range(bars*4):
        add(melody[step % len(melody)], step*bs, beat*0.7, 0.11, "sine")
    for step in range(bars*4):
        add(bass[step % len(bass)],     step*bs, beat*0.9, 0.09, "saw")
    for step in range(bars*4):
        add(80, step*bs, 0.05, 0.05, "noise")

    np.clip(buf, -1, 1, out=buf)
    return pygame.sndarray.make_sound((buf*32767).astype(np.int16))

snd_hit    = make_sound(220, 0.10, "square", 0.25)
snd_crit   = make_sound(440, 0.15, "square", 0.35)
snd_buy    = make_sound(523, 0.12, "sine",   0.28)
snd_kill   = make_sound(660, 0.20, "sine",   0.32)

print("Gerando musicas...")
music = {
    "forest": make_music_loop(110, 4, "forest"),
    "lava":   make_music_loop(140, 4, "lava"),
    "lair":   make_music_loop(90,  4, "lair"),
}
print("Pronto!")

current_music = None
music_channel = pygame.mixer.Channel(0)

# ==================================================
# CONFIGURAÇÕES
# ==================================================
settings = {
    "dmg_color_normal": (255, 220,  0),
    "dmg_color_crit":   (255,  80,  0),
    "sfx_volume":        0.7,
    "music_volume":      0.4,
    "music_on":          True,
}

COLOR_NORMAL = [("Amarelo",(255,220,0)),("Branco",(255,255,255)),("Ciano",(0,220,255)),("Verde",(0,255,100))]
COLOR_CRIT   = [("Laranja",(255,80,0)),("Vermelho",(220,0,0)),("Rosa",(255,50,180)),("Roxo",(180,0,255))]

def play_music(style):
    global current_music
    if not settings["music_on"]:
        music_channel.stop()
        current_music = None
        return
    if current_music == style:
        return
    music_channel.stop()
    music_channel.play(music[style], loops=-1)
    music_channel.set_volume(settings["music_volume"])
    current_music = style

def update_music_volume():
    if settings["music_on"] and music_channel.get_busy():
        music_channel.set_volume(settings["music_volume"])

def toggle_music():
    settings["music_on"] = not settings["music_on"]
    if settings["music_on"]:
        style = enemy_list[enemy_index]["music"] if mode == "game" else "forest"
        global current_music
        current_music = None
        play_music(style)
    else:
        music_channel.stop()
        current_music = None

# ==================================================
# INIMIGOS  — Dragon tem HP triplicado
# ==================================================
enemy_list = [
    {"name":"Slime",  "hp":40,   "sprite":slime_img,  "music":"forest", "gold_drop":2},
    {"name":"Goblin", "hp":80,   "sprite":goblin_img, "music":"forest", "gold_drop":5},
    {"name":"Orc",    "hp":160,  "sprite":orc_img,    "music":"forest", "gold_drop":12},
    {"name":"Demon",  "hp":280,  "sprite":demon_img,  "music":"lava",   "gold_drop":28},
    {"name":"Dragon", "hp":1350, "sprite":dragon_img, "music":"lair",   "gold_drop":80},
]

# Tempo limite para o Dragon: 30 segundos
DRAGON_TIME_LIMIT = 30

stage_req = {0:("Slime",8), 1:("Goblin",5), 2:("Orc",4), 3:("Demon",8)}

ENEMY_DESC = {
    "Slime":  "Uma gosma viscosa dos bosques.\nFraca, mas persistente.",
    "Goblin": "Criatura agil e traicoeira\ndas florestas sombrias.",
    "Orc":    "Guerreiro brutal das montanhas.\nPele dura como pedra.",
    "Demon":  "Entidade das chamas vindas\ndas profundezas da Terra.",
    "Dragon": "O Senhor das Trevas. Boss\nfinal. Derrote-o em 30s!",
}

LORE_LINES = [
    ("titulo", "A PROFECIA DO CLIQUE"),
    ("espaco", ""),
    ("texto",  "Ha eras, o Reino de Clickaria vivia em paz sob a"),
    ("texto",  "protecao dos Herois Antigos. Mas as Sombras acordaram"),
    ("texto",  "nas profundezas, enviando hordas de monstros."),
    ("espaco", ""),
    ("texto",  "A profecia e clara: um Heroi escolhido surgira,"),
    ("texto",  "cujo toque carrega o poder de destruir o mal."),
    ("espaco", ""),
    ("destaque","Esse heroi... es tu."),
    ("espaco", ""),
    ("texto",  "Percorre os Bosques Encantados, os Campos de Lava"),
    ("texto",  "e o terrivel Covil do Dragao. Acumula ouro,"),
    ("texto",  "fortalece-te e salva Clickaria."),
    ("espaco", ""),
    ("destaque","Clique. Evolua. Venca."),
]

HOW_LINES = [
    ("titulo",   "COMO JOGAR"),
    ("espaco",   ""),
    ("subtitulo","Combate"),
    ("item",     "Clique no monstro para causar dano."),
    ("item",     "Cada monstro morto dropa Gold automaticamente."),
    ("item",     "Quanto mais dificil o inimigo, mais Gold ele dropa."),
    ("espaco",   ""),
    ("subtitulo","Upgrades  (painel esquerdo)"),
    ("item",     "+Gold/Clq  —  ganha gold extra a cada clique."),
    ("item",     "+1 Dano    —  aumenta seu dano base de clique."),
    ("item",     "Auto-DPS   —  causa dano automatico passivo."),
    ("item",     "Critico    —  10% de chance extra por nivel."),
    ("espaco",   ""),
    ("subtitulo","Progressao"),
    ("item",     "Derrote inimigos suficientes para avançar de fase."),
    ("item",     "Dragon: derrote-o em 30 segundos ou volte ao Demon!"),
    ("item",     "Acesse a Galeria para revisitar fases e farmar."),
]

SLASH_SHAPES = [
    [(-40,0,40,0)], [(0,-40,0,40)], [(-30,-30,30,30)], [(-30,30,30,-30)],
    [(-40,-20,0,20),(0,20,40,-20)], [(-30,0,0,-30),(0,-30,30,0)],
    [(-40,-10,40,10)], [(-10,-40,10,40)],
]

# ==================================================
# ESTADO DO JOGO
# ==================================================
count      = 0
damage     = 1
gold_bonus = 0
dps_level  = 0
crit_level = 0

price0 = 10    # +gold/clq
price1 = 30    # +dano
price2 = 200   # auto-dps
price3 = 600   # critico

mode        = "menu"
kills       = {e["name"]:0 for e in enemy_list}
enemy_index = 0
hp          = enemy_list[0]["hp"]
shake_timer = 0
damage_texts= []
slash_anims = []
enemy_rect  = pygame.Rect(0,0,1,1)

# Dragon timer
dragon_timer      = 0.0   # seconds elapsed while fighting dragon
dragon_failed_msg = False # show failure notification

DPS_EVENT = pygame.USEREVENT + 1
ENEMY_CX, ENEMY_CY = 555, 270

# ==================================================
# HELPERS
# ==================================================
def get_bg():
    if enemy_index <= 2: return bg_forest
    if enemy_index == 3: return bg_lava
    return bg_lair

def get_progress():
    d = stage_req.get(enemy_index)
    return (kills[d[0]], d[1]) if d else (0,0)

def can_advance():
    if enemy_index >= len(enemy_list)-1: return False
    d = stage_req.get(enemy_index)
    return d and kills[d[0]] >= d[1]

def go_to_enemy(index):
    global enemy_index, hp, mode, dragon_timer, dragon_failed_msg
    enemy_index = index
    hp = enemy_list[index]["hp"]
    dragon_timer = 0.0
    dragon_failed_msg = False
    mode = "game"
    play_music(enemy_list[index]["music"])

def next_enemy():
    global enemy_index, hp, mode, dragon_timer
    enemy_index += 1
    dragon_timer = 0.0
    if enemy_index >= len(enemy_list):
        mode = "win"
        pygame.mixer.stop()
    else:
        hp = enemy_list[enemy_index]["hp"]
        play_music(enemy_list[enemy_index]["music"])

def apply_damage(dmg):
    global hp, count, mode
    hp -= dmg
    if hp <= 0:
        hp = 0
        e  = enemy_list[enemy_index]
        kills[e["name"]] += 1
        drop = int(e["gold_drop"] * random.uniform(0.7, 1.3))
        count += drop
        ex = ENEMY_CX + random.randint(-30,30)
        ey = ENEMY_CY - random.randint(10,40)
        damage_texts.append({"txt":f"+{drop}g","x":ex,"y":ey,"life":55,"color":(255,215,0),"big":True})
        snd_kill.set_volume(settings["sfx_volume"])
        snd_kill.play()
        if can_advance():
            next_enemy()
        elif enemy_index < len(enemy_list)-1:
            hp = e["hp"]
        else:
            # Dragon killed
            if kills["Dragon"] >= 1:
                mode = "win"
                pygame.mixer.stop()
            else:
                hp = e["hp"]

def dragon_fail():
    """Called when dragon timer runs out."""
    global enemy_index, hp, dragon_timer, dragon_failed_msg
    dragon_failed_msg = True
    enemy_index = 3  # back to Demon
    hp = enemy_list[3]["hp"]
    dragon_timer = 0.0
    play_music(enemy_list[3]["music"])

def click_damage():
    if crit_level > 0:
        # 10% chance per level, capped at 80%
        chance = min(0.10 * crit_level, 0.80)
        mult   = 1 + crit_level
        if random.random() < chance:
            return damage * mult, True
    return damage, False

def draw_text(txt, fnt, color, x, y, anchor="center"):
    img = fnt.render(str(txt), True, color)
    r = img.get_rect(**{anchor:(x,y)})
    screen.blit(img, r)

def draw_button(rect, color, txt, hover=False, radius=10, fnt=None):
    if fnt is None:
        fnt = font
    c = tuple(min(255,v+35) for v in color) if hover else color
    pygame.draw.rect(screen, c, rect, border_radius=radius)
    pygame.draw.rect(screen, (200,200,200), rect, 2, border_radius=radius)
    # Fit text: try given font, fall back to tiny_font
    img = fnt.render(str(txt), True, (255,255,255))
    if img.get_width() > rect.w - 8:
        img = tiny_font.render(str(txt), True, (255,255,255))
    screen.blit(img, img.get_rect(center=rect.center))

def draw_overlay(a=150):
    s = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
    s.fill((0,0,0,a)); screen.blit(s,(0,0))

def draw_panel(rect, color=(10,10,30), a=210):
    s = pygame.Surface((rect.w,rect.h), pygame.SRCALPHA)
    s.fill((*color,a)); screen.blit(s,rect)
    pygame.draw.rect(screen,(180,150,60),rect,2,border_radius=12)

def draw_slider(label, rect, value, color):
    draw_text(label, small_font, (200,200,200), rect.x-10, rect.centery, anchor="midright")
    pygame.draw.rect(screen,(50,50,50),rect,border_radius=6)
    filled = pygame.Rect(rect.x,rect.y,int(value*rect.w),rect.h)
    if filled.w > 0:
        pygame.draw.rect(screen,color,filled,border_radius=6)
    pygame.draw.rect(screen,(160,160,160),rect,2,border_radius=6)
    draw_text(f"{int(value*100)}%", tiny_font,(200,200,200),rect.right+28,rect.centery)
    return rect

def spawn_slash(x,y,crit=False):
    slash_anims.append({"segs":random.choice(SLASH_SHAPES),"x":x,"y":y,
                         "timer":15,"color":settings["dmg_color_crit"] if crit else (255,255,255)})

def draw_slashes():
    for sl in slash_anims[:]:
        sl["timer"] -= 1
        r = sl["timer"]/15
        thick = max(1,int(r*4))
        for seg in sl["segs"]:
            c = tuple(int(v*r) for v in sl["color"])
            pygame.draw.line(screen,c,(sl["x"]+seg[0],sl["y"]+seg[1]),(sl["x"]+seg[2],sl["y"]+seg[3]),thick)
        if sl["timer"]<=0: slash_anims.remove(sl)

# ==================================================
# LAYOUT — botões
# ==================================================
CX = WIDTH//2
BW, BH = 220, 48

btn_play     = pygame.Rect(CX-BW//2, 175, BW, BH)
btn_lore     = pygame.Rect(CX-BW//2, 236, BW, BH)
btn_howto    = pygame.Rect(CX-BW//2, 297, BW, BH)
btn_settings = pygame.Rect(CX-BW//2, 358, BW, BH)
btn_back     = pygame.Rect(CX-90, HEIGHT-62, 180, 44)

PAD=10; UPW=162; UPH=70
upg_rects  = [pygame.Rect(PAD, 88+i*(UPH+8), UPW, UPH) for i in range(4)]
upg_colors = [(180,160,0),(180,100,20),(20,140,210),(190,40,40)]
upg_names  = ["+Gold/Clq","+1 Dano","Auto-DPS","Critico"]

# ==================================================
# LOOP
# ==================================================
running = True
play_music("forest")

while running:
    dt = clock.tick(FPS) / 1000.0  # delta time in seconds
    mp = pygame.mouse.get_pos()

    bg = get_bg() if mode=="game" else bg_forest
    screen.blit(bg,(0,0))

    if shake_timer>0:
        shake_timer-=1; ox=random.randint(-6,6); oy=random.randint(-4,4)
    else:
        ox=oy=0

    # Dragon countdown
    if mode == "game" and enemy_index == 4:
        dragon_timer += dt
        if dragon_timer >= DRAGON_TIME_LIMIT:
            dragon_fail()

    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False

        if event.type==DPS_EVENT and mode=="game":
            auto=max(1,dps_level*damage)
            apply_damage(auto)
            damage_texts.append({"txt":f"~{auto}","x":ENEMY_CX+random.randint(-30,30),
                                  "y":ENEMY_CY-20,"life":30,"color":(160,210,255),"big":False})

        if event.type==pygame.MOUSEBUTTONDOWN:
            mx,my=mp

            # ---- MENU ----
            if mode=="menu":
                if btn_play.collidepoint(mp):
                    mode="game"; play_music(enemy_list[enemy_index]["music"])
                elif btn_lore.collidepoint(mp):    mode="lore"
                elif btn_howto.collidepoint(mp):   mode="howto"
                elif btn_settings.collidepoint(mp):mode="settings"

            # ---- VOLTAR ----
            elif mode in ("lore","howto"):
                if btn_back.collidepoint(mp):
                    mode="menu"; music_channel.stop()
                    current_music=None; play_music("forest")

            # ---- WIN ----
            elif mode == "win":
                btn_gallery_win_e = pygame.Rect(CX-200, 350, 175, 44)
                btn_menu_win_e    = pygame.Rect(CX+25,  350, 175, 44)
                if btn_gallery_win_e.collidepoint(mp):
                    mode = "collection"
                elif btn_menu_win_e.collidepoint(mp):
                    mode="menu"; music_channel.stop(); current_music=None; play_music("forest")

            elif mode == "collection":
                if btn_back.collidepoint(mp):
                    mode="game" if enemy_index < len(enemy_list) else "menu"
                    if mode == "game":
                        play_music(enemy_list[enemy_index]["music"])
                    else:
                        music_channel.stop(); current_music=None; play_music("forest")
                else:
                    # MUST match draw rects: cols=3, cw=192, ch=118, gap=12
                    cols=3; cw=192; ch=118; gap=12
                    sx=(WIDTH-cols*cw-(cols-1)*gap)//2
                    for i,e in enumerate(enemy_list):
                        if kills[e["name"]] > 0:
                            ci=i%cols; ri=i//cols
                            cx2=sx+ci*(cw+gap); cy2=90+ri*(ch+gap)
                            cr=pygame.Rect(cx2,cy2,cw,ch)
                            if cr.collidepoint(mp):
                                go_to_enemy(i)
                                break

            # ---- SETTINGS ----
            # IMPORTANT: rects here must EXACTLY match the draw rects in the settings section below
            elif mode=="settings":
                if btn_back.collidepoint(mp):
                    mode="menu"
                else:
                    # Cor dano normal — draw: Rect(80+i*155, 104, 140, 30)
                    for i,(_,col) in enumerate(COLOR_NORMAL):
                        r=pygame.Rect(80+i*155,104,140,30)
                        if r.collidepoint(mp): settings["dmg_color_normal"]=col
                    # Cor dano crit — draw: Rect(80+i*155, 164, 140, 30)
                    for i,(_,col) in enumerate(COLOR_CRIT):
                        r=pygame.Rect(80+i*155,164,140,30)
                        if r.collidepoint(mp): settings["dmg_color_crit"]=col
                    # Slider SFX — draw: Rect(200, 282, 200, 16)
                    sfx_r=pygame.Rect(200,282,200,16)
                    if sfx_r.collidepoint(mp):
                        settings["sfx_volume"]=max(0,min(1,(mx-sfx_r.x)/sfx_r.w))
                    # Slider Musica — draw: Rect(200, 328, 200, 16)
                    mus_r=pygame.Rect(200,328,200,16)
                    if mus_r.collidepoint(mp):
                        settings["music_volume"]=max(0,min(1,(mx-mus_r.x)/mus_r.w))
                        update_music_volume()
                    # Botão mute — draw: Rect(CX-90, 365, 180, 36)
                    mute_btn=pygame.Rect(CX-90,365,180,36)
                    if mute_btn.collidepoint(mp): toggle_music()

            # ---- GAME ----
            elif mode=="game":
                if enemy_rect.collidepoint(mp):
                    dmg,crit=click_damage()
                    count+=1+gold_bonus
                    apply_damage(dmg)
                    shake_timer=8
                    spawn_slash(mx,my,crit)
                    col=settings["dmg_color_crit"] if crit else settings["dmg_color_normal"]
                    lbl=f"CRIT! {dmg}" if crit else str(dmg)
                    snd=(snd_crit if crit else snd_hit)
                    snd.set_volume(settings["sfx_volume"]); snd.play()
                    damage_texts.append({"txt":lbl,"x":mx,"y":my-10,"life":45,"color":col,"big":crit})

                prices=[price0,price1,price2,price3]
                for i,rect in enumerate(upg_rects):
                    if rect.collidepoint(mp) and count>=prices[i]:
                        count-=prices[i]
                        snd_buy.set_volume(settings["sfx_volume"]); snd_buy.play()
                        if i==0:
                            gold_bonus+=1; price0=int(price0*2.0)
                        elif i==1:
                            damage+=1;    price1=int(price1*2.2)
                        elif i==2:
                            dps_level+=1; price2=int(price2*2.3)
                            pygame.time.set_timer(DPS_EVENT,max(400,1500-dps_level*150))
                        elif i==3:
                            crit_level+=1;price3=int(price3*2.4)

                gal_btn=pygame.Rect(WIDTH-128,HEIGHT-48,118,34)
                if gal_btn.collidepoint(mp): mode="collection"

                menu_btn=pygame.Rect(WIDTH-258,HEIGHT-48,118,34)
                if menu_btn.collidepoint(mp):
                    mode="menu"
                    music_channel.stop()
                    current_music=None
                    play_music("forest")

            # ---- DRAGON FAIL notif dismiss ----
            # (handled automatically after a few seconds, see drawing section)

    # ====================================================
    # DESENHO — MENU
    # ====================================================
    if mode=="menu":
        draw_overlay(110)

        sh = title_font.render("HEROIS DO CLIQUE", True, (0,0,0))
        screen.blit(sh, sh.get_rect(center=(CX+3,93)))
        ti = title_font.render("HEROIS DO CLIQUE", True, (255,220,60))
        screen.blit(ti, ti.get_rect(center=(CX,90)))

        sub = small_font.render("Um clicker epico de fantasia", True, (190,190,190))
        screen.blit(sub, sub.get_rect(center=(CX,135)))

        for rect,col,txt in [
            (btn_play,    (35,160,55),  "Jogar"),
            (btn_lore,    (75,55,155),  "Lore"),
            (btn_howto,   (25,110,170), "Como Jogar"),
            (btn_settings,(75,75,75),   "Configuracoes"),
        ]:
            draw_button(rect,col,txt,hover=rect.collidepoint(mp))

        ver=tiny_font.render("v2.2 — Herois do Clique",True,(90,90,90))
        screen.blit(ver,(8,HEIGHT-18))

    # ====================================================
    # DESENHO — LORE
    # ====================================================
    elif mode=="lore":
        draw_overlay(140)
        panel=pygame.Rect(55,22,WIDTH-110,HEIGHT-72)
        draw_panel(panel,(8,4,28))

        y=58
        for kind,line in LORE_LINES:
            if kind=="titulo":
                draw_text(line,big_font,(255,215,50),CX,y); y+=52
            elif kind=="espaco":
                y+=10
            elif kind=="destaque":
                draw_text(line,font,(200,160,255),CX,y); y+=28
            else:
                draw_text(line,small_font,(210,195,240),CX,y); y+=22

        draw_button(btn_back,(55,55,55),"Voltar",hover=btn_back.collidepoint(mp))

    # ====================================================
    # DESENHO — COMO JOGAR
    # ====================================================
    elif mode=="howto":
        draw_overlay(140)
        panel=pygame.Rect(55,22,WIDTH-110,HEIGHT-72)
        draw_panel(panel,(4,18,8))

        y=58
        for kind,line in HOW_LINES:
            if kind=="titulo":
                draw_text(line,big_font,(100,240,110),CX,y); y+=52
            elif kind=="espaco":
                y+=10
            elif kind=="subtitulo":
                draw_text(line,font,(160,230,160),CX,y); y+=28
            elif kind=="item":
                draw_text(line,small_font,(195,225,195),CX,y); y+=22

        draw_button(btn_back,(55,55,55),"Voltar",hover=btn_back.collidepoint(mp))

    # ====================================================
    # DESENHO — CONFIGURAÇÕES  (reorganizado)
    # ====================================================
    elif mode=="settings":
        draw_overlay(140)
        panel=pygame.Rect(38,18,WIDTH-76,HEIGHT-55)
        draw_panel(panel,(8,8,28))

        draw_text("CONFIGURACOES",big_font,(255,215,50),CX,48)

        # --- Cores dano normal ---
        draw_text("Cor do dano normal",small_font,(190,190,190),CX,88,anchor="center")
        for i,(name,col) in enumerate(COLOR_NORMAL):
            r=pygame.Rect(80+i*155,104,140,30)
            pygame.draw.rect(screen,col,r,border_radius=7)
            if settings["dmg_color_normal"]==col:
                pygame.draw.rect(screen,(255,255,255),r,3,border_radius=7)
            draw_text(name,tiny_font,(0,0,0) if sum(col)>420 else (255,255,255),r.centerx,r.centery)

        # --- Cores dano crit ---
        draw_text("Cor do dano critico",small_font,(190,190,190),CX,148,anchor="center")
        for i,(name,col) in enumerate(COLOR_CRIT):
            r=pygame.Rect(80+i*155,164,140,30)
            pygame.draw.rect(screen,col,r,border_radius=7)
            if settings["dmg_color_crit"]==col:
                pygame.draw.rect(screen,(255,255,255),r,3,border_radius=7)
            draw_text(name,tiny_font,(255,255,255),r.centerx,r.centery)

        # --- Preview bem separado ---
        prev_panel = pygame.Rect(CX-180, 208, 360, 52)
        pygame.draw.rect(screen,(20,20,50), prev_panel, border_radius=8)
        pygame.draw.rect(screen,(100,100,140), prev_panel, 1, border_radius=8)
        draw_text("Preview:", tiny_font,(150,150,180), prev_panel.x+12, prev_panel.centery, anchor="midleft")
        pn=font.render("15 dano", True, settings["dmg_color_normal"])
        screen.blit(pn, pn.get_rect(center=(CX-40, prev_panel.centery)))
        pc=font.render("CRIT! 42", True, settings["dmg_color_crit"])
        screen.blit(pc, pc.get_rect(center=(CX+100, prev_panel.centery)))

        # --- Sliders ---
        sfx_r=pygame.Rect(200,282,200,16)
        draw_slider("Vol. SFX",sfx_r,settings["sfx_volume"],(80,200,120))

        mus_r=pygame.Rect(200,328,200,16)
        draw_slider("Vol. Musica",mus_r,settings["music_volume"],(100,140,220))

        # --- Botão mute com largura maior ---
        mute_btn=pygame.Rect(CX-90,365,180,36)
        mute_col=(160,40,40) if not settings["music_on"] else (40,130,40)
        mute_lbl="Musica: MUDO" if not settings["music_on"] else "Musica: LIGADA"
        draw_button(mute_btn,mute_col,mute_lbl,hover=mute_btn.collidepoint(mp),fnt=small_font)

        draw_button(btn_back,(55,55,55),"Voltar",hover=btn_back.collidepoint(mp))

    # ====================================================
    # DESENHO — GAME
    # ====================================================
    elif mode=="game":
        enemy=enemy_list[enemy_index]

        s=pygame.Surface((UPW+PAD*2,HEIGHT),pygame.SRCALPHA)
        s.fill((0,0,0,145)); screen.blit(s,(0,0))

        draw_text("UPGRADES",small_font,(255,210,70),(UPW+PAD*2)//2,18)
        draw_text(f"Gold: {count}",font,(255,215,0),(UPW+PAD*2)//2,44)
        draw_text(f"DMG: {damage}",tiny_font,(190,190,190),(UPW+PAD*2)//2,66)

        prices=[price0,price1,price2,price3]
        upg_subs=[
            f"Bonus: +{gold_bonus}/clq",
            f"Dano atual: {damage}",
            f"Nivel: {dps_level}",
            f"Nivel: {crit_level}  chance:{min(80,crit_level*10)}%",
        ]
        for i,rect in enumerate(upg_rects):
            can=count>=prices[i]
            hover=rect.collidepoint(mp) and can
            col=upg_colors[i]
            dc=tuple(max(0,v-70) for v in col) if not can else col
            bc=tuple(min(255,v+35) for v in dc) if hover else dc
            pygame.draw.rect(screen,bc,rect,border_radius=8)
            pygame.draw.rect(screen,(170,170,170) if can else (55,55,55),rect,2,border_radius=8)
            draw_text(upg_names[i],small_font,(255,255,255),rect.centerx,rect.y+16)
            draw_text(upg_subs[i], tiny_font, (200,200,200),rect.centerx,rect.y+33)
            draw_text(f"{prices[i]}g",tiny_font,(255,215,0) if can else (110,110,110),rect.centerx,rect.y+52)

        s2=pygame.Surface((WIDTH-(UPW+PAD*2),76),pygame.SRCALPHA)
        s2.fill((0,0,0,125)); screen.blit(s2,(UPW+PAD*2,0))

        cur,needed=get_progress()
        draw_text(enemy["name"],font,(255,255,255),WIDTH//2+55,17)
        draw_text(f"HP: {hp} / {enemy['hp']}",small_font,(200,200,200),WIDTH//2+55,37)

        bx=UPW+PAD*2+18; bw=WIDTH-bx-18
        pygame.draw.rect(screen,(55,25,25),(bx,55,bw,15),border_radius=7)
        ratio=max(0,hp/enemy["hp"])
        if ratio>0:
            bcol=(50,200,50) if ratio>0.5 else (220,180,0) if ratio>0.25 else (220,30,30)
            pygame.draw.rect(screen,bcol,(bx,55,int(ratio*bw),15),border_radius=7)
        pygame.draw.rect(screen,(160,160,160),(bx,55,bw,15),2,border_radius=7)

        # Dragon: show countdown timer
        if enemy_index == 4:
            time_left = max(0.0, DRAGON_TIME_LIMIT - dragon_timer)
            tcol = (220,30,30) if time_left < 10 else (255,200,0)
            draw_text(f"TEMPO: {time_left:.1f}s", font, tcol, WIDTH-80, 55, anchor="center")
        else:
            prog=f"Kills: {cur}/{needed}" if needed>0 else "BOSS FINAL!"
            draw_text(prog,small_font,(190,190,190),WIDTH-82,17)
            draw_text(f"+{enemy['gold_drop']}g/kill",tiny_font,(255,200,50),WIDTH-82,35)

        sprite=enemy["sprite"]
        edx=ENEMY_CX+ox; edy=ENEMY_CY+oy
        enemy_rect=sprite.get_rect(center=(edx,edy))

        sw=sprite.get_width()
        shd=pygame.Surface((sw,16),pygame.SRCALPHA)
        pygame.draw.ellipse(shd,(0,0,0,65),(0,0,sw,16))
        screen.blit(shd,(enemy_rect.x,enemy_rect.bottom-9))
        screen.blit(sprite,enemy_rect)

        mini_hp_rect = pygame.Rect(enemy_rect.x, enemy_rect.y-18, sw, 10)
        pygame.draw.rect(screen,(75,0,0),mini_hp_rect,border_radius=4)
        if ratio>0:
            pygame.draw.rect(screen,(210,30,30),(enemy_rect.x,enemy_rect.y-18,int(ratio*sw),10),border_radius=4)

        draw_slashes()

        for t in damage_texts[:]:
            t["y"]-=1.3; t["life"]-=1
            f2=font if t.get("big") else small_font
            img=f2.render(t["txt"],True,t["color"])
            screen.blit(img,(t["x"]-img.get_width()//2,int(t["y"])))
            if t["life"]<=0: damage_texts.remove(t)

        gal_btn=pygame.Rect(WIDTH-128,HEIGHT-48,118,34)
        draw_button(gal_btn,(50,50,110),"Galeria",hover=gal_btn.collidepoint(mp),radius=8)

        menu_btn=pygame.Rect(WIDTH-258,HEIGHT-48,118,34)
        draw_button(menu_btn,(90,40,40),"Menu",hover=menu_btn.collidepoint(mp),radius=8)

        # Dragon fail notification overlay
        if dragon_failed_msg:
            notif = pygame.Rect(UPW+PAD*2+20, HEIGHT//2-55, WIDTH-(UPW+PAD*2)-40, 110)
            ns = pygame.Surface((notif.w, notif.h), pygame.SRCALPHA)
            ns.fill((80,0,0,220))
            screen.blit(ns, notif)
            pygame.draw.rect(screen,(220,60,60), notif, 2, border_radius=10)
            draw_text("DERROTA!", big_font, (255,60,60), notif.centerx, notif.y+28)
            draw_text("Voce nao conseguiu derrotar", small_font,(220,180,180), notif.centerx, notif.y+60)
            draw_text("o Dragao. Treine mais forte!", small_font,(220,180,180), notif.centerx, notif.y+80)
            # auto-dismiss after 3s using a simple approach: just show it until next dragon attempt
            # player can click anywhere to dismiss
            if any(event.type == pygame.MOUSEBUTTONDOWN for event in []):
                dragon_failed_msg = False

    # ====================================================
    # DESENHO — GALERIA
    # ====================================================
    elif mode=="collection":
        draw_overlay(150)
        panel=pygame.Rect(28,18,WIDTH-56,HEIGHT-58)
        draw_panel(panel,(8,8,28))
        draw_text("GALERIA DE MONSTROS",big_font,(255,215,50),CX,48)
        draw_text("Clique num monstro desbloqueado para farmar!", tiny_font,(160,160,200),CX,74)

        cols=3; cw=192; ch=118; gap=12
        sx=(WIDTH-cols*cw-(cols-1)*gap)//2

        for i,e in enumerate(enemy_list):
            ci=i%cols; ri=i//cols
            cx2=sx+ci*(cw+gap); cy2=90+ri*(ch+gap)
            cr=pygame.Rect(cx2,cy2,cw,ch)
            unlocked=kills[e["name"]]>0

            is_hover = cr.collidepoint(mp) and unlocked

            s=pygame.Surface((cw,ch),pygame.SRCALPHA)
            if is_hover:
                s.fill((50,50,100,240))
            elif unlocked:
                s.fill((28,28,58,215))
            else:
                s.fill((22,22,22,215))
            screen.blit(s,cr)

            border_col = (255,215,50) if is_hover else ((190,150,45) if unlocked else (50,50,50))
            pygame.draw.rect(screen, border_col, cr, 2, border_radius=8)

            if unlocked:
                thumb=pygame.transform.scale(e["sprite"],(50,50))
                screen.blit(thumb,(cx2+4,cy2+ch//2-25))

                tx = cx2+62  # text x start
                draw_text(e["name"],    small_font,(255,215,70),  tx,cy2+10, anchor="midleft")
                draw_text(f"Mortes: {kills[e['name']]}", tiny_font,(195,195,195), tx,cy2+26, anchor="midleft")
                draw_text(f"HP: {e['hp']}",              tiny_font,(195,195,195), tx,cy2+40, anchor="midleft")
                draw_text(f"Drop: ~{e['gold_drop']}g",   tiny_font,(255,210,50),  tx,cy2+54, anchor="midleft")

                desc_lines = ENEMY_DESC[e["name"]].split("\n")[:2]
                for li,ln in enumerate(desc_lines):
                    if len(ln) > 20: ln = ln[:18]+"..."
                    draw_text(ln, tiny_font,(155,155,195), tx,cy2+70+li*13, anchor="midleft")

                if is_hover:
                    draw_text(">> IR PARA FASE <<", tiny_font,(255,255,100), cr.centerx, cr.bottom-10, anchor="center")
            else:
                draw_text("???",font,(65,65,65),cx2+cw//2,cy2+ch//2-10)
                draw_text("Nao descoberto",tiny_font,(50,50,50),cx2+cw//2,cy2+ch//2+10)

        draw_button(btn_back,(55,55,55),"Voltar",hover=btn_back.collidepoint(mp))

    # ====================================================
    # DESENHO — WIN
    # ====================================================
    elif mode=="win":
        draw_overlay(170)
        panel=pygame.Rect(80,60,WIDTH-160,HEIGHT-120)
        draw_panel(panel,(20,10,0))
        draw_text("VOCE VENCEU!",        big_font,(255,215,0),   CX,102)
        draw_text("O Dragon foi derrotado!", font,(215,195,255), CX,152)
        draw_text("Clickaria esta salva!",   font,(190,250,190), CX,178)
        pygame.draw.line(screen,(150,120,40),(130,210),(WIDTH-130,210),1)
        draw_text(f"Gold acumulado:   {count}",           font,(255,210,0),  CX,232)
        draw_text(f"Dano final:       {damage}",          font,(200,200,200),CX,258)
        draw_text(f"Total de abates:  {sum(kills.values())}",font,(200,200,200),CX,284)
        pygame.draw.line(screen,(100,80,20),(130,310),(WIDTH-130,310),1)

        draw_text("Continue farmando ou volte ao menu!", small_font,(180,180,220), CX, 326)

        btn_gallery_win = pygame.Rect(CX-200, 350, 175, 44)
        btn_menu_win    = pygame.Rect(CX+25,  350, 175, 44)
        draw_button(btn_gallery_win,(50,50,140),"Ver Galeria",   hover=btn_gallery_win.collidepoint(mp))
        draw_button(btn_menu_win,   (40,140,55),"Menu Principal",hover=btn_menu_win.collidepoint(mp))



    pygame.display.flip()

pygame.quit()
sys.exit()