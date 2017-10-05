#librerie importate
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import telegram
import time
import random
import os

#variabili globali utility
TOKEN = "418736265:AAHwfZPegrNyi8KgYcLfDp1oZkvSNDjZ1aU"
PORT = int(os.environ.get('PORT', '5000'))
updater = Updater(TOKEN)
dispatcher = updater.dispatcher

#stati menu handler
MENU, HELP, SETTINGS = range(3)

#variabili globali per il gioco
group_id=0
group_list=[]
player_list=[]
role_list=[]
#variabili stato gioco
role_index=0
can_join=0
night=True
night_counter=0

#definizioni classi
class Player():
    """Player entity"""
    def __init__(self, name, chat_id, role='default', status='alive',vote=0, can_power=0,special_power=0):
        self.name = name
        self.chat_id = chat_id
        self.role = role
        self.status = status
        self.vote = vote
        self.can_power=can_power
        self.special_power=special_power

    def wake(self):
        if self.can_power==0:
            self.can_power=1

    def sleep(self):
        if self.can_power==1:
            self.can_power=0

    def end_power(self):
        self.can_power=-1

    def use_special(self):
        self.special_power-=1

    def set_status(self,status):
        if status in ['alive','dead','victim']: #add here other valid status
            self.status=status
    def voted(self):
        self.voti+=1
#FUNZIONE SPECIALE ADMIN
def showMatchInfo(bot,update):
    if update.message.chat.type=='private' and update.message.from_user.first_name == 'samubura':
        global player_list
        matchInfo="*CURRENT MATCH INFO*\nPlayerList:\n"
        bot.send_message(chat_id=update.message.chat_id,parse_mode='Markdown',text=matchInfo)
        for player in player_list:
            matchInfo=player.name + " " + player.role +" " +player.status+" power:"+str(player.can_power) + "chatid:"+str(player.chat_id)
            bot.send_message(chat_id=update.message.chat_id,parse_mode='Markdown',text=matchInfo)

#Definizioni poteri principali
def kill(bot,update,args):
    global player_list
    if night:
        if update.message.chat.type=='group':
            bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo come messaggio privato a @lupusinbot')
            return
        name=update.message.from_user.first_name
        if len(args)==0:
            bot.send_message(chat_id=update.message.chat_id,text='Devi scrivere il nome del giocatore che vuoi uccidere /kill <name>')
            return
        victim=args[0]
        for player in player_list:
            if player.name==name and player.role=='lupo' and player.can_power==1:
                for i in player_list:
                    if i.name==victim and i.role!='lupo':
                        i.set_status('victim')
                        bot.send_message(chat_id=update.message.chat_id,text='La vittima è stata scelta, ora torna a dormire')
                        go_sleep(bot)
                        return
                bot.send_message(chat_id=update.message.chat_id,text='Il giocatore non è nella lista')
                return
        bot.send_message(chat_id=update.message.chat_id,text='Non sei autorizzato ad usare questo comando')
    else: bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo potere solo di notte')
def burn(bot,update,args):
    global player_list
    if not night:
        if update.message.chat.type=='private':
            bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo in un gruppo con @lupusinbot')
            return
        if len(args)==0:
            bot.send_message(chat_id=update.message.chat_id,text='Devi scrivere il nome del giocatore che vuoi mandare al rogo /burn <name>')
            return
        name=update.message.from_user.first_name
        burned=args[0]
        for player in player_list:
            if player.name==name and player.can_power:
                for i in player_list:
                    if i.name==burned:
                        i.voted()
                        player.sleep()
                if player.can_power:
                    bot.send_message(chat_id=update.message.chat_id,text='Il giocatore non è nella lista')
        tot_vote=0
        for player in player_list:
            tot_vote+=player.vote
        if tot_vote>=len(player_list):
            end_day(bot)
            return
        bot.send_message(chat_id=update.message.chat_id,text='Non sei autorizzato ad usare questo comando')
    else:
        bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo di giorno')

#Altri poteri
def see(bot,update,args):
    if night:
        if update.message.chat.type=='group':
            bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo come messaggio privato a @lupusinbot')
            return
        name=update.message.from_user.first_name
        if len(args)==0:
            bot.send_message(chat_id=update.message.chat_id,text='Devi scrivere il nome del giocatore che vuoi esaminare /see <name>')
            return
        examined=args[0]
        for player in player_list:
            if player.name==name and player.role=='veggente' and player.can_power==1:
                for i in player_list:
                    if i.name==examied:
                        if i.role=='lupo':
                            mex_text=name +' è un lupo!'
                            bot.send_message(chat_id=update.message.chat_id,text=mex_text)
                        else:
                            mex_text=name +'non è un lupo.'
                            bot.send_message(chat_id=update.message.chat_id,text=mex_text)
                        go_sleep(bot)
                        return
                bot.send_message(chat_id=update.message.chat_id,text='Il giocatore non è nella lista')
                return
        bot.send_message(chat_id=update.message.chat_id,text='Non sei autorizzato ad usare questo comando')
    else: bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo potere solo di notte')

def save(bot,update,args):
    global player_list
    if night:
        if update.message.chat.type=='group':
            bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo comando solo come messaggio privato a @lupusinbot')
            return
        name=update.message.from_user.first_name
        if len(args)==0:
            bot.send_message(chat_id=update.message.chat_id,text='Devi scrivere il nome del giocatore che vuoi proteggere /save <name>')
            return
        saved=args[0]
        for player in player_list:
            if player.name==name and player.role=='protettore' and player.can_power==1:
                for i in player_list:
                    if i.name==saved:
                        if i.name==name:
                            if player.special_power>0:
                                player.use_special()
                                bot.send_message(chat_id=update.message.chat_id,text='Ti sei salvato da solo, non potrai più farlo durante la partita')
                            else:
                                bot.send_message(chat_id=update.message.chat_id,text="Puoi salvarti da solo una sola volta scegli un altro giocatore")
                                return
                        if i.status=='victim':
                            i.set_status('alive')
                        bot.send_message(chat_id=update.message.chat_id,text='Hai scelto la persona da proteggere, torna a dormire')
                        go_sleep(bot)
                        return
                bot.send_message(chat_id=update.message.chat_id,text='Il giocatore non è nella lista')
                return
        bot.send_message(chat_id=update.message.chat_id,text='Non sei autorizzato ad usare questo comando')
    else: bot.send_message(chat_id=update.message.chat_id,text='Puoi usare questo potere solo di notte')

#funzioni principali per il gioco
def start_match(bot):
    global role_list
    global role_index
    role_index=0
    wolf_list=[]
    i=0
    for r in role_list:
        if r=='lupo': break
        i=i+1
    if i!=0:
        role_list[i], role_list[0] = role_list[0], role_list[i] #scambio inline metto i lupi in testa
    #poi informo i lupi dei loro compagni
    for p in player_list:
        if p.role=='lupo':
            wolf_list.append(p)
        elif p.role in ['protettore','assassino']:
            p.special_power=1
    if len(wolf_list)==1:
        bot.send_message(chat_id=wolf_list[0].chat_id,text='Sei un lupo solitario!')
    else:
        for player in wolf_list:
            bot.send_message(chat_id=player.chat_id,text='Membri del branco:')
            for w in wolf_list:
                if w.name!=player.name:
                    bot.send_message(chat_id=player.chat_id, text=w.name)
    awakening(bot)
def awakening(bot): #awaken only the right role
    global night
    night=True
    if role_index==0:
        bot.send_message(chat_id=group_id,text='Scende la notte sul villaggio, tutti vanno a dormire')

    role=role_list[role_index]
    if role=='lupo': bot.send_message(chat_id=group_id,text='Si svegliano i lupi.')
    elif role=='veggente': bot.send_message(chat_id=group_id,text='Si sveglia il veggente')
    elif role=='protettore': bot.send_message(chat_id=group_id,text='Si sveglia il protettore')
    #activate powers
    for player in player_list:
        if player.role==role:
            if player.status=='dead':
                time.sleep(random.randint(1200,3000))
                go_sleep()
            else:
                Flag='Sveglio il' + role
                bot.send_message(chat_id=group,text=Flag)
                player.wake()
                bot.send_message(chat_id=player.chat_id,text='Lista persone vive:')
                for p in player_list:
                    if p.status!='dead' and p.role!=role:
                        bot.send_message(chat_id=player.chat_id,text=p.name)
                if role=='lupo':
                    bot.send_message(chat_id=player.chat_id,text='Puoi usare /kill <name> per scegliere chi uccidere')
                elif role=='veggente':
                    bot.send_message(chat_id=player.chat_id,text='Puoi usare /see <name> per scegliere chi esaminare')
                elif role=='protettore':
                    bot.send_message(chat_id=player.chat_id,text='Puoi usare /save <name> per scegliere chi salvare')
        return
def go_sleep(bot):
    global role_index
    global player_list

    role=role_list[role_index]
    if role=='lupo': bot.send_message(chat_id=group_id,text='I lupi hanno scelto la loro vittima e tornano a dormire')
    elif role=='veggente': bot.send_message(chat_id=group_id,text='Il veggente usa il suo potere e torna a dormire')
    elif role=='protettore': bot.send_message(chat_id=group_id,text='Il protettore sceglie chi proteggere poi torna a dormire')
    for player in player_list:
        player.sleep()
    if role_index==len(role_list)-1:
        day(bot)
    else:
        role_index+=1
        awakening(bot)
def day(bot):
    #fase diurna
    global night
    global role_index
    role_index=0
    bot.send_message(chat_id=group_id,text='Sorge il sole sul villaggio, si svegliano tutti...')
    for player in player_list:
        if player.status=='victim':  #kill the player
            player.set_status('dead')
            player.end_power()
            death_mex='...tutti tranne '+ player.name
            bot.send_message(chat_id=group_id,text=death_mex)
    CheckVictory(bot)
    night=False
    bot.send_message(chat_id=group_id,text='I cittadini si riuniscono in piazza per decidere chi mandare al rogo.\nManda un messaggio con scritto /burn <name> per scegliere chi bruciare')
    bot.send_message(chat_id=group_id,text='Lista persone vive:')
    for p in player_list:
        p.wake()
        if p.status!='dead':
            bot.send_message(chat_id=group_id,text=p.name)
    return
def end_day(bot):
    global player_list
    m=0
    for i in range(0,len(player_list)-1):
        if player_list[i].vote>player_list[m].vote:
            m=i
    most_voted=[]
    for i in range(0,len(player_list)-1):
        if player_list[i].vote==player_list[m].vote:
            most_voted.append(i)
            player_list[i].vote=0   #reset vote
    if len(most_voted)>1:
        bot.send_message(chat_id=group_id,text='Situazione di parità')
    else:
        player=most_voted[0]
        player.set_status('dead')
        player.end_power()
        death_mex=player.name + ' è stato bruciato, tutti tornano a casa sentendosi più sicuri'
        bot.send_message(chat_id=group_id,text=death_mex)
    CheckVictory(bot)

def CheckVictory(bot):
    global night
    c=0
    w=0
    for player in player_list:
        if player.role=='lupo' and player.status=='alive':
            w+=1
        if player.role!='lupo' and player.status=='alive':
            c+=1

    if w==0:
        bot.send_message(chat_id=group_id,text="Tutti i lupi sono morti!\nVittoria dei contadini.")
        end_game(bot)
    elif c==0:
        bot.send_message(chat_id=group_id,text="Tutti gli abitanti del villaggio sono morti!\nVittoria dei lupi.")
        end_game(bot)

def end_game(bot):
    global player_list
    global role_list
    global group_list
    global group_id
    global role_index
    global can_join
    global night
    global night_counter

    del player_list[:]
    del role_list[:]
    del group_list[:]
    group_id=0
    role_index=0
    can_join=0
    night=True
    night_counter=0
    bot.send_message(chat_id=group_id,text="Partita finita, per iniziare una nuova partita scrivi /newgame")

#Definizioni funzioni per relazionarsi con l'utente
def start(bot,update):
    if update.message.chat.type=='group':
        bot.send_message(chat_id=update.message.chat_id, text='Benvenuto in @lupusinbot puoi iniziare una partita scrivendo /newgame')
    elif update.effective_chat.type=='private' :
        bot.send_message(chat_id=update.message.chat_id, text='Benvenuto in @lupusinbot puoi aggiungerti ad una partita scrivendo /join')
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Non disponi delle autorizzazioni necessarie per usare questo bot')
def newgame(bot, update):
    if update.message.chat.type=='group':
        kb = [[telegram.InlineKeyboardButton('Nuova partita',callback_data='y')]]
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        bot.send_message(chat_id=update.message.chat_id, text='Iniziare una nuova partita? Tutti i progressi attuali saranno persi', reply_markup=kb_markup)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Non puoi usare questo comando in una chat privata')
def menu(bot,update): #resetta le variabili globali
    global group_id
    global group_list
    global player_list
    global can_join
    global night_counter
    global role_list

    del player_list[:]
    del role_list[:]
    del group_list[:]
    group_id=update.callback_query.message.chat_id
    group_list=bot.get_chat_administrators(group_id)
    bot.edit_message_text(chat_id=group_id, message_id=update.callback_query.message.message_id,
                         text='Ho creato un nuovo villaggio. Invia un messaggio privato a @lupusinbot con scritto /join per entrare.\nQuando tutti sono entrati scrivi /settings per impostare i ruoli')
    can_join=1
def helper(bot,update):
    kb = [
    [telegram.InlineKeyboardButton('Elenco ruoli',callback_data='ruoli'),telegram.InlineKeyboardButton('Elenco comandi',callback_data='comandi')],
    [telegram.InlineKeyboardButton('Come si gioca?',callback_data='faq')]
    ]
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.send_message(chat_id=update.message.chat.id,text='Come posso aiutarti?', reply_markup=kb_markup)
def helpmenu(bot,update):
    data=update.callback_query.data
    if data=='ruoli':
        bot.send_message(chat_id=update.callback_query.message.chat.id,parse_mode='Markdown', text="*RUOLI*\n_Lupo_: Se sei un lupo devi uccidere tutti gli altri membri del villaggio, esclusi i tuoi compagni lupi.\nAccordatevi di notte per scegliere chi uccidere\n"
                                                                                        "_Veggente_: Il veggente può scoprire se un membro del villaggio è un lupo o no, ma deve essere cauto a rivelarsi o i lupi lo uccideranno!\n"
                                                                                        "_Protettore_: Il protettore può scegliere ogni notte qualcuno da salvare, può salvarsi anche da solo ma solo una volta durante la partita!\n"
                                                                                        "_Contadino_: I Contadini non hanno poteri speciali, devono cercare di bruciare i lupi sul rogo per salvarsi"
                                                                                        "\n _[altri ruoli in arrivo...]_")
    elif data=='comandi':
        bot.send_message(chat_id=update.callback_query.message.chat.id,parse_mode='Markdown', text="*COMANDI*\n/start - Avvia il bot\n"
        "/help - Visualizza il menu\n"
        "/newgame - Crea una nuova partita\n"
        "/join - Entra in una nuova partita\n"
        "/settings - Imposta i ruoli\n"
        "/kill - <player> Scegli chi uccidere di notte\n"
        "/burn - <player> Scegli chi mandare al rogo\n"
        "/see - <player> Scopri il ruolo del giocatore scelto\n"
        "/save - <player> Proteggi un giocatore per una notte\n")
    elif data=='faq':
        bot.send_message(chat_id=update.callback_query.message.chat.id,parse_mode='Markdown', text="*COME SI GIOCA*\n"
                                                                            "Scrivi /start per avviare il bot dopo un periodo di inattività, attendi la risposta anche se potrebbe volerci un po'\n"
                                                                            "Una volta avviato scegliete *una persona* che si occuperà di creare la partita e impostarla (per non fare confusione)\n"
                                                                            "Scrivi /newgame per avviare una partita e poi scrivete /join in chat **privata** per unirvi alla partita appena iniziata\n"
                                                                            "Scrivi /settings quando tutti sono entrati e poi premi i pulsanti per aggiungere personaggi (dai tempo al bot di rispondere)\n"
                                                                            "Quando è tutto pronto premi INIZIA PARTITA per avviare il gioco e segui le indicazioni del bot per le varie fasi\n"
                                                                            "Buon divertimento!\n")
def createPlayer(bot,update):
    #creating a new player
    global player_list
    global can_join

    flag=0;
    if can_join:
        if update.message.chat_id==group_id:
            bot.send_message(chat_id=group_id, text='Puoi usare /join solo come messaggio privato a @lupusinbot')
        else:
            newplayer=Player(update.message.from_user.first_name,update.message.chat_id)
             #cerco il giocatore
            for player in player_list:
                if player.name==newplayer.name and player.chat_id==newplayer.chat_id: flag=1

            if (flag):
                bot.send_message(chat_id=update.message.chat_id, text='Sei già dentro il villaggio')
            else:
                player_list.append(newplayer)
                bot.send_message(chat_id=update.message.chat_id, text='Sei entrato nel villaggio')
                jointext=update.message.from_user.first_name + ' è entrato nel villaggio'
                bot.send_message(chat_id=group_id, text= jointext)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Al momento non è possibile aggiungersi alla partita')
def set_roles(bot,update):
    global can_join
    can_join=0
    kb = [
    [telegram.InlineKeyboardButton('Lupo',callback_data='lupo'),telegram.InlineKeyboardButton('Veggente',callback_data='veggente')],
    [telegram.InlineKeyboardButton('Protettore',callback_data='protettore'),telegram.InlineKeyboardButton('Contadino',callback_data='contadino')],
    [telegram.InlineKeyboardButton('INIZIA PARTITA',callback_data='play')]
    ]
    kb_markup = telegram.InlineKeyboardMarkup(kb)
    bot.send_message(chat_id=group_id, text='Seleziona i ruoli da inserire, premi INIZIA PARTITA quando hai finito', reply_markup=kb_markup)
def ruoli(bot,update):
    global player_list
    global role_list
    role=update.callback_query.data
    i=random.randint(0,len(player_list)-1)
    c=0
    while player_list[i].role != 'default' and c<=len(player_list):
        i=random.randint(0,len(player_list)-1)
        c+=1
    if c<=len(player_list):
        if ((role not in role_list) and (role!='contadino')):
            role_list.append(role)
        player_list[i].role=role
        message='Inserito un ' + role
        bot.send_message(chat_id=group_id, text=message)
        message='Sei un '+role
        bot.send_message(chat_id=player_list[i].chat_id, text=message)
    else:
        kb = [
        [telegram.InlineKeyboardButton('INIZIA PARTITA',callback_data='play')]
        ]
        kb_markup = telegram.InlineKeyboardMarkup(kb)
        bot.send_message(chat_id=group_id, text='Tutti i giocatori hanno un ruolo', reply_markup=kb_markup)

#gestione tutti menu a bototoni
def button_mixer(bot,update):
    data=update.callback_query.data
    if data == 'y':
        menu(bot,update)
    elif data in ['lupo','veggente','protettore','contadino']:
        ruoli(bot,update)
    elif data in ['ruoli','comandi','faq']:
        helpmenu(bot,update)
    elif data=='play': start_match(bot)

#definizioni menu
start=CommandHandler('start',start)
dispatcher.add_handler(start)
join=CommandHandler('join',createPlayer)
dispatcher.add_handler(join)
newgame=CommandHandler('newgame',newgame)
dispatcher.add_handler(newgame)
settings=CommandHandler('settings',set_roles)
dispatcher.add_handler(settings)
helper=CommandHandler('help',helper)
dispatcher.add_handler(helper)


#powers
kill=CommandHandler('kill',kill,pass_args=True)
dispatcher.add_handler(kill)
see=CommandHandler('see',see,pass_args=True)
dispatcher.add_handler(see)
save=CommandHandler('save',save,pass_args=True)
dispatcher.add_handler(save)
burn=CommandHandler('burn',burn,pass_args=True)
dispatcher.add_handler(burn)

show=CommandHandler('show',showMatchInfo)
dispatcher.add_handler(show)

#callbackQuery
buttons=CallbackQueryHandler(button_mixer)
dispatcher.add_handler(buttons)

#corpo del programma
updater.bot.setWebhook("https://lupusinbot.herokuapp.com/" + TOKEN)
updater.start_webhook(listen="0.0.0.0",
                    port=PORT,
                    url_path=TOKEN)
updater.idle()
